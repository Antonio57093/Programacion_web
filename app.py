from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from db import Database 
import ssl

app = Flask(__name__)
app.secret_key = "clave_secreta"
# Conexión BD
db = Database()
def get_db_connection():
    return db.connect()

# Decorador para proteger rutas según rol
def role_required(roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if "usuario" not in session or "rol" not in session:
                return redirect(url_for("home"))
            if session["rol"] not in roles:
                return "Acceso denegado: no tienes permisos suficientes"
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# Página de login
@app.route("/", methods=["GET"])
def home():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    usuario = request.form["usuario"].strip()
    contrasena = request.form["contrasena"].strip()

    if not usuario or not contrasena:
        return render_template("login.html", error="Por favor llena todos los campos antes de continuar.")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM clientes WHERE usuario=%s",
        (usuario,),
    )
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['contrasena'], contrasena):  # ✅ Verificar hash
        session["usuario"] = user["usuario"]
        session["rol"] = user.get("rol", "user")
        return redirect(url_for("inicio"))
    else:
        return render_template("login.html", error="Usuario o contraseña incorrectos")

# Página de registro
@app.route("/registro", methods=["GET", "POST"])
def registro():
    mensaje = ""
    datos_formulario = {
        "usuario": "",
        "correo": "",
        "nombre": "",
        "contrasena": "",
        "confirmar_contrasena": ""
    }
    if request.method == "POST":
        usuario = request.form["usuario"]
        correo = request.form["correo"]
        nombre = request.form["nombre"]
        contrasena = request.form["contrasena"]
        confirmar = request.form["confirmar_contrasena"]

        datos_formulario={
            "usuario": usuario,
            "correo": correo,
            "nombre": nombre,
            "contrasena": contrasena,
            "confirmar_contrasena": confirmar
        }

        if contrasena != confirmar:
            mensaje = "Las contraseñas no coinciden"
            return render_template("registro.html", mensaje=mensaje,datos=datos_formulario)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM clientes WHERE usuario=%s OR correo=%s",
            (usuario, correo),
        )
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            conn.close()
            if usuario_existente["usuario"] == usuario:
                mensaje = "El nombre de usuario ya está en uso."
            else:
                mensaje = "El correo electrónico ya está registrado."
            return render_template("registro.html", mensaje=mensaje,datos=datos_formulario)



        # Hashear la contraseña antes de guardarla
        contrasena_cifrada = generate_password_hash(contrasena)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (usuario, nombre, correo, contrasena, rol) VALUES (%s,%s,%s,%s,%s)",
            (usuario, nombre, correo, contrasena_cifrada, "user"), 
        )
        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    return render_template("registro.html", mensaje=mensaje,datos=datos_formulario)

@app.route("/verificar_usuario_email")
def verificar_usuario_email():
    usuario = request.args.get('usuario', '')
    correo = request.args.get('correo', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT usuario, correo FROM clientes WHERE usuario=%s OR correo=%s",
        (usuario, correo)
    )
    usuario_existente = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if usuario_existente:
        if usuario_existente["usuario"] == usuario:
            return {"disponible": False, "mensaje": "El nombre de usuario ya está en uso"}
        elif usuario_existente["correo"] == correo:
            return {"disponible": False, "mensaje": "El correo electrónico ya está registrado"}
    
    return {"disponible": True, "mensaje": "Disponible"}

# Página de inicio después del login
@app.route("/inicio")
def inicio():
    if "usuario" in session:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT nombre, costo FROM servicios")
            servicios = cursor.fetchall()
            cursor.close()
            conn.close()
        except mysql.connector.Error:
            servicios = None
        return render_template(
            "inicio.html", usuario=session["usuario"], servicios=servicios, rol=session.get("rol")
        )
    return redirect(url_for("home"))




# Gestión de usuarios
@app.route("/usuarios")
@role_required(["admin"])
def usuarios_panel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, usuario, nombre, correo, rol FROM clientes")
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("usuarios.html", usuarios=usuarios)


# Agregar usuario
@app.route("/usuarios/agregar", methods=["POST"])
@role_required(["admin"])
def usuarios_agregar():
    usuario = request.form["usuario"]
    nombre = request.form["nombre"]
    correo = request.form["correo"]
    contrasena = request.form["contrasena"]
    rol = request.form["rol"]
    contrasena_cifrada = generate_password_hash(contrasena)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clientes (usuario, nombre, correo, contrasena, rol) VALUES (%s, %s, %s, %s, %s)",
        (usuario, nombre, correo, contrasena_cifrada, rol)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("usuarios_panel"))


#Editar usuario
@app.route("/usuarios/editar", methods=["POST"])
@role_required(["admin"])
def usuarios_editar():
    id_usuario = request.form["id"]
    usuario = request.form["usuario"]
    nombre = request.form["nombre"]
    correo = request.form["correo"]
    rol = request.form["rol"]
    contrasena = request.form["contrasena"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Si no se cambia la contraseña, solo actualiza los demás campos
    if contrasena.strip():
        contrasena_cifrada = generate_password_hash(contrasena)
        cursor.execute(
            "UPDATE clientes SET usuario=%s, nombre=%s, correo=%s, rol=%s, contrasena=%s WHERE id=%s",
            (usuario, nombre, correo, rol, contrasena_cifrada, id_usuario)
        )
    else:
        cursor.execute(
            "UPDATE clientes SET usuario=%s, nombre=%s, correo=%s, rol=%s WHERE id=%s",
            (usuario, nombre, correo, rol, id_usuario)
        )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("usuarios_panel"))


#Eliminar usuario
@app.route("/usuarios/eliminar", methods=["POST"])
@role_required(["admin"])
def usuarios_eliminar():
    id_usuario = request.form["id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = %s", (id_usuario,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("usuarios_panel"))

# Panel de administración
@app.route("/admin")
@role_required(["admin"])
def admin_panel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM servicios")
    servicios = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin.html", servicios=servicios)


@app.route("/agregar_servicio", methods=["POST"])
@role_required(["admin"])
def agregar_servicio():
    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    costo = request.form["costo"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO servicios (nombre, descripcion, costo) VALUES (%s, %s, %s)",
        (nombre, descripcion, costo)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_panel"))

@app.route("/eliminar_servicio", methods=["POST"])
@role_required(["admin"])
def eliminar_servicio():
    id_servicio = request.form["id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM servicios WHERE id = %s", (id_servicio,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_panel"))

@app.route("/actualizar_servicio", methods=["POST"])
@role_required(["admin"])
def actualizar_servicio():
    id_servicio = request.form["id"]
    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    costo = request.form["costo"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE servicios SET nombre=%s, descripcion=%s, costo=%s WHERE id=%s",
        (nombre, descripcion, costo, id_servicio)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_panel"))

#
# Cerrar sesion
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    print("Servidor HTTPS ejecutándose en: https://localhost:5000")
    
    # SIN ADVERTENCIAS - forma moderna
    app.run(
        host="0.0.0.0", 
        port=5000, 
        debug=True,
        ssl_context=('ssl/cert.pem', 'ssl/key.pem')
    )