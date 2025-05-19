document.addEventListener('DOMContentLoaded', () => {
  const user = localStorage.getItem('auth_user');
  const pass = localStorage.getItem('auth_pass');
  const loginBtn = document.querySelector('.login-btn');

  if (user && pass && loginBtn) {
    // Modifico il pulsante in “Logout (username)”
    loginBtn.textContent = `Logout (${user})`;
    loginBtn.href = '#';
    loginBtn.addEventListener('click', (e) => {
      e.preventDefault();
      localStorage.removeItem('auth_user');
      localStorage.removeItem('auth_pass');
      window.location.reload();
    });
  }
});
