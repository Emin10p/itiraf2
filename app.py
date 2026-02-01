from flask import Flask, request, render_template_string, redirect
import logging
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, db

# ================= HTML =================

HOME_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>NGL - Anonim</title>
</head>
<body>
<h1>NGL Anonim</h1>
<form method="GET" action="/">
    <input type="text" name="username" placeholder="Kullanıcı adı">
    <button type="submit">Devam Et</button>
</form>
</body>
</html>
"""

NGL_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>NGL</title>
</head>
<body>
{% if success %}
    <h2>✅ Mesaj gönderildi</h2>
{% else %}
    <h1>@{{ username }}</h1>
    <form method="POST">
        <textarea name="message" required></textarea><br>
        <button type="submit">Gönder</button>
    </form>
{% endif %}
</body>
</html>
"""

# ================= Logging =================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ================= Firebase (DOSYA YÖNTEMİ) =================

firebase_ready = False

try:
    cred = credentials.Certificate("serviceAccountKey.json")

    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://itiraf-a5d24-default-rtdb.firebaseio.com/"
    })

    firebase_ready = True
    logging.info("Firebase başarıyla başlatıldı (dosyadan)")

except Exception as e:
    logging.error("Firebase başlatılamadı", exc_info=True)

# ================= Flask =================

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    username = request.args.get("username", "").strip()
    if username:
        return redirect(f"/{username}")
    return render_template_string(HOME_HTML)

@app.route("/<username>", methods=["GET", "POST"])
def ngl_page(username):
    success = False

    # IP tespiti
    if "CF-Connecting-IP" in request.headers:
        client_ip = request.headers["CF-Connecting-IP"]
    elif "X-Forwarded-For" in request.headers:
        client_ip = request.headers["X-Forwarded-For"].split(",")[0]
    elif "X-Real-IP" in request.headers:
        client_ip = request.headers["X-Real-IP"]
    else:
        client_ip = request.remote_addr

    if request.method == "POST":
        if not firebase_ready:
            return "Firebase bağlı değil", 500

        message = request.form.get("message", "").strip()
        if message:
            ref = db.reference(f"messages/{username}")
            ref.push({
                "message": message,
                "ip": client_ip,
                "time": datetime.utcnow().isoformat()
            })
            logging.info(f"{username} | IP: {client_ip}")
            success = True

    return render_template_string(
        NGL_HTML,
        username=username,
        success=success
    )

if __name__ == "__main__":
    app.run(debug=True)
