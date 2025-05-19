// sidebar.js

document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('sidebar-toggle');
  const icon = document.getElementById('sidebar-icon');

  toggleBtn.addEventListener('click', () => {
    const isOpen = sidebar.classList.toggle('expanded');

    // riallinea il toggle button in base allo stato
    if (isOpen) {
      toggleBtn.style.left = '260px';   // 250px larghezza sidebar + 10px di margine
    } else {
      toggleBtn.style.left = '10px';
    }

    if (isOpen) {
      icon.src = '/static/icons/close_sidebar.svg';
      icon.alt = 'Chiudi sidebar';
    } else {
      icon.src = '/static/icons/open_sidebar.svg';
      icon.alt = 'Apri sidebar';
    }
  });
});

document.getElementById('btn-database').addEventListener('click', () => {
  window.location.href = '/database';
});
