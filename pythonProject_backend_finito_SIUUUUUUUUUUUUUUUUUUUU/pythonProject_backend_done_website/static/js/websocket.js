/*
   Il server ora invia JSON:        { "flag":"...", "payload":"..." }
   flag = start | text | html | end | ... (nuovi tipi hard-coded a piacere)
*/
const ws = new WebSocket(`ws://${location.host}/ws/log`);

ws.onmessage = ({ data }) => {
    let msg;
    try   { msg = JSON.parse(data); }
    catch { msg = { flag:'text', payload:data }; }

    const box = window.__currentAnswerBox;
    if (!box) return;                     // sicurezza

    switch (msg.flag) {
        case 'start':
            // eventuale log, al momento nessuna azione
            break;

        case 'html': {                    // snippet HTML già “hard-coded”
            box.insertAdjacentHTML('beforeend', msg.payload);
            break;
        }

        case 'end':                       // risposta terminata: blocco immutabile
            box.classList.remove('waiting');
            delete window.__currentAnswerBox;
            if (window.addUserBlock) window.addUserBlock();
            break;

        case 'text':
        case 'thinking':
        case 'analysis':
        case 'warning': {                    // aggiungi qui i flag che vuoi trattare come testo
            const p = document.createElement('p');
            p.textContent = msg.payload;
            p.classList.add(`flag-${msg.flag}`);   //  ← stile diversi a seconda del flag
            box.appendChild(p);
            break;
        }
    }
    box.scrollTop = box.scrollHeight;
    document.getElementById('chatArea').scrollTop =
        document.getElementById('chatArea').scrollHeight;
};

ws.onclose = () => console.warn('WebSocket chiuso');
