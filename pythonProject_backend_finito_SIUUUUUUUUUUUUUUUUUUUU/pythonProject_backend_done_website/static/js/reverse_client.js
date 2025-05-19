// reverse_client.js
function b642buf(b64) {
  return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
}

// Ricezione dati cifrati
export async function decryptData(data, aesKey) {
  const ivBuf = b642buf(data.iv);
  const ctBuf = b642buf(data.ciphertext);
  const ptBuf = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: ivBuf },
    aesKey,
    ctBuf
  );
  return JSON.parse(new TextDecoder().decode(ptBuf));
}
