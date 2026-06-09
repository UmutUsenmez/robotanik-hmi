import sys
import os
import math
import datetime
import roslibpy
from fpdf import FPDF
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QWidget, QLabel, QGroupBox, QFrame, QGraphicsScene, 
                             QGraphicsView, QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsPolygonItem)
from PyQt5.QtGui import QPixmap, QPen, QBrush, QColor, QImage, QPainter, QPolygonF
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QPointF

try:
    from tedavi_db import get_treatment
except ImportError:
    print("Uyarı: tedavi_db.py bulunamadı.")
    def get_treatment(d, p): return "Tedavi veritabanına ulaşılamadı."

# --- HARİTA AYARLARI ---
MAP_RESOLUTION = 0.05
MAP_ORIGIN_X = 0.0
MAP_ORIGIN_Y = 0.0

# Kodun çalıştığı mevcut klasörün yolunu otomatik bulur
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Harita ve pdf için public yollar
ROS_MAP_PATH = os.path.join(CURRENT_DIR, "robotanik_sera.pgm")
VISUAL_MAP_PATH = os.path.join(CURRENT_DIR, "download.png")
REPORT_OUTPUT_PATH = os.path.join(CURRENT_DIR, "Robotanik_Saha_Raporu.pdf")
TEMP_HEATMAP_PATH = os.path.join(CURRENT_DIR, "temp_heatmap.png")

# Kümeleme yarıçapı (Metre cinsinden. 1.5 metre içindeki hastalıklar tek bölge sayılır)
CLUSTER_RADIUS = 1.5 

STYLESHEET = """
QMainWindow { background-color: #f0f2f5; }
QFrame.Card { background-color: #ffffff; border-radius: 12px; border: 1px solid #e1e4e8; }
QLabel.Title { color: #2c3e50; font-size: 16px; font-weight: bold; padding-bottom: 5px; }
QLabel.Value { color: #27ae60; font-size: 20px; font-weight: bold; }
QPushButton { border-radius: 8px; font-weight: bold; font-size: 14px; padding: 12px; color: white; }
QPushButton#btnConnect { background-color: #3498db; }
QPushButton#btnConnect:hover { background-color: #2980b9; }
QPushButton#btnStart { background-color: #2ecc71; }
QPushButton#btnStart:hover { background-color: #27ae60; }
QPushButton#btnPause { background-color: #f1c40f; color: #2c3e50; }
QPushButton#btnPause:hover { background-color: #f39c12; }
QPushButton#btnStop { background-color: #e74c3c; }
QPushButton#btnStop:hover { background-color: #c0392b; }
QPushButton#btnReport { background-color: #9b59b6; }
QPushButton#btnReport:hover { background-color: #8e44ad; }
"""

class RosSignals(QObject):
    telemetry_signal = pyqtSignal(str, int) 
    location_signal = pyqtSignal(float, float, float)

class RobotanikHMI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AgriBot - Otonom Botanik Yönetim Paneli")
        self.setGeometry(50, 50, 1250, 800)
        self.setStyleSheet(STYLESHEET)

        self.ros = roslibpy.Ros(host='localhost', port=9090)
        self.signals = RosSignals()
        self.signals.telemetry_signal.connect(self.update_diagnostics_ui)
        self.signals.location_signal.connect(self.update_location_ui)

        self.telemetry_listener = None
        self.location_listener = None
        self.command_publisher = None
        
        self.total_scanned = 0
        self.total_diseases = 0
        self.current_x = 0.0 
        self.current_y = 0.0
        self.disease_log = [] 

        self.map_height = 600 
        if os.path.exists(ROS_MAP_PATH):
            pgm = QImage(ROS_MAP_PATH)
            if not pgm.isNull():
                self.map_height = pgm.height()

        self.init_ui()

    def create_card(self):
        card = QFrame()
        card.setProperty("class", "Card")
        return card

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # ================= SOL: HARİTA =================
        map_card = self.create_card()
        map_layout = QVBoxLayout(map_card)
        map_layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("🌿 Saha Görünümü & Canlı Isı Haritası")
        title_label.setProperty("class", "Title")
        map_layout.addWidget(title_label)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setAlignment(Qt.AlignCenter)
        self.view.setStyleSheet("background-color: #eaf2e3; border: none; border-radius: 8px;") 

        if os.path.exists(VISUAL_MAP_PATH):
            visual_img = QImage(VISUAL_MAP_PATH)
            if not visual_img.isNull():
                scaled_img = visual_img.scaledToHeight(self.map_height, Qt.SmoothTransformation)
                self.map_pixmap = QPixmap.fromImage(scaled_img)
                self.scene.addPixmap(self.map_pixmap)

        self.scene.setSceneRect(self.scene.itemsBoundingRect())

        # ================= ROBOT İKONU =================
        self.robot_marker = QGraphicsRectItem(-15, -20, 30, 40)
        self.robot_marker.setPen(QPen(Qt.NoPen)) 
        
        fov_polygon = QPolygonF([QPointF(0, 0), QPointF(80, -40), QPointF(80, 40)])
        self.fov_cone = QGraphicsPolygonItem(fov_polygon, self.robot_marker)
        self.fov_cone.setBrush(QBrush(QColor(46, 204, 113, 80)))
        self.fov_cone.setPen(QPen(Qt.NoPen))
        
        self.robot_body = QGraphicsRectItem(-12, -15, 24, 30, self.robot_marker)
        self.robot_body.setBrush(QBrush(QColor("#ffffff")))
        self.robot_body.setPen(QPen(QColor("#2c3e50"), 2))
        
        wheel_color = QBrush(QColor("#34495e"))
        self.wheel1 = QGraphicsRectItem(-16, -12, 4, 8, self.robot_marker); self.wheel1.setBrush(wheel_color)
        self.wheel2 = QGraphicsRectItem(-16, 4, 4, 8, self.robot_marker); self.wheel2.setBrush(wheel_color)
        self.wheel3 = QGraphicsRectItem(12, -12, 4, 8, self.robot_marker); self.wheel3.setBrush(wheel_color)
        self.wheel4 = QGraphicsRectItem(12, 4, 4, 8, self.robot_marker); self.wheel4.setBrush(wheel_color)
        
        self.sensor = QGraphicsEllipseItem(4, -5, 10, 10, self.robot_marker)
        self.sensor.setBrush(QBrush(QColor("#2c3e50")))

        self.robot_marker.setZValue(10)
        self.scene.addItem(self.robot_marker)
        self.robot_marker.setVisible(False)

        map_layout.addWidget(self.view)
        main_layout.addWidget(map_card, stretch=5)

        # ================= SAĞ: KONTROLLER =================
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

        diag_card = self.create_card()
        diag_layout = QVBoxLayout(diag_card)
        diag_title = QLabel("⚙️ Sistem Teşhisi")
        diag_title.setProperty("class", "Title")
        diag_layout.addWidget(diag_title)

        self.lbl_conn = QLabel("Ağ Durumu: Bekleniyor")
        self.lbl_battery = QLabel("Batarya: %85 (Stabil)")
        self.lbl_conn.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        self.lbl_battery.setStyleSheet("color: #27ae60; font-size: 14px; font-weight: bold;")
        
        self.btn_connect = QPushButton("Bağlantıyı Kur")
        self.btn_connect.setObjectName("btnConnect")
        self.btn_connect.clicked.connect(self.toggle_connection)

        diag_layout.addWidget(self.lbl_conn)
        diag_layout.addWidget(self.lbl_battery)
        diag_layout.addWidget(self.btn_connect)
        right_panel.addWidget(diag_card)

        stats_card = self.create_card()
        stats_layout = QVBoxLayout(stats_card)
        stats_title = QLabel("📊 Anlık YOLO Verisi")
        stats_title.setProperty("class", "Title")
        
        self.lbl_scanned = QLabel("Taranan Bitki: 0")
        self.lbl_diseases = QLabel("Bulunan Hastalık: 0")
        self.lbl_scanned.setProperty("class", "Value")
        self.lbl_diseases.setStyleSheet("color: #e74c3c; font-size: 20px; font-weight: bold;")
        
        self.lbl_last_detect = QLabel("Son Teşhis: Bekleniyor...")
        self.lbl_last_detect.setStyleSheet("color: #34495e; font-size: 13px; margin-top: 10px;")

        stats_layout.addWidget(stats_title)
        stats_layout.addWidget(self.lbl_scanned)
        stats_layout.addWidget(self.lbl_diseases)
        stats_layout.addWidget(self.lbl_last_detect)
        right_panel.addWidget(stats_card)

        ctrl_card = self.create_card()
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_title = QLabel("🕹️ Operatör Paneli")
        ctrl_title.setProperty("class", "Title")
        ctrl_layout.addWidget(ctrl_title)

        self.btn_start = QPushButton("▶ Görevi Başlat")
        self.btn_start.setObjectName("btnStart")
        self.btn_start.clicked.connect(lambda: self.send_cmd('start'))

        self.btn_pause = QPushButton("⏸ Duraklat")
        self.btn_pause.setObjectName("btnPause")
        self.btn_pause.clicked.connect(lambda: self.send_cmd('pause'))

        self.btn_stop = QPushButton("🛑 Acil Durdur")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.clicked.connect(lambda: self.send_cmd('stop'))

        self.btn_report = QPushButton("📄 Tedavi Raporu Oluştur")
        self.btn_report.setObjectName("btnReport")
        self.btn_report.clicked.connect(self.generate_report)

        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_pause)
        ctrl_layout.addWidget(self.btn_stop)
        ctrl_layout.addWidget(self.btn_report)
        right_panel.addWidget(ctrl_card)

        main_layout.addLayout(right_panel, stretch=2)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def showEvent(self, event):
        super().showEvent(event)
        self.fit_map()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_map()
        
    def fit_map(self):
        if hasattr(self, 'scene') and self.scene.sceneRect().width() > 0:
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def toggle_connection(self):
        if not self.ros.is_connected:
            try:
                self.ros.run()
                if self.ros.is_connected:
                    self.lbl_conn.setText("Ağ Durumu: BAĞLI (Wi-Fi)")
                    self.lbl_conn.setStyleSheet("color: #27ae60; font-size: 14px; font-weight:bold;")
                    self.btn_connect.setText("Bağlantıyı Kes")
                    self.btn_connect.setStyleSheet("background-color: #7f8c8d;")
                    self.robot_marker.setVisible(True)
                    self.start_listening()
            except Exception as e:
                self.lbl_conn.setText("Bağlantı Hatası!")
        else:
            self.stop_listening()
            self.ros.terminate()
            self.lbl_conn.setText("Ağ Durumu: KESİLDİ")
            self.lbl_conn.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight:bold;")
            self.btn_connect.setText("Bağlantıyı Kur")
            self.btn_connect.setStyleSheet("")
            self.robot_marker.setVisible(False)

    def start_listening(self):
        self.telemetry_listener = roslibpy.Topic(self.ros, '/telemetry/disease_stats', 'std_msgs/msg/String')
        self.telemetry_listener.subscribe(self.telemetry_callback)

        self.location_listener = roslibpy.Topic(self.ros, '/robot/pose_sim', 'geometry_msgs/msg/Pose')
        self.location_listener.subscribe(self.location_callback)

        self.command_publisher = roslibpy.Topic(self.ros, '/robot/command', 'std_msgs/msg/String')

    def stop_listening(self):
        if self.telemetry_listener: self.telemetry_listener.unsubscribe()
        if self.location_listener: self.location_listener.unsubscribe()
        if self.command_publisher: self.command_publisher.unadvertise()

    def send_cmd(self, cmd_str):
        if self.ros.is_connected:
            self.command_publisher.publish(roslibpy.Message({'data': cmd_str}))

    def safe_text(self, text):
        chars = {'ı':'i', 'ğ':'g', 'ü':'u', 'ş':'s', 'ö':'o', 'ç':'c', 'İ':'I', 'Ğ':'G', 'Ü':'U', 'Ş':'S', 'Ö':'O', 'Ç':'C'}
        for tr, eng in chars.items():
            text = text.replace(tr, eng)
        return text

    def generate_report(self):
        self.lbl_last_detect.setText("Durum: PDF Raporu ve Harita Hazırlanıyor...")
        QApplication.processEvents() 
        
        try:
            rect = self.scene.sceneRect()
            image = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32)
            image.fill(Qt.transparent)
            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)
            self.scene.render(painter)
            painter.end()
            image.save(TEMP_HEATMAP_PATH)

            pdf = FPDF()
            pdf.add_page()
            
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt=self.safe_text("ROBOTANIK - ISI HARITASI VE GENEL DURUM"), ln=True, align='C')
            pdf.ln(5)
            
            pdf.set_font("Arial", '', 12)
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pdf.cell(200, 8, txt=self.safe_text(f"Rapor Tarihi: {current_time}"), ln=True)
            pdf.cell(200, 8, txt=self.safe_text(f"Toplam Taranan Bitki: {self.total_scanned}"), ln=True)
            pdf.cell(200, 8, txt=self.safe_text(f"Toplam Hastalikli Bitki: {self.total_diseases}"), ln=True)
            pdf.ln(5)
            
            pdf.image(TEMP_HEATMAP_PATH, x=20, y=pdf.get_y(), w=170)
            
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt=self.safe_text("DETAYLI TEHLIKE ANALIZI VE LOKASYON BAZLI TEDAVI"), ln=True, align='C')
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
            if self.total_diseases == 0:
                pdf.set_font("Arial", '', 12)
                pdf.cell(200, 10, txt=self.safe_text("Tebrikler! Sahada herhangi bir hastalik tespit edilmedi."), ln=True)
            else:
                grouped_diseases = {}
                for entry in self.disease_log:
                    name = entry['name']
                    tier = entry['tier']
                    if name not in grouped_diseases:
                        grouped_diseases[name] = {}
                    if tier not in grouped_diseases[name]:
                        grouped_diseases[name][tier] = []
                    grouped_diseases[name][tier].append(entry)

                for disease, tiers in grouped_diseases.items():
                    pdf.set_font("Arial", 'B', 14)
                    pdf.set_text_color(192, 57, 43) 
                    pdf.cell(200, 10, txt=self.safe_text(f"> Hastalik Türü: {disease}"), ln=True)
                    pdf.set_text_color(0, 0, 0)
                    
                    for tier, clusters in sorted(tiers.items()):
                        max_danger_in_tier = max(c['danger'] for c in clusters)
                        total_plants_in_tier = sum(c['count'] for c in clusters)
                        
                        pdf.set_font("Arial", 'B', 11)
                        pdf.cell(200, 6, txt=self.safe_text(f"  - Risk Seviyesi: {tier} (Maksimum Tespit: %{max_danger_in_tier} | Etkilenen Bitki: {total_plants_in_tier})"), ln=True)
                        
                        oneri = get_treatment(disease, max_danger_in_tier)
                        pdf.set_font("Arial", '', 10)
                        pdf.multi_cell(0, 6, txt=self.safe_text(f"    {oneri}"))
                        
                        pdf.set_font("Arial", 'I', 9)
                        pdf.set_text_color(41, 128, 185) 
                        
                        # --- KÜMELERİ YAZDIRMA ---
                        loc_strings = [f"(X: {c['x']:.1f}, Y: {c['y']:.1f} -> {c['count']} bitki)" for c in clusters]
                        loc_text = "    Enfeksiyon Merkezleri [Metre]: " + " | ".join(loc_strings)
                        pdf.multi_cell(0, 5, txt=self.safe_text(loc_text))
                        pdf.set_text_color(0, 0, 0)
                        pdf.ln(3)
                    pdf.ln(2)

            pdf.output(REPORT_OUTPUT_PATH)
            self.lbl_last_detect.setText(self.safe_text(f"PDF Basarili! Konum: {REPORT_OUTPUT_PATH}"))
            
        except Exception as e:
            self.lbl_last_detect.setText(f"Rapor Hatasi: {str(e)}")

    def telemetry_callback(self, message):
        data = message['data']
        try:
            parts = data.split(" | ")
            durum = parts[0].split(": ")[1]
            tehlike_str = parts[1].split(": %")[1]
            self.signals.telemetry_signal.emit(durum, int(tehlike_str))
        except:
            pass

    def location_callback(self, message):
        pos = message['position']
        ori = message['orientation']
        self.current_x = pos['x']
        self.current_y = pos['y']
        
        yaw = 2.0 * math.atan2(ori['z'], ori['w']) * (180.0 / math.pi)
        self.signals.location_signal.emit(pos['x'], pos['y'], yaw)

    def update_diagnostics_ui(self, durum, tehlike):
        self.total_scanned += 1
        self.lbl_scanned.setText(f"Taranan Bitki: {self.total_scanned}")
        
        if durum != "Saglikli":
            self.total_diseases += 1
            self.lbl_diseases.setText(f"Bulunan Hastalık: {self.total_diseases}")
            self.lbl_last_detect.setText(f"Son Teşhis: {durum} (Tehlike: %{tehlike})")
            
            tier = "Dusuk Risk (T1)" if tehlike < 50 else ("Orta Risk (T2)" if tehlike < 75 else "Yuksek Risk (T3)")
            
            # --- MEKANSAL KÜMELEME (CLUSTERING) KONTROLÜ ---
            is_clustered = False
            for entry in self.disease_log:
                if entry['name'] == durum and entry['tier'] == tier:
                    # Euclidean Distance
                    dist = math.sqrt((self.current_x - entry['x'])**2 + (self.current_y - entry['y'])**2)
                    if dist <= CLUSTER_RADIUS:
                        entry['count'] += 1
                        if tehlike > entry['danger']:
                            entry['danger'] = tehlike
                        is_clustered = True
                        break

            # Eğer mevcut bir kümeye girmediyse, yeni bir enfeksiyon merkezi olarak ekle
            if not is_clustered:
                self.disease_log.append({
                    'name': durum,
                    'tier': tier,
                    'danger': tehlike,
                    'x': self.current_x,
                    'y': self.current_y,
                    'count': 1
                })
            
            dot_color = QColor("#e74c3c") if tehlike > 70 else QColor("#f1c40f")
            rx, ry = self.robot_marker.x(), self.robot_marker.y()
            dot = QGraphicsEllipseItem(-6, -6, 12, 12)
            dot.setPos(rx, ry)
            dot.setBrush(QBrush(dot_color))
            dot.setPen(QPen(Qt.NoPen))
            dot.setZValue(5) 
            self.scene.addItem(dot)
        else:
            self.lbl_last_detect.setText("Son Teşhis: Temiz (Sağlıklı Bitki)")

    def update_location_ui(self, x, y, yaw):
        pixel_x = (x - MAP_ORIGIN_X) / MAP_RESOLUTION
        pixel_y = self.map_height - ((y - MAP_ORIGIN_Y) / MAP_RESOLUTION)
        self.robot_marker.setPos(pixel_x, pixel_y)
        self.robot_marker.setRotation(-yaw)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RobotanikHMI()
    window.show()
    sys.exit(app.exec_())