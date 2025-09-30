from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from functools import wraps

app = Flask(__name__)
app.secret_key = "clave_secreta"

# Conexión BD
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="C8be1987d0d4", 
        database="lexcorp"
    )

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
    usuario = request.form["usuario"]
    contrasena = request.form["contrasena"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM clientes WHERE usuario=%s AND contrasena=%s",
        (usuario, contrasena),
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        session["usuario"] = user["usuario"]
        session["rol"] = user.get("rol", "user")  # si no hay rol, se asume cliente
        return redirect(url_for("inicio"))
    else:
        return "Usuario o contraseña incorrectos"

# Página de registro
@app.route("/registro", methods=["GET", "POST"])
def registro():
    mensaje = ""
    if request.method == "POST":
        usuario = request.form["usuario"]
        correo = request.form["correo"]
        nombre = request.form["nombre"]
        contrasena = request.form["contrasena"]
        confirmar = request.form["confirmar_contrasena"]

        if contrasena != confirmar:
            mensaje = "Las contraseñas no coinciden"
            return render_template("registro.html", mensaje=mensaje)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (usuario, nombre, correo, contrasena, rol) VALUES (%s,%s,%s,%s,%s)",
            (usuario, nombre, correo, contrasena, "user"),  # por defecto cliente
        )
        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    return render_template("registro.html", mensaje=mensaje)

# Página de inicio después de login
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


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

