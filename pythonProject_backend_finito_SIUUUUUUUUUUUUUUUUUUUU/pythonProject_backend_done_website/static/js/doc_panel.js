import { sendEncryptedJSON } from './auth.js';

document.addEventListener('DOMContentLoaded', async () => {
  const user = localStorage.getItem('auth_user');
  const pass = localStorage.getItem('auth_pass');
  const docPanel = document.getElementById('doc-panel');
  const scrollPanel = docPanel.querySelector('.scroll-panel');

  // Prompt di login
  const promptEl = document.createElement('p');
  promptEl.id = 'login-prompt';
  promptEl.textContent = 'Effettua il login per vedere i documenti.';
  scrollPanel.appendChild(promptEl);

  if (user && pass) {
    // Rimuovo prompt
    promptEl.remove();

    // Invio richiesta 'retrieval'
    try {
      const payload = { action: 'retrieval', username: user };
      const resp = await sendEncryptedJSON(payload);

      if (resp.status === 'ok' && Array.isArray(resp.files)) {
        resp.files.forEach(filename => {
          const btn = document.createElement('button');
          btn.textContent = filename;
          btn.classList.add('sidebar-btn');
          // qui si può aggiungere l'evento di download o apertura
          scrollPanel.appendChild(btn);
        });
      } else {
        console.error('Retrieval failed:', resp.message);
      }
    } catch (err) {
      console.error('Errore recupero documenti:', err);
    }
  }
});