import tornado.ioloop
import tornado.web
import tornado.websocket
import os
import json
import secrets
import base64
import re
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from MachineLearningAlgorithm.knowledge_query import interactive_search
from RegexAlgorithm.ricerca_prompt_fix import analizza_query
from live_log import register, unregister, emit
from sqlalchemy.exc import IntegrityError
from account_database import session, User

SERVER_PRIV = ec.generate_private_key(ec.SECP256R1())
SERVER_PUB_BYTES = SERVER_PRIV.public_key().public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)
SERVER_PUB_B64 = base64.b64encode(SERVER_PUB_BYTES).decode()

# ----------------------------------
#   FUNZIONE PER Tx DATI DAL SERVER
# ----------------------------------

def encrypt_for_client(client_pub_b64: str, payload: dict) -> dict:
    """
    Data la public key del client in Base64 e un payload dict,
    ritorna {"iv": base64, "ciphertext": base64}.
    """
    # 1) Decodifica public key client
    cpub = base64.b64decode(client_pub_b64)
    client_pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), cpub)

    # 2) Deriva shared secret e chiave AES
    shared = SERVER_PRIV.exchange(ec.ECDH(), client_pub)
    key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"handshake data").derive(shared)

    # 3) Cifra con AES-GCM
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    pt = json.dumps(payload).encode()
    ct = aesgcm.encrypt(iv, pt, None)

    # 4) Restituisci Base64 di iv e ciphertext
    return {
        "iv": base64.b64encode(iv).decode(),
        "ciphertext": base64.b64encode(ct).decode()
    }

# ----------------------------------
#   HANDLER PER Rx DATI DA CLIENT
# ----------------------------------

class HandshakeHandler(tornado.web.RequestHandler):
    def get(self):
        self.write({"server_public": SERVER_PUB_B64})

class MessageHandler(tornado.web.RequestHandler):
    def post(self):
        print("Request dal client: ", self.request.body)

        data = json.loads(self.request.body)
        cpub = base64.b64decode(data["client_public"])
        iv   = base64.b64decode(data["iv"])
        ct   = base64.b64decode(data["ciphertext"])

        # Import chiave pubblica client e derivazione shared secret
        client_pub = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(), cpub
        )
        shared = SERVER_PRIV.exchange(ec.ECDH(), client_pub)

        # Stesso HKDF usato in JS (salt vuoto, info “handshake data”)
        key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"handshake data"
        ).derive(shared)

        # Decrittazione AES-GCM
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(iv, ct, None)

        print("plaintext ricavato: ", plaintext.decode())

        # Parsing JSON
        try:
            obj = json.loads(plaintext.decode())
        except json.JSONDecodeError:
            self.set_status(400)
            return self.write({"status": "error", "message": "JSON non valido"})

        print("Ricevuto JSON:", obj)

        action = obj.get("action")
        resp_payload = {"status": "failed"}

        if action == "retrieval":
            username = obj.get("username")
            files_list = []
            if username:
                user_dir = os.path.join('uploaded', username)
                if os.path.isdir(user_dir):
                    files_list = os.listdir(user_dir)
            resp_payload = {"status": "ok", "files": files_list}

        if action == "upload":
            username = obj.get("username")
            files = obj.get("files", [])
            if not username or not files:
                resp_payload = {"status": "failed", "message": "Dati mancanti"}
            else:
                upload_dir = os.path.join('uploaded', username)
                os.makedirs(upload_dir, exist_ok=True)
                errore = False
                for file_info in files:
                    filename = file_info.get("filename", "")
                    b64data = file_info.get("data", "")
                    if not filename or not b64data or not re.search(r'\.(pdf|txt)$', filename, re.IGNORECASE):
                        errore = True
                        break
                    path = os.path.join(upload_dir, filename)
                    try:
                        body = base64.b64decode(b64data)
                        with open(path, 'wb') as f:
                            f.write(body)
                    except Exception:
                        errore = True
                        break
                resp_payload = {"status": "ok"} if not errore else {"status": "failed", "message": "Errore su uno o più file"}

        if action == "register":
            username = obj.get("username")
            password = obj.get("password")
            if username and password:
                user = User(username=username, password=password, is_admin=False)
                session.add(user)
                try:
                    session.commit()
                    resp_payload = {"status": "ok", "username": username, "password": password}
                except IntegrityError:
                    session.rollback()

        elif action == "access":
            username = obj.get("username")
            password = obj.get("password")
            if username and password:
                user = session.query(User).filter_by(username=username).first()
                if user and user.password == password:
                    resp_payload = {"status": "ok", "username": username, "password": password}

        # per qualsiasi altro action o mancanza dati, resp_payload rimane {"status": "failed"}

        resp = encrypt_for_client(data["client_public"], resp_payload)
        self.write(resp)

# ----------------------------------
#   HANDLER PER LE PAGINE WEB
# ----------------------------------

class DatabaseHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("database.html")

class MainHandler(tornado.web.RequestHandler):
    """Pagina principale con la chat"""

    def get(self):
        self.render("index.html")

class LoginHandler(tornado.web.RequestHandler):
    """Pagina di login"""

    def get(self):
        self.render("login.html")

class QueryHandler(tornado.web.RequestHandler):
    """Gestisce richieste POST dal front-end"""

    def post(self):
        data   = json.loads(self.request.body)
        query  = data.get("query", "")
        toggle = data.get("toggle", False)
        print(f"Richiesta ricevuta: '{query}', toggle attivo: {toggle}")

        emit("", "start")     # inizio

        if toggle:
            interactive_search(query)
        else:
            analizza_query(query)

        emit("", "end")       # fine

class LogSocket(tornado.websocket.WebSocketHandler):
    """Websocket per mandare al client gli aggiornamenti live"""

    def open(self):
        register(self)

    def on_close(self):
        unregister(self)

    # se non ti serve ricevere messaggi dal client:
    def on_message(self, msg):
        pass

class UploadHandler(tornado.web.RequestHandler):
    def post(self):
        # prendo username dal form
        user = self.get_body_argument('username', None)
        if not user:
            self.set_status(400)
            return self.write({'status': 'failed', 'message': 'Utente non autenticato'})

        files = self.request.files.get('file')
        if not files:
            self.set_status(400)
            return self.write({'status': 'failed', 'message': 'Nessun file inviato'})

        fileinfo = files[0]
        filename = fileinfo['filename']
        # controllo estensione
        if not re.search(r'\.(pdf|txt)$', filename, re.IGNORECASE):
            self.set_status(400)
            return self.write({'status': 'failed', 'message': 'Formato non supportato'})

        # creo cartella utente
        upload_dir = os.path.join('uploaded', user)
        os.makedirs(upload_dir, exist_ok=True)
        path = os.path.join(upload_dir, filename)

        # salvo il file
        with open(path, 'wb') as f:
            f.write(fileinfo['body'])

        self.write({'status': 'ok'})

# ----------------------------------
#   CREAZIONE DELL'APPLICAZIONE
# ----------------------------------

def make_app():
    settings = dict(
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        debug=True,
        autoreload=True,
        cookie_secret = os.environ.get("COOKIE_SECRET") or secrets.token_hex(32),
    )

    routes: list[tuple[str, type[tornado.web.RequestHandler]]] = [
        (r"/", MainHandler),
        (r"/login", LoginHandler),
        (r"/query", QueryHandler),
        (r"/ws/log", LogSocket),
        (r"/handshake", HandshakeHandler),
        (r"/message",   MessageHandler),
        (r"/database", DatabaseHandler),
        (r"/upload", UploadHandler),
    ]

    return tornado.web.Application(routes, **settings)

# ----------------------------------
#   AVVIO DEL SERVER
# ----------------------------------

if __name__ == "__main__":
    try:
        app = make_app()
        app.listen(8888)
        print("Server avviato su http://localhost:8888")
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        print("Programma interrotto!")
