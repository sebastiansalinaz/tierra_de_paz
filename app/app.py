from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, login_user, current_user, logout_user, UserMixin
import os
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import or_
from datetime import datetime
from pytz import timezone
import pandas as pd
import plotly.express as px
from flask import jsonify
from flask import make_response



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/tierra-de-paz'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TIMEZONE'] = 'America/Bogota'
os.environ['TZ'] = app.config['TIMEZONE']
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(400), nullable=False)
    foto_perfil = db.Column(db.String(200))  

class Documento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(100))
    fecha_registro = db.Column(db.DateTime, default=lambda: datetime.now(timezone('America/Bogota')))
    archivo = db.Column(db.String(100))

class Catalogo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(100))
    fecha_registro = db.Column(db.DateTime, default=lambda: datetime.now(timezone('America/Bogota')))
    archivo = db.Column(db.String(100))

class Actividad(db.Model):
    __tablename__ = 'actividad'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    persona_encargada = db.Column(db.String(100), nullable=True)
    fecha_realizacion = db.Column(db.Date, nullable=False)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyecto.id'), nullable=True)  # Ahora es opcional
    registros = db.relationship('Registro', backref='actividad', lazy=True)


class Registro(db.Model):
    __tablename__ = 'registro'  # Agregando el nombre de la tabla explícitamente
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    tipo_documento = db.Column(db.String(20), nullable=False)
    numero_documento = db.Column(db.String(20), nullable=False)
    pais = db.Column(db.String(100), nullable=False)
    departamento = db.Column(db.String(100), nullable=False)
    municipio = db.Column(db.String(100), nullable=False)
    genero = db.Column(db.String(20), nullable=False)
    edad = db.Column(db.Integer, nullable=False)
    grupo_edad = db.Column(db.String(20), nullable=False)
    grupo_etnico = db.Column(db.String(50), nullable=False)
    discapacidad = db.Column(db.String(2), nullable=False)
    comunidad = db.Column(db.String(100), nullable=False)
    actividad_id = db.Column(db.Integer, db.ForeignKey('actividad.id'), nullable=False)

class Proyecto(db.Model):
    __tablename__ = 'proyecto'  # Agregando el nombre de la tabla explícitamente
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    cluster = db.Column(db.String(50), nullable=False)
    responsable = db.Column(db.String(100), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_finalizacion = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), nullable=False)
    actividades = db.relationship('Actividad', backref='proyecto', lazy=True)








@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        if Usuario.query.filter_by(correo=correo).first():
            flash('El correo ya está registrado.', 'error')
            return redirect(url_for('registro'))

        hashed_password = generate_password_hash(contraseña).decode('utf-8')

        nuevo_usuario = Usuario(nombre=nombre, correo=correo, contraseña=hashed_password)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('¡Registro exitoso!', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario:
            if check_password_hash(usuario.contraseña, contraseña):
                login_user(usuario)
                flash('¡Inicio de sesión exitoso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                error_message = 'Contraseña incorrecta. Por favor, verifica tu contraseña.'
        else:
            error_message = 'No se encuentra el Correo electronico. Por favor, verifica tu correo.'

    return render_template('login.html', error_message=error_message)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('¡Has cerrado sesión exitosamente!', 'success')
    return redirect(url_for('login'))

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/usuarios')
@login_required
def usuarios():
    # Obtener todas las actividades de la base de datos
    actividades = Actividad.query.all()
    
    # Obtener todos los registros de usuarios de la base de datos
    registros = Registro.query.all()

    # Renderizar la plantilla de eventos y pasar las actividades y registros como contexto
    return render_template('modules/usuarios.html', actividades=actividades, registros=registros)




@app.route('/guardar_actividad', methods=['POST'])
@login_required
def guardar_actividad():
    if request.method == 'POST':
        # Verificar el token CSRF
        if 'csrf_token' not in request.form:
            flash('Token CSRF faltante. Intente enviar el formulario nuevamente.', 'error')
            return redirect(url_for('usuarios'))

        # Obtener los datos del formulario
        nombre_actividad = request.form['nombre_actividad']
        persona_encargada = request.form['persona_encargada']
        fecha_realizacion = request.form['fecha_realizacion']

        # Crear una nueva instancia de la clase Actividad
        nueva_actividad = Actividad(
            nombre=nombre_actividad,
            persona_encargada=persona_encargada,
            fecha_realizacion=fecha_realizacion
        )

        # Agregar la nueva actividad a la base de datos
        db.session.add(nueva_actividad)
        db.session.commit()

        # Devolver la información de la actividad recién creada al cliente
        return jsonify({'nombre': nueva_actividad.nombre})

    # Manejar el caso donde el método de solicitud no es POST
    # Si llega aquí, podría ser una buena idea mostrar un mensaje de error o redirigir a otra página
    flash('Error al procesar la solicitud', 'error')
    return redirect(url_for('usuarios'))


@app.route('/guardar_registro', methods=['POST'])
def guardar_registro():
    if request.method == 'POST':
        # Recupera los datos del formulario
        nombres = request.form['nombres']
        apellidos = request.form['apellidos']
        tipo_documento = request.form['tipo_documento']
        numero_documento = request.form['numero_documento']
        pais = request.form['pais']
        departamento = request.form['departamento']
        municipio = request.form['municipio']
        genero = request.form['genero']
        edad = request.form['edad']
        grupo_edad = request.form['grupo_edad']
        grupo_etnico = request.form['grupo_etnico']
        discapacidad = request.form['discapacidad']
        comunidad = request.form['comunidad']
        actividad_nombre = request.form['actividad']

        # Buscar la actividad por su nombre
        actividad = Actividad.query.filter_by(nombre=actividad_nombre).first()

        if actividad:
            # Crea un nuevo registro en la base de datos
            nuevo_registro = Registro(
                nombres=nombres,
                apellidos=apellidos,
                tipo_documento=tipo_documento,
                numero_documento=numero_documento,
                pais=pais,
                departamento=departamento,
                municipio=municipio,
                genero=genero,
                edad=edad,
                grupo_edad=grupo_edad,
                grupo_etnico=grupo_etnico,
                discapacidad=discapacidad,
                comunidad=comunidad,
                actividad=actividad
            )

            # Guarda el nuevo registro en la base de datos
            db.session.add(nuevo_registro)
            db.session.commit()

            # Redirige a una página de éxito o a donde desees
            flash('Registro exitoso!', 'success')
            return redirect(url_for('usuarios'))
        else:
            flash('No se encontró la actividad especificada', 'error')
            return redirect(url_for('usuarios'))


@app.route('/get_activities', methods=['GET'])
@login_required
def get_activities():
    actividades = Actividad.query.all()
    actividades_list = [{'nombre': actividad.nombre} for actividad in actividades]
    return jsonify(actividades_list)


@app.route('/get_datos_tabla', methods=['GET'])
@login_required
def get_datos_tabla():
    # Obtener todos los registros de la tabla 'Registro'
    registros = Registro.query.all()
    
    # Crear una lista de diccionarios con los datos de los registros
    datos_tabla = []
    for registro in registros:
        datos_tabla.append({
            'nombres': registro.nombres,
            'apellidos': registro.apellidos,
            'tipo_documento': registro.tipo_documento,
            'numero_documento': registro.numero_documento,
            'pais': registro.pais,
            'departamento': registro.departamento,
            'municipio': registro.municipio,
            'genero': registro.genero,
            'edad': registro.edad,
            'grupo_edad': registro.grupo_edad,
            'grupo_etnico': registro.grupo_etnico,
            'discapacidad': registro.discapacidad,
            'comunidad': registro.comunidad,
            'actividad': registro.actividad.nombre  # Nombre de la actividad asociada al registro
        })
    
    # Devolver los datos de la tabla en formato JSON
    return jsonify(datos_tabla)




@app.route('/eliminar_registro/<int:registro_id>', methods=['POST'])
@login_required
def eliminar_registro(registro_id):
    registro = Registro.query.get_or_404(registro_id)
    db.session.delete(registro)
    db.session.commit()
    flash('Registro eliminado correctamente.', 'success')
    return redirect(url_for('usuarios'))






@app.route('/proyectos')
@login_required
def busqueda():
    return render_template('modules/proyectos.html')

@app.route('/eventos')
@login_required
def eventos():
    df = pd.read_csv('datos.csv')

    bar_fig = px.bar(df, x='mes', y='cantidad_personas', title='Cantidad de personas por mes', labels={'cantidad_personas': 'Cantidad de personas'})
    bar_fig.update_xaxes(title='Mes', tickangle=45)
    bar_fig.update_yaxes(title='Cantidad de personas')

    pie_fig = px.pie(df, values='cantidad_personas', names='mes', title='Distribución de la cantidad de personas por mes')

    bar_html = bar_fig.to_html(full_html=False)
    pie_html = pie_fig.to_html(full_html=False)

    return render_template('modules/eventos.html', bar_html=bar_html, pie_html=pie_html)

@app.route('/actualizacion')
@login_required
def actualizacion():
    return render_template('modules/actualizacion.html')

@app.route('/recursos')
@login_required
def catalogo():
 return render_template('modules/recursos.html')

@app.route('/cargar_catalogo', methods=['POST'])
def cargar_catalogo():
    if request.method == 'POST':
        descripcion = request.form['descripcion']
        archivo = request.files['documento']
        catalogo = Catalogo(descripcion=descripcion, archivo=archivo.filename)
        db.session.add(catalogo)
        db.session.commit()
        archivo.save(f"uploads/{secure_filename(archivo.filename)}")
        return redirect(url_for('catalogo'))

@app.route('/previsualizar_catalogo/<int:id>')
def previsualizar_catalogo(id):
    catalogo = db.session.get(Catalogo, id)
    if catalogo:
        return send_from_directory(app.config['UPLOAD_FOLDER'], catalogo.archivo, as_attachment=False)
    else:
        flash('Catalogo no encontrado', 'error')
        return redirect(url_for('catalogo'))

@app.route('/eliminar_catalogo/<int:id>')
def eliminar_catalogo(id):
    catalogo = db.session.get(Catalogo, id)
    if catalogo:
        db.session.delete(catalogo)
        db.session.commit()
        return redirect(url_for('catalogo'))
    else:
        flash('Catalogo no encontrado', 'error')
        return redirect(url_for('catalogo'))

@app.route('/documentacion')
@login_required
def documentacion():
    page = request.args.get('page', 1, type=int)
    per_page = 7

    search_term = request.args.get('search', '')

    if search_term:
        documentos = Documento.query.filter(or_(Documento.descripcion.contains(search_term),
                                                 Documento.archivo.contains(search_term))) \
                                    .order_by(Documento.fecha_registro.desc()) \
                                    .paginate(page=page, per_page=per_page)
    else:
        documentos = Documento.query.order_by(Documento.fecha_registro.desc()) \
                                    .paginate(page=page, per_page=per_page)

    return render_template('modules/documentacion.html', documentos=documentos)


@app.route('/cargar_documento', methods=['POST'])
def cargar_documento():
    if request.method == 'POST':
        descripcion = request.form['descripcion']
        archivo = request.files['documento']
        documento = Documento(descripcion=descripcion, archivo=archivo.filename)
        db.session.add(documento)
        db.session.commit()
        archivo.save(f"uploads/{secure_filename(archivo.filename)}")
        return redirect(url_for('documentacion'))

@app.route('/previsualizar_documento/<int:id>')
def previsualizar_documento(id):
    documento = db.session.get(Documento, id)
    if documento:
        return send_from_directory(app.config['UPLOAD_FOLDER'], documento.archivo, as_attachment=False)
    else:
        flash('Documento no encontrado', 'error')
        return redirect(url_for('documentacion'))

@app.route('/eliminar_documento/<int:id>')
def eliminar_documento(id):
    documento = db.session.get(Documento, id)
    if documento:
        db.session.delete(documento)
        db.session.commit()
        return redirect(url_for('documentacion'))
    else:
        flash('Documento no encontrado', 'error')
        return redirect(url_for('documentacion'))

@app.route('/editar_perfil')
@login_required
def editar_perfil():
    return render_template('edit.html')

@app.route('/eliminar_perfil', methods=['GET', 'POST'])
@login_required
def eliminar_perfil():
    user = current_user
    db.session.delete(user)
    db.session.commit()
    flash('Tu cuenta ha sido eliminada correctamente.', 'success')
    return redirect(url_for('login'))

@app.route('/guardar_perfil', methods=['POST'])
@login_required
def guardar_perfil():
    nombre = request.form['nombre']
    correo = request.form['correo']
    contraseña = request.form['contraseña']
    foto = request.files['foto']

    current_user.nombre = nombre
    current_user.correo = correo
    if contraseña:
        current_user.contraseña = generate_password_hash(contraseña).decode('utf-8')
    if foto:
        foto_nombre = secure_filename(foto.filename)
        foto_ruta = os.path.join(app.config['UPLOAD_FOLDER'], foto_nombre)
        foto.save(foto_ruta)
        current_user.foto_perfil = foto_nombre

    db.session.commit()

    flash('¡Perfil actualizado correctamente!', 'success')
    return redirect(url_for('editar_perfil'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
