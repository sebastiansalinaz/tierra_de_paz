INSTRUCCIONES

Este software utiliza una version,
Python 3.12.1 en adelante.
python.exe -m pip install --upgrade pip


## Instalación
### Paso 1: Clonar el repositorio
Clona el repositorio desde GitHub utilizando el siguiente comando:
git clone https://github.com/sebastiansalinaz/tierra_de_paz



### Paso 2: 
Abre tu editor de código y selecciona la carpeta tierra_de_paz-main.
dentro de la carpeta clonada: tierra_de_paz-main

Dentro de esta carpeta, crea un entorno virtual con el siguiente comando:
python -m venv env

Activa el entorno virtual con el comando adecuado para tu sistema operativo:
En Windows:
env\Scripts\activate

En macOS/Linux:
source env/bin/activate



### Paso 3: Instalar las dependencias
Accede a la carpeta app dentro del proyecto:
cd app

Instala todas las dependencias necesarias ejecutando:
pip install -r requirements.txt

Si es necesario, actualiza pip nuevamente:
python.exe -m pip install --upgrade pip



### Paso 4: Configurar la base de datos
Configura la base de datos para el proyecto. Utiliza XAMPP para iniciar un servidor local y abre phpMyAdmin. 
En la línea 35 del archivo app.py, configura el nombre de la base de datos:
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/tierra-de-paz'

Inicializa y migra la base de datos con los siguientes comandos:
flask db init
flask db migrate
flask db upgrade



### Paso 5: Ejecutar la aplicación
Inicia la aplicación ejecutando:
python app.py 
La aplicación estará disponible en la dirección:
http://127.0.0.1:8000/

Alternativamente, puedes usar:
flask run
La aplicación estará disponible en:
http://127.0.0.1:5000/



### Paso 6: Importar datos precargados.
Importa los datos precargados en la base de datos.
El archivo SQL con los datos se encuentra en la raíz del proyecto. 
Usa tu gestor de bases de datos MySQL (phpMyAdmin) para importar este archivo.



### Paso 7: Iniciar.
Accede a la aplicación en la siguiente dirección:
http://127.0.0.1:8000/login
Ingresa tus credenciales para iniciar sesión. Serás redirigido automáticamente al panel de control.


_________________________________________________________________________________________________________________
Siguiendo estos pasos, podrás instalar y configurar el proyecto correctamente.
