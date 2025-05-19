const $ = id => document.getElementById(id);
import { sendEncryptedJSON } from "./auth.js";

// Elementi da abilitare/disabilitare
const elems = [
  $("username"),
  $("password"),
  $("btn-login"),
  $("btn-register")
];

// Contenitore per messaggi
const feedback = $("feedback");

// Funzione per bloccare/sbloccare form e pulsanti
function setEnabled(enabled) {
  elems.forEach(el => el.disabled = !enabled);
}

// LOGIN
$("btn-login").onclick = async () => {
  setEnabled(false);
  feedback.textContent = '';

  const username = $("username").value;
  const password = $("password").value;
  const flag = "access";
  const message = { username, password, action: flag };

  try {
    const plain = await sendEncryptedJSON(message);
    const obj = typeof plain === 'string' ? JSON.parse(plain) : plain;

    if (obj.status === "ok") {
      // salva in cache
      localStorage.setItem('auth_user', obj.username);
      localStorage.setItem('auth_pass', obj.password);
      // mostra link per tornare alla home
      feedback.innerHTML = `
        <p class="text-green-600">Accesso riuscito!</p>
        <button id="btn-home">Torna alla home</button>
      `;
      $("btn-home").onclick = () => window.location.href = '/';
    } else {
      setEnabled(true);
      feedback.textContent = 'Operazione fallita. Riprova.';
    }
  } catch (e) {
    console.error(e);
    setEnabled(true);
    feedback.textContent = 'Errore di rete. Riprova.';
  }
};

// REGISTER
$("btn-register").onclick = async () => {
  setEnabled(false);
  feedback.textContent = '';

  const username = $("username").value;
  const password = $("password").value;
  const flag = "register";
  const message = { username, password, action: flag };

  try {
    const plain = await sendEncryptedJSON(message);
    const obj = typeof plain === 'string' ? JSON.parse(plain) : plain;

    if (obj.status === "ok") {
      localStorage.setItem('auth_user', obj.username);
      localStorage.setItem('auth_pass', obj.password);
      feedback.innerHTML = `
        <p class="text-green-600">Registrazione riuscita!</p>
        <button id="btn-home">Torna alla home</button>
      `;
      $("btn-home").onclick = () => window.location.href = 'index.html';
    } else {
      setEnabled(true);
      feedback.textContent = 'Operazione fallita. Riprova.';
    }
  } catch (e) {
    console.error(e);
    setEnabled(true);
    feedback.textContent = 'Errore di rete. Riprova.';
  }
};

