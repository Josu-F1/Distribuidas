import os
from flask import Flask, jsonify, request
from mssql_python import connect

app = Flask(__name__)

# --- Configuración de Conexión ---
def get_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    port = os.getenv("DB_PORT", "1433")

    if not server or not database or not username or not password:
        raise ValueError("Faltan variables de entorno para la base de datos")

    connection_string = (
        f"Server=tcp:{server},{port};"
        f"Database={database};"
        f"Uid={username};"
        f"Pwd={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Authentication=SqlPassword;"
    )
    return connect(connection_string)

# --- Lógica de envío de alertas ---
def enviar_correo_alerta(asunto, mensaje, destino):
    # AQUÍ DEBES PONER TU LÓGICA DE ENVÍO DE CORREO
    # Por ejemplo: smtplib, SendGrid, Mailgun, etc.
    print(f"Simulando envío a {destino}: {asunto}")
    return True

# --- Rutas ---

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "API Flask funcionando correctamente en Render"
    })

@app.route("/debug-env")
def debug_env():
    return jsonify({
        "DB_SERVER": os.getenv("DB_SERVER"),
        "DB_DATABASE": os.getenv("DB_DATABASE"),
        "DB_USERNAME": os.getenv("DB_USERNAME"),
        "DB_PASSWORD_EXISTS": bool(os.getenv("DB_PASSWORD")),
        "DB_PORT": os.getenv("DB_PORT"),
    })

@app.route("/test-db")
def test_db():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE() AS fecha_servidor")
        row = cursor.fetchone()
        return jsonify({
            "success": True,
            "message": "Conexión a SQL Server exitosa",
            "server_date": str(row[0])
        })
    except Exception as e:
        return jsonify({"success": False, "message": "Error al conectar", "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route("/productos")
def listar_productos():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, precio, stock, url_imagen FROM productos ORDER BY id DESC")
        rows = cursor.fetchall()
        data = [{"id": r[0], "nombre": r[1], "precio": float(r[2]) if r[2] else None, "stock": r[3], "url_imagen": r[4]} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": "Error al consultar", "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route("/enviar-alerta", methods=["POST"])
def enviar_alerta():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No se recibió JSON"}), 400
        
        destino = data.get("to")
        asunto = data.get("subject")
        mensaje = data.get("message")

        if not destino or not asunto or not mensaje:
            return jsonify({"success": False, "message": "Faltan datos (to, subject, message)"}), 400

        enviar_correo_alerta(asunto, mensaje, destino)
        return jsonify({"success": True, "message": "Correo enviado correctamente"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)