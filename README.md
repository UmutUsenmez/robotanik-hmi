cat << 'EOF' > README.md
# 🌿 Robotanik HMI - Otonom Botanik Yönetim Paneli 🚜

Bu depo, otonom tarım ve bitki hastalığı tespit robotu olan **Robotanik (AgriBot)** projesinin yer istasyonu ve operatör kontrol arayüzünü (HMI) içerir.
Sistem, ROS2 üzerinden robotla haberleşerek anlık saha verilerini görselleştirir, hastalıkları kümelendirir ve otonom tedavi raporları üretir.

## 📌 Temel Özellikler
* **Canlı Isı Haritası & Otonom Takip:** Robotun tarladaki konumu (X, Y, Yaw) ve sensör yönelimi ROS2 üzerinden anlık olarak arayüze yansıtılır.
* **Mekansal Kümeleme (Spatial Clustering):** Tarlada tespit edilen hastalıklar (YOLO verileri), veri gürültüsünü önlemek amacıyla 1.5 metrelik yarıçaplar halinde algoritmik olarak kümelenerek *Enfeksiyon Merkezlerine* dönüştürülür.
* **Modüler Tedavi Veritabanı:** `tedavi_db.py` modülü sayesinde tespit edilen hastalığın tehlike riskine göre (T1, T2, T3) otonom organik/kimyasal tedavi reçeteleri belirlenir.
* **Tek Tıkla PDF Raporlama:** Operatör komutuyla tarlanın yüksek çözünürlüklü ısı haritası ve nokta atışı koordinatlı (Örn: X: 2.1, Y: 4.5) tedavi reçeteleri anında `.pdf` formatında dışa aktarılır.

## 🛠️ Proje Mimarisi
* `hmi_main.py`: PyQt5 tabanlı ana operatör kontrol paneli ve PDF motoru. Tamamen gevşek bağlı (loosely coupled) WebSocket mimarisi.
* `dummy_robot.py`: Donanım olmadan arayüz testleri yapabilmek için tasarlanmış gerçekçi ROS2 otonom sürüş ve hastalık simülatörü.
* `tedavi_db.py`: Hastalık türleri ve risk seviyelerine göre ayrıştırılmış tedavi veri tabanı.
* `robotanik_sera.pgm`: Matematiksel konum hesaplamaları için referans harita.
* `download.png`: HMI üzerinde gösterilen modern tarla görseli.

## ⚙️ Kurulum & Entegrasyon
Arayüzün çalışacağı bilgisayarda ROS2 kurulu olmasına gerek yoktur. Gerekli kütüphaneleri kurmak için:

`pip3 install PyQt5 roslibpy fpdf`

*(Not: Ağ bağlantısı için `hmi_main.py` içindeki `localhost` adresi, robotu kontrol eden bilgisayarın yerel IP adresi ile değiştirilmelidir).*

## 🚀 Sistemi Çalıştırma
1. **ROSBridge Sunucusu (Robot PC):** `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`
2. **Otonom Sistem (Robot PC):** `python3 dummy_robot.py`
3. **HMI Paneli (Arayüz PC):** `python3 hmi_main.py`

---
*Geliştiriciler: Umut Üşenmez

git add README.md
git commit -m "docs: Proje mimarisi, özellikler ve kurulum adımlarını içeren endüstriyel kalitede README eklendi"
git push
