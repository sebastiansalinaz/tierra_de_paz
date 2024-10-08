from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file
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
from sqlalchemy.orm import joinedload
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
import pdfkit
from weasyprint import HTML
from sqlalchemy.exc import IntegrityError








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
    rol = db.Column(db.Integer, nullable=False, default=3)  # Default role as Monitor

    def is_administrator(self):
        return self.rol == 1

    def is_coordinator(self):
        return self.rol == 2

    def is_monitor(self):
        return self.rol == 3
    


class Actividad(db.Model):
    __tablename__ = 'actividad'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    persona_encargada = db.Column(db.String(100), nullable=True)
    fecha_realizacion = db.Column(db.Date, nullable=False)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyecto.id'), nullable=True)
    registros = db.relationship('Registro', backref='actividad', lazy=True)
    subactividades = db.relationship('Actividad', backref=db.backref('parent', remote_side=[id]), lazy=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('actividad.id'), nullable=True)
    actividad_padre = db.relationship('Actividad', remote_side=[id], back_populates='subactividades')


    def get_all_registros(self):
        registros = self.registros.copy()
        for subactividad in self.subactividades:
            registros.extend(subactividad.get_all_registros())
        return registros

    def get_all_subactividad_nombres(self):
        subactividad_nombres = [sub.nombre for sub in self.subactividades]
        for sub in self.subactividades:
            subactividad_nombres.extend(sub.get_all_subactividad_nombres())
        return subactividad_nombres




class Registro(db.Model):
    __tablename__ = 'registro'
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
    estado = db.Column(db.String(20), nullable=False, default='habilitado')
    inhabilitado = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow) 
    imagen_url = db.Column(db.String(200))

class Proyecto(db.Model):
    __tablename__ = 'proyecto'
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
@login_required
def registro():
    if current_user.rol != 1:
        flash('No tienes permiso para realizar esta acción.', 'warning')
        return redirect(url_for('configuracion'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        rol = request.form['rol']  # Obtener el rol del formulario

        if Usuario.query.filter_by(correo=correo).first():
            flash('El correo ya está registrado.', 'error')
            return redirect(url_for('registro'))

        hashed_password = generate_password_hash(contraseña)

        nuevo_usuario = Usuario(nombre=nombre, correo=correo, contraseña=hashed_password, rol=rol)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('¡Registro exitoso!', 'success')
        return redirect(url_for('configuracion'))

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
            error_message = 'No se encuentra el correo electrónico. Por favor, verifica tu correo.'

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
    page = request.args.get('page', 1, type=int)
    per_page = 15

    search_query = request.args.get('search', '')

    registros_filtrados = Registro.query
    if search_query:
        registros_filtrados = registros_filtrados.filter(
            or_(
                Registro.nombres.like(f"%{search_query}%"),
                Registro.apellidos.like(f"%{search_query}%"),
                Registro.tipo_documento.like(f"%{search_query}%"),
                Registro.numero_documento.like(f"%{search_query}%"),
                Registro.pais.like(f"%{search_query}%"),
                Registro.departamento.like(f"%{search_query}%"),
                Registro.municipio.like(f"%{search_query}%"),
                Registro.genero.like(f"%{search_query}%"),
                Registro.grupo_edad.like(f"%{search_query}%"),
                Registro.grupo_etnico.like(f"%{search_query}%"),
                Registro.discapacidad.like(f"%{search_query}%"),
                Registro.comunidad.like(f"%{search_query}%"),
                Registro.actividad.has(Actividad.nombre.like(f"%{search_query}%"))
            )
        )

    registros_paginados = registros_filtrados.order_by(Registro.fecha_creacion.desc()).paginate(page=page, per_page=per_page, error_out=False)

    actividades = Actividad.query.options(joinedload(Actividad.actividad_padre)).all()

    actividades_with_subregistros = []
    for actividad in actividades:
        actividad_dict = actividad.__dict__
        actividad_dict['registros'] = actividad.get_all_registros()
        actividad_dict['subactividad_nombres'] = actividad.get_all_subactividad_nombres()
        actividades_with_subregistros.append(actividad_dict)

    total_pages = registros_paginados.pages

    return render_template('modules/usuarios.html', actividades=actividades_with_subregistros, registros_paginados=registros_paginados,
                           total_pages=total_pages, current_page=page, search_query=search_query)




@app.route('/search_usuarios')
@login_required
def search_usuarios():
    search_query = request.args.get('search', '')

    # Obtener todos los registros paginados que coincidan con la búsqueda si hay un término de búsqueda
    if search_query:
        registros_filtrados = Registro.query.filter(
            or_(
                Registro.nombres.like(f"%{search_query}%"),
                Registro.apellidos.like(f"%{search_query}%"),
                Registro.tipo_documento.like(f"%{search_query}%"),
                Registro.numero_documento.like(f"%{search_query}%"),
                Registro.pais.like(f"%{search_query}%"),
                Registro.departamento.like(f"%{search_query}%"),
                Registro.municipio.like(f"%{search_query}%"),
                Registro.genero.like(f"%{search_query}%"),
                Registro.grupo_edad.like(f"%{search_query}%"),
                Registro.grupo_etnico.like(f"%{search_query}%"),
                Registro.discapacidad.like(f"%{search_query}%"),
                Registro.comunidad.like(f"%{search_query}%"),
                Registro.actividad.has(Actividad.nombre.like(f"%{search_query}%"))
            )
        ).order_by(Registro.fecha_creacion.desc()).all()
    else:
        # Obtener todos los registros paginados si no hay término de búsqueda
        page = request.args.get('page', 1, type=int)
        per_page = 15
        registros_filtrados = Registro.query.order_by(Registro.fecha_creacion.desc()).paginate(page=page, per_page=per_page, error_out=False).items

    registros = []
    for registro in registros_filtrados:
        registros.append({
            'id': registro.id,
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
            'actividad': registro.actividad.nombre,
            'estado': registro.estado,
            'inhabilitado': registro.inhabilitado
        })

    return jsonify(registros)




@app.route('/historial/<int:registro_id>')
def historial_registro(registro_id):
    registro = Registro.query.get_or_404(registro_id)
    return render_template('historial.html', registro=registro)



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
        parent_id = request.form.get('parent_id')

        # Crear una nueva instancia de la clase Actividad
        nueva_actividad = Actividad(
            nombre=nombre_actividad,
            persona_encargada=persona_encargada,
            fecha_realizacion=fecha_realizacion,
            parent_id=parent_id if parent_id else None
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



@app.route('/asignar_actividades/<int:proyecto_id>', methods=['POST'])
@login_required
def asignar_actividades(proyecto_id):
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    actividades_seleccionadas = request.form.getlist('actividades[]')

    if not actividades_seleccionadas:
        flash('No se seleccionaron actividades para asignar.', 'warning')
        return redirect(url_for('editar_proyecto', proyecto_id=proyecto_id))

    actividades_conflicto = []
    for actividad_id in actividades_seleccionadas:
        actividad = Actividad.query.get(actividad_id)
        if actividad.proyecto_id and actividad.proyecto_id != proyecto_id:
            actividades_conflicto.append(actividad)

    if actividades_conflicto:
        flash('Algunas actividades ya están asignadas a otro proyecto.', 'warning')
        return redirect(url_for('editar_proyecto', proyecto_id=proyecto_id))

    try:
        for actividad_id in actividades_seleccionadas:
            actividad = Actividad.query.get(actividad_id)
            actividad.proyecto_id = proyecto_id
            db.session.add(actividad)

        db.session.commit()
        flash('¡Actividades asignadas exitosamente!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Error al asignar actividades. Intente nuevamente.', 'danger')

    return redirect(url_for('editar_proyecto', proyecto_id=proyecto_id))



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

            # Determinar la página de redirección según la URL de referencia
            redirect_page = 'usuarios' if '/usuarios' in request.referrer else 'editar_proyecto'
            
            # Obtener el proyecto_id de la ruta actual si es editar_proyecto
            proyecto_id = None
            if redirect_page == 'editar_proyecto':
                proyecto_id = request.referrer.split('/')[-1]

            # Redirige a la página correspondiente
            flash('Registro exitoso!', 'success')
            if proyecto_id:
                return redirect(url_for(redirect_page, proyecto_id=proyecto_id))
            else:
                return redirect(url_for(redirect_page))
        else:
            flash('No se encontró la actividad especificada', 'error')
            return redirect(url_for('usuarios'))  # Otra opción es redirigir a la página de usuarios en caso de error


@app.route('/obtener_registro/<int:registro_id>', methods=['GET'])
@login_required
def obtener_registro(registro_id):
    registro = Registro.query.get_or_404(registro_id)
    registro_dict = {
        'id': registro.id,
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
        'actividad': registro.actividad.nombre
    }
    return jsonify(registro_dict)


@app.route('/editar_registro', methods=['POST'])
@login_required
def editar_registro():
    registro_id = request.form.get('id')
    registro = Registro.query.get_or_404(registro_id)

    # Actualizar los campos del registro con los datos del formulario
    registro.nombres = request.form.get('nombres')
    registro.apellidos = request.form.get('apellidos')
    registro.tipo_documento = request.form.get('tipo_documento')
    registro.numero_documento = request.form.get('numero_documento')
    registro.pais = request.form.get('pais')
    registro.departamento = request.form.get('departamento')
    registro.municipio = request.form.get('municipio')
    registro.genero = request.form.get('genero')
    registro.edad = request.form.get('edad')
    registro.grupo_edad = request.form.get('grupo_edad')
    registro.grupo_etnico = request.form.get('grupo_etnico')
    registro.discapacidad = request.form.get('discapacidad')
    registro.comunidad = request.form.get('comunidad')

    # Si la actividad se selecciona a través de un select, asegúrate de obtenerla correctamente
    actividad_nombre = request.form.get('actividad')
    actividad = Actividad.query.filter_by(nombre=actividad_nombre).first()
    registro.actividad = actividad

    # Guardar los cambios en la base de datos
    db.session.commit()

    flash('Registro actualizado correctamente', 'success')

    # Redireccionar a alguna página después de editar el registro
    # Puedes redirigir a la página de detalles del registro o a cualquier otra página que desees
    return redirect(url_for('usuarios', registro_id=registro.id))



@app.route('/toggle_habilitar/<int:registro_id>', methods=['POST'])
@login_required
def toggle_habilitar(registro_id):
    registro = Registro.query.get_or_404(registro_id)
    registro.inhabilitado = not registro.inhabilitado
    db.session.commit()
    return jsonify({'status': 'success', 'inhabilitado': registro.inhabilitado})


@app.route('/upload_image/<int:registro_id>', methods=['POST'])
@login_required
def upload_image(registro_id):
    registro = Registro.query.get_or_404(registro_id)
    if 'imagen' not in request.files:
        flash('No file part', 'error')
        return redirect(request.referrer)
    
    file = request.files['imagen']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.referrer)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        registro.imagen_url = url_for('uploaded_file', filename=filename)
        db.session.commit()
        flash('Imagen actualizada con éxito', 'success')
        return redirect(url_for('historial_registro', registro_id=registro.id))
    else:
        flash('Invalid file type', 'error')
        return redirect(request.referrer)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}




@app.route('/get_activities', methods=['GET'])
@login_required
def get_activities():
    actividades = Actividad.query.all()
    actividades_list = [{'nombre': actividad.nombre} for actividad in actividades]
    return jsonify(actividades_list)







@app.route('/eliminar_actividades/<int:proyecto_id>', methods=['POST'])
@login_required
def eliminar_actividades(proyecto_id):
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    actividades_seleccionadas = request.form.getlist('actividades[]')
    
    if not actividades_seleccionadas:
        return jsonify({'status': 'warning', 'message': 'No se seleccionaron actividades para eliminar.'}), 400
    
    actividades_a_eliminar = Actividad.query.filter(Actividad.id.in_(actividades_seleccionadas)).all()
    
    try:
        for actividad in actividades_a_eliminar:
            # Elimina la actividad de todas las relaciones
            if actividad in proyecto.actividades:
                proyecto.actividades.remove(actividad)
            # Elimina la actividad de la base de datos
            db.session.delete(actividad)
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': '¡Actividades eliminadas exitosamente!'}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'status': 'danger', 'message': 'No se puede eliminar la actividad seleccionada porque contiene registros asociados.'}), 400




@app.route('/get_datos_tabla', methods=['GET'])
@login_required
def get_datos_tabla():
    # Obtener todos los registros de la tabla 'Registro' en orden descendente por 'id'
    registros = Registro.query.order_by(Registro.id.desc()).all()
    
    # Crear una lista de diccionarios con los datos de los registros
    datos_tabla = []
    for registro in registros:
        datos_tabla.append({
            'id': registro.id,  # Asegurarse de incluir el 'id' para las operaciones de editar/eliminar
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



@app.route('/buscar_registros', methods=['GET'])
@login_required
def buscar_registros():
    query = request.args.get('q', '')
    # Filtra los registros por nombres, apellidos, o número de documento
    registros = Registro.query.filter(
        or_(
            Registro.nombres.ilike(f'%{query}%'),
            Registro.apellidos.ilike(f'%{query}%'),
            Registro.numero_documento.ilike(f'%{query}%')
        )
    ).all()
    
    resultados = []
    for registro in registros:
        resultados.append({
            'id': registro.id,
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
            'actividad': registro.actividad.nombre,
            'inhabilitado': registro.inhabilitado
        })
    return jsonify(resultados)


@app.route('/eliminar_registro/<int:registro_id>', methods=['POST'])
@login_required
def eliminar_registro(registro_id):
    registro = Registro.query.get_or_404(registro_id)
    db.session.delete(registro)
    db.session.commit()
    flash('Registro eliminado correctamente.', 'success')
    return redirect(url_for('usuarios'))



@app.route('/get_estadisticas_usuarios')
@login_required
def get_estadisticas_usuarios():
    total_registros = Registro.query.count()
    registros_habilitados = Registro.query.filter_by(estado='habilitado').count()
    registros_inhabilitados = Registro.query.filter_by(inhabilitado=True).count()  # Modificación aquí
    
    estadisticas = {
        'registrados': total_registros,
        'habilitados': registros_habilitados,
        'inhabilitados': registros_inhabilitados
    }
    
    return jsonify(estadisticas)




@app.route('/proyectos')
@login_required
def proyectos():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Número de proyectos por página
    proyectos_paginados = Proyecto.query.paginate(page=page, per_page=per_page)
    
    return render_template('modules/proyectos.html', proyectos_paginados=proyectos_paginados)




@app.route('/crear_proyecto', methods=['POST'])
@login_required
def crear_proyecto():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        cluster = request.form.get('cluster')
        responsable = request.form.get('responsable')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_finalizacion = request.form.get('fecha_finalizacion')
        estado = request.form.get('estado')
        
        # Crear un nuevo objeto Proyecto con los datos del formulario
        nuevo_proyecto = Proyecto(nombre=nombre, descripcion=descripcion, cluster=cluster,
                                  responsable=responsable, fecha_inicio=fecha_inicio,
                                  fecha_finalizacion=fecha_finalizacion, estado=estado)
        # Guardar el nuevo proyecto en la base de datos
        db.session.add(nuevo_proyecto)
        db.session.commit()
        
        flash('¡Proyecto creado exitosamente!', 'success')
        return redirect(url_for('proyectos'))  # Redireccionar a la página de proyectos

    # Redireccionar a la página de proyectos si se accede a la ruta por métodos diferentes a POST
    return redirect(url_for('proyectos'))


@app.route('/get_datos_tabla_proyectos', methods=['GET'])
@login_required
def get_datos_tabla_proyectos():
    proyectos = Proyecto.query.all()
    
    datos_tabla_proyectos = []
    for proyecto in proyectos:
        datos_tabla_proyectos.append({
            'id': proyecto.id,
            'nombre': proyecto.nombre,
            'descripcion': proyecto.descripcion,
            'cluster': proyecto.cluster,
            'responsable': proyecto.responsable,
            'fecha_inicio': proyecto.fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_finalizacion': proyecto.fecha_finalizacion.strftime('%Y-%m-%d'),
            'estado': proyecto.estado
        })
    
    return jsonify(datos_tabla_proyectos)




@app.route('/editar_proyecto/<int:proyecto_id>', methods=['GET', 'POST'])
@login_required
def editar_proyecto(proyecto_id):
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    actividades = Actividad.query.all()

    if request.method == 'POST':
        proyecto.nombre = request.form['nombre']
        proyecto.descripcion = request.form['descripcion']
        proyecto.cluster = request.form['cluster']
        proyecto.responsable = request.form['responsable']
        proyecto.fecha_inicio = request.form['fecha_inicio']
        proyecto.fecha_finalizacion = request.form['fecha_finalizacion']
        proyecto.estado = request.form['estado']

        # Obtener las actividades seleccionadas para este proyecto
        actividades_seleccionadas = request.form.getlist('actividades[]')
        actividades = Actividad.query.filter(Actividad.id.in_(actividades_seleccionadas)).all()
        
        proyecto.actividades = actividades

        db.session.commit()

        flash('¡Proyecto actualizado exitosamente!', 'success')
        return redirect(url_for('editar_proyecto', proyecto_id=proyecto.id))

    # Recuperar registros de las actividades relacionadas con el proyecto, excluyendo los deshabilitados
    actividades_del_proyecto = proyecto.actividades
    registros = []
    unique_ids = set()
    for actividad in actividades_del_proyecto:
        for registro in actividad.get_all_registros():
            if registro.id not in unique_ids and not registro.inhabilitado:
                unique_ids.add(registro.id)
                registros.append(registro)
    
    # Definir estado_proyecto basado en el estado actual del proyecto
    estado_proyecto = proyecto.estado.lower()

    # Obtener las actividades seleccionadas para pasarlas a la plantilla
    actividades_seleccionadas = [actividad.id for actividad in proyecto.actividades]

    return render_template('editar_proyecto.html', proyecto=proyecto, actividades=actividades, registros=registros, estado_proyecto=estado_proyecto, actividades_seleccionadas=actividades_seleccionadas)




@app.route('/get_proyecto/<int:proyecto_id>', methods=['GET'])
@login_required
def get_proyecto(proyecto_id):
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    proyecto_data = {
        'id': proyecto.id,
        'nombre': proyecto.nombre,
        'descripcion': proyecto.descripcion,
        'cluster': proyecto.cluster,
        'responsable': proyecto.responsable,
        'fecha_inicio': proyecto.fecha_inicio,
        'fecha_finalizacion': proyecto.fecha_finalizacion,
        'estado': proyecto.estado
    }
    return jsonify(proyecto_data)








@app.route('/get_estadisticas_proyectos')
def get_estadisticas_proyectos():
    # Lógica para obtener las estadísticas de proyectos desde la base de datos
    proyectos_registrados = Proyecto.query.count()
    proyectos_activos = Proyecto.query.filter_by(estado='Activo').count()
    proyectos_terminados = Proyecto.query.filter_by(estado='Inactivo').count()

    # Crear un diccionario con las estadísticas
    estadisticas = {
        'registrados': proyectos_registrados,
        'activos': proyectos_activos,
        'terminados': proyectos_terminados
    }

    # Devolver los datos en formato JSON
    return jsonify(estadisticas)







@app.route('/generate_pdf/<int:proyecto_id>')
@login_required
def generate_pdf(proyecto_id):
    # Obtener datos del proyecto
    proyecto = Proyecto.query.get(proyecto_id)

    # Obtener todas las actividades asociadas al proyecto
    actividades = Actividad.query.filter_by(proyecto_id=proyecto_id).all()
    
    # Obtener los registros asociados a estas actividades, excluyendo los inhabilitados
    registros = Registro.query.filter(Registro.actividad_id.in_([actividad.id for actividad in actividades]), Registro.inhabilitado == False).all()

    # Ruta completa de la imagen
    image_path = os.path.join(app.root_path, 'static', 'img', 'logo.png')

    # Renderizar la plantilla HTML
    rendered_html = render_template('pdf_template.html', proyecto=proyecto, registros=registros, image_path=image_path)

    # Generar PDF con WeasyPrint
    pdf = HTML(string=rendered_html, base_url=request.host_url).write_pdf()

    # Crear una respuesta Flask con el PDF
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=proyecto_{proyecto_id}.pdf'
    return response













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



@app.route('/recursos')
@login_required
def recursos():
 return render_template('modules/recursos.html')




@app.route('/editar_perfil')
@login_required
def editar_perfil():
    if current_user.rol == 3:
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('dashboard'))
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


@app.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    if current_user.rol not in [1, 2]:
        flash('No tienes permiso para acceder a esta página.', 'warning')
        return redirect(url_for('dashboard'))

    usuarios = Usuario.query.all()
    return render_template('modules/configuracion.html', usuarios=usuarios, current_user=current_user)

@app.route('/editar_usuario/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(usuario_id):
    if current_user.rol != 1:
        flash('No tienes permiso para realizar esta acción.', 'warning')
        return redirect(url_for('configuracion'))

    usuario = Usuario.query.get_or_404(usuario_id)

    if request.method == 'POST':
        usuario.nombre = request.form['nombre']
        usuario.correo = request.form['correo']
        usuario.rol = request.form['rol']

        db.session.commit()
        flash('Usuario actualizado correctamente.', 'success')
        return redirect(url_for('configuracion'))

    return render_template('modules/editar_usuario.html', usuario=usuario)

@app.route('/eliminar_usuario/<int:usuario_id>', methods=['POST'])
@login_required
def eliminar_usuario(usuario_id):
    if current_user.rol != 1:
        flash('No tienes permiso para realizar esta acción.', 'warning')
        return redirect(url_for('configuracion'))

    usuario = Usuario.query.get_or_404(usuario_id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('configuracion'))




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
