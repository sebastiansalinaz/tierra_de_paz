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
from sqlalchemy.orm import joinedload



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
    actividades = Actividad.query.options(joinedload(Actividad.actividad_padre)).all()
    registros = Registro.query.all()

    actividades_with_subregistros = []
    for actividad in actividades:
        actividad_dict = actividad.__dict__
        actividad_dict['registros'] = actividad.get_all_registros()
        actividad_dict['subactividad_nombres'] = actividad.get_all_subactividad_nombres()
        actividades_with_subregistros.append(actividad_dict)

    return render_template('modules/usuarios.html', actividades=actividades_with_subregistros, registros=registros)






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
def proyectos():
    # Obtener todos los proyectos de la base de datos
    proyectos = Proyecto.query.all()
    
    # Renderizar la plantilla de proyectos y pasar los proyectos como contexto
    return render_template('modules/proyectos.html', proyectos=proyectos)



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
    # Obtener todos los registros de la tabla 'Proyecto'
    proyectos = Proyecto.query.all()
    
    # Crear una lista de diccionarios con los datos de los proyectos
    datos_tabla_proyectos = []
    for proyecto in proyectos:
        datos_tabla_proyectos.append({
            'id': proyecto.id,
            'nombre': proyecto.nombre,
            'descripcion': proyecto.descripcion,
            'cluster': proyecto.cluster,
            'responsable': proyecto.responsable,
            'fecha_inicio': proyecto.fecha_inicio.strftime('%Y-%m-%d'),  # Formato de fecha YYYY-MM-DD
            'fecha_finalizacion': proyecto.fecha_finalizacion.strftime('%Y-%m-%d'),  # Formato de fecha YYYY-MM-DD
            'estado': proyecto.estado
        })
    
    # Devolver los datos de la tabla en formato JSON
    return jsonify(datos_tabla_proyectos)




@app.route('/editar_proyecto/<int:proyecto_id>', methods=['GET', 'POST'])
@login_required
def editar_proyecto(proyecto_id):
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    actividades = Actividad.query.all()  # Obtener todas las actividades
    
    if request.method == 'POST':
        proyecto.nombre = request.form['nombre']
        proyecto.descripcion = request.form['descripcion']
        proyecto.cluster = request.form['cluster']
        proyecto.responsable = request.form['responsable']
        proyecto.fecha_inicio = request.form['fecha_inicio']
        proyecto.fecha_finalizacion = request.form['fecha_finalizacion']
        proyecto.estado = request.form['estado']

        db.session.commit()

        flash('¡Proyecto actualizado exitosamente!', 'success')
        return redirect(url_for('proyectos'))

    return render_template('editar_proyecto.html', proyecto=proyecto, actividades=actividades)  # Pasar las actividades como contexto



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


@app.route('/agregar_beneficiarios/<int:proyecto_id>', methods=['POST'])
@login_required
def agregar_beneficiarios(proyecto_id):
    if request.method == 'POST':
        actividad_id = request.form['actividad']
        proyecto = Proyecto.query.get_or_404(proyecto_id)
        actividad = Actividad.query.get_or_404(actividad_id)
        
        # Recuperar todas las actividades creadas anteriormente
        actividades = Actividad.query.all()
        
        beneficiarios_seleccionados = request.form.getlist('beneficiarios')

        # Itera sobre los IDs de los beneficiarios seleccionados y crea registros asociados con la actividad
        for beneficiario_id in beneficiarios_seleccionados:
            # Comprueba si ya existe un registro para este beneficiario y esta actividad
            if not Registro.query.filter_by(beneficiario_id=beneficiario_id, actividad_id=actividad.id).first():
                # Crea un nuevo registro para el beneficiario asociado con la actividad
                nuevo_registro = Registro(beneficiario_id=beneficiario_id, actividad_id=actividad.id)
                db.session.add(nuevo_registro)

        # Guarda los cambios en la base de datos
        db.session.commit()

        flash('Beneficiarios agregados exitosamente al proyecto.', 'success')
        return redirect(url_for('proyectos'))



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
def catalogo():
 return render_template('modules/recursos.html')




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
