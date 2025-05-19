import { decryptData } from "./reverse_client.js";

// Helpers per base64 ↔ ArrayBuffer
function buf2b64(buf) {
  return btoa(String.fromCharCode(...new Uint8Array(buf)));
}
function b642buf(b64) {
  return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
}

async function handshake() {
  // 1) Prendo la public key server
  const res = await fetch("/handshake");
  const { server_public } = await res.json();
  const serverPubBuf = b642buf(server_public);

  // 2) Genero coppia ECDH client
  const clientKeys = await crypto.subtle.generateKey(
    { name: "ECDH", namedCurve: "P-256" },
    true,
    ["deriveKey", "deriveBits"]
  );

  // 3) Export public key client
  const clientPubRaw = await crypto.subtle.exportKey("raw", clientKeys.publicKey);

  // 4) Import public key server
  const serverPubKey = await crypto.subtle.importKey(
    "raw", serverPubBuf,
    { name: "ECDH", namedCurve: "P-256" },
    false, []
  );

  // 5) Derivo raw bits (256 bit)
  const sharedBits = await crypto.subtle.deriveBits(
    { name: "ECDH", public: serverPubKey },
    clientKeys.privateKey,
    256
  );

  // 6) Import bits in una chiave HKDF
  const hkdfKey = await crypto.subtle.importKey(
    "raw", sharedBits,
    "HKDF", false, ["deriveKey"]
  );

  // 7) Derivo la chiave AES-GCM con gli stessi parametri del server
  const aesKey = await crypto.subtle.deriveKey(
    {
      name: "HKDF",
      hash: "SHA-256",
      salt: new Uint8Array(),                                  // salt = None
      info: new TextEncoder().encode("handshake data")         // info = b"handshake data"
    },
    hkdfKey,
    { name: "AES-GCM", length: 256 },
    true,
    ["encrypt","decrypt"]
  );

  return { aesKey, clientPubRaw };
}

export async function sendEncryptedJSON(obj) {
  const message = JSON.stringify(obj);
  const { aesKey, clientPubRaw } = await handshake();

  // 8) Cifro con AES-GCM
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encoded = new TextEncoder().encode(message);
  const ctBuf = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    aesKey,
    encoded
  );

  // 9) Invio tutto in base64
  const payload = {
    client_public: buf2b64(clientPubRaw),
    iv:            buf2b64(iv),
    ciphertext:    buf2b64(ctBuf)
  };
  console.log("Payload cifrato inviato:", payload);

  const resp = await fetch("/message", {
    method: "POST",
    headers: { "Content-Type":"application/json" },
    body: JSON.stringify(payload)
  });
  const data = await resp.json();
  console.log("received data back:", data);

  const plain = await decryptData(data, aesKey);
  console.log("plain text: ", plain);
  return plain;
}
