from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "clave_secreta"

# Conexión BD
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="C&be1987d0d4", 
        database="lexcorp"
    )

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
    cursor.execute("SELECT * FROM clientes WHERE usuario=%s AND contrasena=%s", (usuario, contrasena))
    user = cursor.fetchone()
    conn.close()

    if user:
        session["usuario"] = user["usuario"]
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
            "INSERT INTO clientes (usuario, nombre, correo, contrasena) VALUES (%s,%s,%s,%s)",
            (usuario, nombre, correo, contrasena),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    return render_template("registro.html",mensaje=mensaje)

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
        return render_template("inicio.html", usuario=session["usuario"], servicios=servicios)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


