document.getElementById('switch-to-register').addEventListener('click', function() {
    document.querySelector('.login-container').style.display = 'none';
    document.querySelector('.register-container').style.display = 'flex';
});

document.getElementById('switch-to-login').addEventListener('click', function() {
    document.querySelector('.register-container').style.display = 'none';
    document.querySelector('.login-container').style.display = 'flex';
});

// Exibe o formulário de login por padrão
document.querySelector('.login-container').style.display = 'flex';
document.querySelector('.register-container').style.display = 'none';
