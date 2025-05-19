import os
import sqlite3
import re
import json
import glob
import sys

try:
    import spacy
except ImportError:
    print("SpaCy non è installato. Installa spaCy con 'pip install spacy' e il modello italiano con 'python -m spacy download it_core_news_sm'.")
    sys.exit(1)

if __name__ == "__main__":
    DB_PATH = "knowledge.db"
    TRAIN_DIR = "training_material"
else:
    DB_PATH = "MachineLearningAlgorithm/knowledge.db"
    TRAIN_DIR = "MachineLearningAlgorithm/training_material"

###############################################################################
# Inizializzazione del database                                              #
###############################################################################

def initialize_db(conn: sqlite3.Connection) -> None:
    """Crea le tabelle se non esistono già."""
    cur = conn.cursor()

    # Nota: tutti i nomi che potrebbero entrare in conflitto con parole riservate
    #       (ad es. CASE) sono racchiusi tra doppi apici, l'escape standard di SQLite.

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS "Pattern" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            syntax TEXT UNIQUE NOT NULL
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS "Word" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS "Case" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Word_Scorage (
            case_id   INTEGER NOT NULL,
            word_id   INTEGER NOT NULL,
            score     INTEGER NOT NULL,
            PRIMARY KEY (case_id, word_id),
            FOREIGN KEY (case_id) REFERENCES "Case"(id),
            FOREIGN KEY (word_id) REFERENCES "Word"(id)
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Pattern_Scorage (
            case_id    INTEGER NOT NULL,
            pattern_id INTEGER NOT NULL,
            score      INTEGER NOT NULL,
            PRIMARY KEY (case_id, pattern_id),
            FOREIGN KEY (case_id) REFERENCES "Case"(id),
            FOREIGN KEY (pattern_id) REFERENCES "Pattern"(id)
        );
        """
    )

    conn.commit()

###############################################################################
# Funzioni helper                                                             #
###############################################################################

def get_or_create_word(conn: sqlite3.Connection, word: str) -> int:
    """Ritorna l'id della parola, creandola se necessario."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM \"Word\" WHERE word = ?", (word,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO \"Word\" (word) VALUES (?)", (word,))
    conn.commit()
    return cur.lastrowid


def get_or_create_pattern(conn: sqlite3.Connection, pattern_list: list[str]) -> int:
    """Ritorna l'id del pattern (lista di stringhe JSON), creandolo se necessario."""
    syntax_json = json.dumps(pattern_list, ensure_ascii=False)
    cur = conn.cursor()
    cur.execute("SELECT id FROM \"Pattern\" WHERE syntax = ?", (syntax_json,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO \"Pattern\" (syntax) VALUES (?)", (syntax_json,))
    conn.commit()
    return cur.lastrowid


def get_or_create_case(conn: sqlite3.Connection, name: str) -> int:
    """Ritorna l'id del case, creandolo se necessario."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM \"Case\" WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO \"Case\" (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid


def increment_word_score(conn: sqlite3.Connection, case_id: int, word_id: int) -> None:
    """Incrementa di 1 lo score della parola per il case dato."""
    cur = conn.cursor()
    cur.execute(
        "SELECT score FROM Word_Scorage WHERE case_id = ? AND word_id = ?",
        (case_id, word_id),
    )
    if cur.fetchone():
        cur.execute(
            "UPDATE Word_Scorage SET score = score + 1 WHERE case_id = ? AND word_id = ?",
            (case_id, word_id),
        )
    else:
        cur.execute(
            "INSERT INTO Word_Scorage (case_id, word_id, score) VALUES (?, ?, 1)",
            (case_id, word_id),
        )
    conn.commit()


def increment_pattern_score(conn: sqlite3.Connection, case_id: int, pattern_id: int) -> None:
    """Incrementa di 1 lo score del pattern per il case dato."""
    cur = conn.cursor()
    cur.execute(
        "SELECT score FROM Pattern_Scorage WHERE case_id = ? AND pattern_id = ?",
        (case_id, pattern_id),
    )
    if cur.fetchone():
        cur.execute(
            "UPDATE Pattern_Scorage SET score = score + 1 WHERE case_id = ? AND pattern_id = ?",
            (case_id, pattern_id),
        )
    else:
        cur.execute(
            "INSERT INTO Pattern_Scorage (case_id, pattern_id, score) VALUES (?, ?, 1)",
            (case_id, pattern_id),
        )
    conn.commit()

###############################################################################
# Funzioni di processing                                                      #
###############################################################################

SANITIZE_REGEX = re.compile(r"[^A-Za-zÀ-ÖØ-öø-ÿ0-9]+", re.UNICODE)


def sanitize(text: str) -> str:
    """Rimuove caratteri non alfanumerici (ma mantiene gli accenti)."""
    return SANITIZE_REGEX.sub(" ", text).strip()


def process_file(conn: sqlite3.Connection, nlp, filepath: str) -> None:
    """Analizza un singolo file di training e poi lo elimina."""
    case_name = os.path.splitext(os.path.basename(filepath))[0]
    case_id = get_or_create_case(conn, case_name)

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            sanitized_line = sanitize(line)
            if not sanitized_line:
                continue  # riga vuota

            # --- Parole ------------------------------------------------------
            for raw_word in sanitized_line.split():
                word = raw_word.lower().strip()
                if not word:
                    continue
                word_id = get_or_create_word(conn, word)
                increment_word_score(conn, case_id, word_id)

            # --- Pattern POS --------------------------------------------------
            doc = nlp(sanitized_line)
            pattern_list = [token.pos_ for token in doc if token.text.strip()]
            if not pattern_list:
                continue
            pattern_id = get_or_create_pattern(conn, pattern_list)
            increment_pattern_score(conn, case_id, pattern_id)

    # Elimina il file dopo l'elaborazione
    os.remove(filepath)

###############################################################################
# Main                                                                        #
###############################################################################

def main():
    # Connessione (e creazione) del DB
    with sqlite3.connect(DB_PATH) as conn:
        initialize_db(conn)

        # Carica il modello SpaCy italiano
        try:
            nlp = spacy.load("it_core_news_sm")
        except OSError:
            print(
                "Modello 'it_core_news_sm' non trovato. Installa con: python -m spacy download it_core_news_sm"
            )
            sys.exit(1)

        # Assicura che la directory di training esista
        if not os.path.isdir(TRAIN_DIR):
            os.makedirs(TRAIN_DIR, exist_ok=True)
            print(
                f"Directory '{TRAIN_DIR}' creata. Aggiungi file .txt da elaborare e riesegui lo script."
            )
            return

        # Analizza ogni file .txt presente
        txt_files = glob.glob(os.path.join(TRAIN_DIR, "*.txt"))
        if not txt_files:
            print("Nessun file .txt trovato in 'training_material'. Niente da fare.")
            return

        for txt_path in txt_files:
            print(f"Processo '{txt_path}' ...")
            process_file(conn, nlp, txt_path)
        print("Elaborazione completata.")


if __name__ == "__main__":
    main()