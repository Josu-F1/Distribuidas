import os
import threading
import resend
from flask import Flask, jsonify, request
from mssql_python import connect

app = Flask(__name__)

# --- CONFIGURACIÓN DE RESEND ---
resend.api_key = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = os.environ.get("MAIL_RESEND", "onboarding@resend.dev")

# --- CONFIGURACIÓN DE BASE DE DATOS ---
def get_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    port = os.getenv("DB_PORT", "1433")

    if not all([server, database, username, password]):
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

# --- FUNCIONES DE APOYO ---
def enviar_correo_resend(destino, asunto, mensaje):
    try:
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [destino],
            "subject": asunto,
            "html": f"<p>{mensaje}</p>"
        })
        print(f"Correo enviado exitosamente a {destino}")
    except Exception as e:
        print(f"Error enviando correo: {str(e)}")

# --- RUTAS ---

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "API Flask funcionando correctamente"
    })

@app.route("/test-db")
def test_db():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE()")
        row = cursor.fetchone()
        return jsonify({"success": True, "server_date": str(row[0])})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
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
        data = [{"id": r[0], "nombre": r[1], "precio": float(r[2]) if r[2] else 0, "stock": r[3], "url_imagen": r[4]} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- NUEVO ENDPOINT ASÍNCRONO ---
@app.route("/enviar-alerta-resend", methods=["POST"])
def enviar_alerta_resend():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibió JSON"}), 400

    correo = data.get("email")
    asunto = data.get("subject", "Notificación")
    mensaje = data.get("message", "Mensaje desde Render")

    if not correo:
        return jsonify({"error": "Falta el email"}), 400

    try:
        # Ejecuta el envío en un hilo separado para no bloquear la respuesta
        threading.Thread(target=enviar_correo_resend, args=(correo, asunto, mensaje)).start()

        return jsonify({
            "status": "ok",
            "msg": "Correo enviado (async)"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "msg": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)