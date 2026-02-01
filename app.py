from flask import Flask, request, render_template_string, redirect
import logging
import requests
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('ngl_hacker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Mesajları tut (restart olunca sıfırlanır)
messages = []

HOME_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>itiraf_ipal</title>
    <style>
        body { background: linear-gradient(135deg, #000000, #1a0033); color: white; font-family: 'Helvetica Neue', Arial, sans-serif; text-align: center; margin: 0; padding: 20px; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; }
        h1 { font-size: 4rem; font-weight: 800; margin-bottom: 20px; background: linear-gradient(90deg, #ff00cc, #3333ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        input[type="text"], textarea { width: 80%; max-width: 500px; padding: 15px; font-size: 1.2rem; border: none; border-radius: 16px; background: rgba(255,255,255,0.1); color: white; margin-bottom: 20px; }
        input[type="text"]::placeholder, textarea::placeholder { color: rgba(255,255,255,0.6); }
        textarea { height: 120px; resize: none; }
        button { padding: 16px 50px; background: linear-gradient(90deg, #ff00cc, #3333ff); color: white; border: none; border-radius: 50px; font-size: 1.3rem; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { transform: scale(1.05); }
        .info, .footer { margin-top: 30px; font-size: 0.9rem; opacity: 0.7; color: #ccc; }
        .success { font-size: 2rem; margin-top: 50px; animation: fadeIn 1s; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    {% if success %}
        <div class="success">Mesajın gönderildi!✅</div>
        <p>gizlilik esastır.</p>
    {% else %}
        <h1>@{{ username if username else 'itiraf_ipal' }}</h1>
        <p>Anonim mesaj gönder</p>
        <form method="POST">
            <input type="text" name="username" placeholder="Kullanıcı adın (isteğe bağlı)" value="{{ username }}" autocomplete="off"><br>
            <textarea name="message" placeholder="Buraya yaz..." required></textarea><br>
            <button type="submit">Gönder</button>
        </form>
        <div class="info">http://instagram.com/itiraf_ipal</div>
        <div class="footer">Bu site itiraf_ipal tarafından yapılmıştır tüm hakları saklıdır©</div>
    {% endif %}
</body>
</html>
"""

MESAJLAR_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>itiraf_ipal - Mesajlar</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        body {
            background: linear-gradient(135deg, #0f001a, #1a0033, #2a004d, #4b0082);
            color: white;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 0;
            min-height: 100vh;
        }
        h1 {
            text-align: center;
            font-size: 2.5rem;
            margin: 40px 0 30px;
            background: linear-gradient(90deg, #ff00cc, #00ffff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .story-preview {
            width: 90%;
            max-width: 400px;
            min-height: 800px;
            margin: 20px auto;
            background: linear-gradient(135deg, #ff00cc, #8a2be2, #4b0082);
            border-radius: 12px;
            box-shadow: 0 15px 50px rgba(255, 0, 204, 0.4);
            color: white;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            padding: 100px 30px 60px;
        }
        .story-preview::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.18) 0%, transparent 60%);
            opacity: 0.5;
            pointer-events: none;
        }
        .inner-box {
            background: rgba(0, 0, 0, 0.45);
            border-radius: 16px;
            width: 90%;
            aspect-ratio: 16 / 9;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 30px;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
            margin-bottom: 40px;
        }
        .username {
            font-size: 1.9rem; /* küçültüldü */
            font-weight: bold;
            margin-bottom: 10px; /* üste kaydırıldı */
            text-shadow: 0 2px 10px rgba(0,0,0,0.6);
            text-align: center;
        }
        .message {
            font-size: 1.8rem;
            line-height: 1.6;
            text-align: center;
        }
        .footer {
            font-size: 1.1rem;
            opacity: 0.9;
            text-align: center;
            margin-top: auto;
            padding-top: 30px;
        }
        .admin-footer {
            font-size: 0.9rem;
            opacity: 0.6;
            text-align: center;
            margin-top: 60px;
            color: #ddd;
        }
        .download-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid white;
            padding: 14px 40px;
            border-radius: 50px;
            cursor: pointer;
            font-weight: bold;
            margin: 30px auto;
            font-size: 1.1rem;
            backdrop-filter: blur(5px);
            transition: all 0.3s;
        }
        .download-btn:hover {
            background: white;
            color: #ff00cc;
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Gelen Mesajlar</h1>
        {% if messages %}
            {% for msg in messages %}
                <div class="story-preview" id="msg-box-{{ loop.index }}">
                    <div class="inner-box">
                        <div class="username">@{{ msg.username or 'Anonim' }}</div>
                        <div class="message">{{ msg.message }}</div>
                    </div>
                    <div class="footer">@itiraf_ipal</div>
                    <div class="admin-footer">@ipal_itiraf</div>
                    <button class="download-btn" onclick="downloadBox('msg-box-{{ loop.index }}')">Story'ye Kaydet (İndir)</button>
                </div>
            {% endfor %}
        {% else %}
            <p>Henüz mesaj yok.</p>
        {% endif %}
    </div>

    <script>
        function downloadBox(boxId) {
            const box = document.getElementById(boxId);
            const buttons = box.getElementsByTagName('button');
            for (let btn of buttons) {
                btn.style.display = 'none';
            }

            html2canvas(box, {
                scale: 4,
                backgroundColor: null, // şeffaf arka plan (siyah/beyaz kenar yok)
                useCORS: true,
                logging: false,
                windowWidth: box.scrollWidth,
                windowHeight: box.scrollHeight
            }).then(canvas => {
                const link = document.createElement('a');
                link.download = 'ngl_story_mesaj.png';
                link.href = canvas.toDataURL('image/png');
                link.click();

                for (let btn of buttons) {
                    btn.style.display = 'block';
                }
            }).catch(err => {
                alert("Resim oluşturulamadı: " + err + " (Uzun bas kaydetmeyi dene)");
                for (let btn of buttons) {
                    btn.style.display = 'block';
                }
            });
        }
    </script>
</body>
</html>
"""

LOGS_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>itiraf_ipal - Loglar</title>
    <style>
        body {
            background: linear-gradient(135deg, #000000, #1a0033);
            color: white;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        h1 {
            text-align: center;
            font-size: 2.5rem;
            margin: 40px 0 30px;
            background: linear-gradient(90deg, #ff00cc, #00ffff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .log-entry {
            background: rgba(0,0,0,0.4);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        .log-title {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 10px;
            color: #ff00cc;
        }
        .log-detail {
            font-size: 1rem;
            margin-bottom: 5px;
        }
    </style>
</head>
<body>
    <h1>Log Detayları</h1>
    {% if messages %}
        {% for msg in messages %}
            <div class="log-entry">
                <div class="log-title">@{{ msg.username or 'Anonim' }} - {{ msg.timestamp }}</div>
                <div class="log-detail"><strong>Mesaj:</strong> {{ msg.message }}</div>
                <div class="log-detail"><strong>IP:</strong> {{ msg.ip or 'Bilinmiyor' }}</div>
                <div class="log-detail"><strong>Konum:</strong> {{ msg.location or 'Bilinmiyor' }}</div>
                <div class="log-detail"><strong>ISP:</strong> {{ msg.isp or 'Bilinmiyor' }}</div>
                <div class="log-detail"><strong>Cihaz:</strong> {{ msg.user_agent[:100] or 'Bilinmiyor' }}...</div>
            </div>
        {% endfor %}
    {% else %}
        <p>Henüz log yok.</p>
    {% endif %}
</body>
</html>
"""

messages = []

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

            messages.append({
                "username": username or 'Anonim',
                "message": msg,
                "ip": client_ip,
                "location": location,
                "isp": isp,
                "user_agent": user_agent,
                "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            })

            return render_template_string(HOME_HTML, username=username, success=True)

    return render_template_string(HOME_HTML, username=username, success=False)

@app.route('/mesajlar')
def mesajlar():
    return render_template_string(MESAJLAR_HTML, messages=messages)

@app.route('/logs')
def logs():
    return render_template_string(LOGS_HTML, messages=messages)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
