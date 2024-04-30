function redirectLogin() {
    window.location.href = "/login";
}

function redirectRegistro() {
    window.location.href = "/registro";
}


document.addEventListener('DOMContentLoaded', function() {
    const formLogin = document.querySelector('.container-form.login');
    formLogin.classList.add('show');
});



document.getElementById('openSidebar').addEventListener('click', function() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('active');
    
    const icon = document.querySelector('#openSidebar i');
    icon.classList.toggle('rotated');
});
