document.addEventListener('DOMContentLoaded', () => {
    const chatArea   = document.getElementById('chatArea');
    const tpl        = document.getElementById('userBlockTpl');
    let   firstBlock = true;          // solo il primo va spostato in alto

    // ---------------------------------------------------------------------
    const scrollBottom = () => chatArea.scrollTo(0, chatArea.scrollHeight);

    function nuovoBloccoUtente () {
        const node   = tpl.content.firstElementChild.cloneNode(true);
        const prompt = node.querySelector('.prompt');
        const toggle = node.querySelector('.toggle');
        const send   = node.querySelector('.send');

        // stato toggle
        let toggleOn = false;
        toggle.addEventListener('click', () => {
            toggleOn = !toggleOn;
            toggle.style.backgroundColor = toggleOn ? '#8fc9ff' : '';
        });

        // invio (ENTER o click)
        function invia () {
            const query = prompt.value.trim();
            if (!query) return;

            node.classList.add('sent');
            prompt.readOnly = true;
            node.querySelector('.controls').remove();
            /* ——— tolta la riga con 'position:absolute' ——— */
            //chatArea.prepend(node);
            firstBlock = false;

            const answerBox = document.createElement('div');
            answerBox.className = 'answer waiting';
            chatArea.insertBefore(answerBox, node.nextSibling);

            fetch('/query', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({query,toggle:toggleOn})
            }).catch(console.error);

            window.__currentAnswerBox = answerBox;
            scrollBottom();
        }

        prompt.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();invia();}});
        send  .addEventListener('click',invia);

        return node;
    }
    window.addUserBlock = () => {
        chatArea.appendChild(nuovoBloccoUtente());
        scrollBottom();
    };

    window.addUserBlock();
});
