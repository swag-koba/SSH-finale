// upload.js
import { sendEncryptedJSON } from "./auth.js";

document.addEventListener('DOMContentLoaded', () => {
  const uploadBtn = document.getElementById('btn-upload');
  const input     = document.getElementById('file-input');
  if (!uploadBtn || !input) return;

  // abilita selezione multipla
  input.multiple = true;

  uploadBtn.addEventListener('click', () => input.click());

  input.addEventListener('change', async () => {
    const files = Array.from(input.files);
    if (files.length === 0) return alert('Nessun file selezionato.');

    const username = localStorage.getItem('auth_user');
    if (!username) return alert('Devi essere loggato per caricare documenti.');

    // Legge tutti i file come base64
    const readPromises = files.map(file => new Promise(resolve => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64data = reader.result.split(',')[1];
        resolve({ filename: file.name, data: base64data });
      };
      reader.readAsDataURL(file);
    }));

    try {
      const filePayloads = await Promise.all(readPromises);
      const message = {
        action: 'upload',
        username: username,
        files: filePayloads
      };
      const resp = await sendEncryptedJSON(message);
      if (resp.status === 'ok') {
        alert('Upload riuscito!');
      } else {
        alert('Upload fallito: ' + (resp.message || ''));
      }
    } catch (e) {
      console.error(e);
      alert('Errore di rete durante l\'upload.');
    } finally {
      input.value = '';
    }
  });
});
