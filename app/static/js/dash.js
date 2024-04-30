const allSideMenu = document.querySelectorAll('#sidebar .side-menu.top li a');

allSideMenu.forEach(item=> {
	const li = item.parentElement;

	item.addEventListener('click', function () {
		allSideMenu.forEach(i=> {
			i.parentElement.classList.remove('active');
		})
		li.classList.add('active');
	})
});




// TOGGLE SIDEBAR
const menuBar = document.querySelector('#content nav .bx.bx-menu');
const sidebar = document.getElementById('sidebar');

menuBar.addEventListener('click', function () {
	sidebar.classList.toggle('hide');
})







const searchButton = document.querySelector('#content nav form .form-input button');
const searchButtonIcon = document.querySelector('#content nav form .form-input button .bx');
const searchForm = document.querySelector('#content nav form');

searchButton.addEventListener('click', function (e) {
	if(window.innerWidth < 576) {
		e.preventDefault();
		searchForm.classList.toggle('show');
		if(searchForm.classList.contains('show')) {
			searchButtonIcon.classList.replace('bx-search', 'bx-x');
		} else {
			searchButtonIcon.classList.replace('bx-x', 'bx-search');
		}
	}
})





if(window.innerWidth < 768) {
	sidebar.classList.add('hide');
} else if(window.innerWidth > 576) {
	searchButtonIcon.classList.replace('bx-x', 'bx-search');
	searchForm.classList.remove('show');
}


window.addEventListener('resize', function () {
	if(this.innerWidth > 576) {
		searchButtonIcon.classList.replace('bx-x', 'bx-search');
		searchForm.classList.remove('show');
	}
})



const switchMode = document.getElementById('switch-mode');

switchMode.addEventListener('change', function () {
	if(this.checked) {
		document.body.classList.add('dark');
	} else {
		document.body.classList.remove('dark');
	}
})



// JavaScript para manejar el menú desplegable
document.addEventListener("DOMContentLoaded", function() {
	var dropdowns = document.querySelectorAll('.dropdown');
	dropdowns.forEach(function(dropdown) {
		dropdown.addEventListener('click', function(event) {
			event.stopPropagation();
			this.querySelector('.dropdown-content').classList.toggle('show');
			this.querySelector('.profile-dropdown i').classList.toggle('rotate');
		});
	});
	// Cerrar el menú desplegable cuando se hace clic fuera de él
	window.onclick = function(event) {
		if (!event.target.matches('.dropdown')) {
			var dropdowns = document.getElementsByClassName("dropdown-content");
			for (var i = 0; i < dropdowns.length; i++) {
				var openDropdown = dropdowns[i];
				if (openDropdown.classList.contains('show')) {
					openDropdown.classList.remove('show');
					document.querySelector('.profile-dropdown i').classList.remove('rotate');
				}
			}
		}
	}
});


    // Obtiene el botón de abrir modal
    var openModalBtn = document.getElementById("openModalBtn");

    // Obtiene el modal
    var modal = document.getElementById("myModal");

    // Obtiene el botón de cerrar modal
    var closeModalBtn = document.getElementById("closeModalBtn");

    // Cuando el usuario hace clic en el botón de abrir modal, muestra el modal
    openModalBtn.onclick = function() {
        modal.style.display = "block";
    }

    // Cuando el usuario hace clic en el botón de cerrar modal (x), oculta el modal
    closeModalBtn.onclick = function() {
        modal.style.display = "none";
    }

    // Cuando el usuario hace clic en cualquier parte fuera del modal, lo cierra
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }


	// Función para mostrar el modal
function mostrarModal() {
    var modal = document.getElementById('confirmarEliminarModal');
    modal.style.display = 'block';
    // Agregar el evento para cerrar el modal al presionar la tecla Esc
    window.addEventListener('keydown', cerrarConEsc);
}

// Función para cerrar el modal
function cerrarModal() {
    var modal = document.getElementById('confirmarEliminarModal');
    modal.style.display = 'none';
    // Remover el evento para cerrar el modal al presionar la tecla Esc
    window.removeEventListener('keydown', cerrarConEsc);
}

// Función para cerrar el modal al presionar la tecla Esc
function cerrarConEsc(event) {
    if (event.key === 'Escape') {
        cerrarModal();
    }
}
