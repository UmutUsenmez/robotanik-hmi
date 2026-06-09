import time
import random
import math
import roslibpy

ros = roslibpy.Ros(host='localhost', port=9090)
ros.run()

telemetry_topic = roslibpy.Topic(ros, '/telemetry/disease_stats', 'std_msgs/msg/String')
location_topic = roslibpy.Topic(ros, '/robot/pose_sim', 'geometry_msgs/msg/Pose')

is_running = False

def command_callback(msg):
    global is_running
    cmd = msg['data']
    if cmd == 'start':
        print("\n[KOMUT ALINDI]: Görev başlatılıyor...")
        is_running = True
    elif cmd == 'stop':
        print("\n[KOMUT ALINDI]: ACİL DURDURMA!")
        is_running = False

command_listener = roslibpy.Topic(ros, '/robot/command', 'std_msgs/msg/String')
command_listener.subscribe(command_callback)

print("Gerçekçi Dummy Robot beklemede. Arayüzden 'Başlat' komutu bekleniyor...")

# Yeni veritabanına uygun tüm hastalıklar
HASTALIK_LISTESI = [
    "Late Blight", "Spider Mites", "Mosaic Virus", 
    "Leaf Miner", "Bacterial Spot", "Early Blight", 
    "Septoria", "Leaf Mold", "Yellow Leaf Curl Virus"
]

try:
    x_pos, y_pos = 2.0, 0.0
    
    # Gerçekçi Enfeksiyon Kümesi (Outbreak Clustering) Değişkenleri
    aktif_enfeksiyon = None
    kalan_hastalikli_bitki = 0
    
    while ros.is_connected:
        if is_running:
            yaw_angle = 90.0 
            yaw_rad = math.radians(yaw_angle)
            
            speed = 0.2
            y_pos += speed
            
            qz = math.sin(yaw_rad / 2.0)
            qw = math.cos(yaw_rad / 2.0)

            pose_msg = {
                'position': {'x': x_pos, 'y': y_pos, 'z': 0.0},
                'orientation': {'x': 0.0, 'y': 0.0, 'z': qz, 'w': qw}
            }
            location_topic.publish(roslibpy.Message(pose_msg))

            # --- GERÇEKÇİ HASTALIK SİMÜLASYONU ---
            if kalan_hastalikli_bitki > 0:
                # Mevcut bir enfeksiyon bölgesinin içinden geçiyoruz
                durum = aktif_enfeksiyon
                # Aynı bölgedeki bitkilerin tehlike yüzdesi birbirine yakın olur
                tehlike = random.randint(65, 95) 
                kalan_hastalikli_bitki -= 1
            else:
                # Sağlıklı bölgedeyiz. Sadece %10 ihtimalle yeni bir salgın bölgesi başlar
                if random.random() < 0.10:
                    aktif_enfeksiyon = random.choice(HASTALIK_LISTESI)
                    durum = aktif_enfeksiyon
                    tehlike = random.randint(40, 95)
                    # Hastalık bulunduysa, yan yana 3 ile 8 bitkide daha aynı hastalık görülsün
                    kalan_hastalikli_bitki = random.randint(3, 8)
                else:
                    durum = "Saglikli"
                    tehlike = 0
                    aktif_enfeksiyon = None

            # Oneri metni artık arayüzde tedavi_db'den çekildiği için burada placeholder gönderiyoruz
            oneri = "Sistem tarafindan PDF'te hesaplanacak" 
            telemetry_msg = {'data': f"Durum: {durum} | Tehlike: %{tehlike} | Oneri: {oneri}"}
            telemetry_topic.publish(roslibpy.Message(telemetry_msg))

            if durum != "Saglikli":
                print(f"Hareket ediliyor... Konum: ({x_pos:.2f}, {y_pos:.2f}) | ⚠️ Tespit: {durum}")
            else:
                print(f"Hareket ediliyor... Konum: ({x_pos:.2f}, {y_pos:.2f}) | ✅ Temiz")
        
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\nSimülasyon kapatıldı.")
finally:
    telemetry_topic.unadvertise()
    location_topic.unadvertise()
    command_listener.unsubscribe()
    ros.terminate()