import sys
import threading # La librería nativa para manejar tareas en segundo plano
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QObject

import descargador

class Senales(QObject):
    descarga_finalizada = pyqtSignal()

class BarraSpotlight(QWidget):
    def __init__(self):
        super().__init__()
        self.senales = Senales()
        self.senales.descarga_finalizada.connect(self.cerrar_aplicacion)
        self.configurar_ventana()

    def configurar_ventana(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(700, 80)
        self.centrar_en_pantalla()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("Pega el link (ej: url 720 --audio --inicio 1:00)...")
        
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-size: 24px;
                padding: 15px 25px;
                border-radius: 15px;
                border: 1px solid #444;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #007aff;
            }
        """)

        self.input_box.returnPressed.connect(self.procesar_input)
        layout.addWidget(self.input_box)
        self.setLayout(layout)

    def centrar_en_pantalla(self):
        geometria_ventana = self.frameGeometry()
        centro_pantalla = self.screen().availableGeometry().center()
        geometria_ventana.moveCenter(centro_pantalla)
        self.move(geometria_ventana.topLeft())

    def procesar_input(self):
        texto = self.input_box.text().strip()
        if texto:
            self.input_box.clear()
            self.hide()

            hilo_descarga = threading.Thread(target=self.analizar_y_descargar, args=(texto,))
            hilo_descarga.start()

    def analizar_y_descargar(self, comando):
        partes = comando.split()
        
        url = partes[0]
        
        resolucion = 1080
        solo_audio = False
        inicio = None
        fin = None

        if "--audio" in partes:
            solo_audio = True
            
        for parte in partes[1:]:
            if parte.isdigit(): 
                resolucion = int(parte)

        if "--inicio" in partes:
            idx = partes.index("--inicio")
            if idx + 1 < len(partes):
                inicio = partes[idx + 1]
                
        if "--fin" in partes:
            idx = partes.index("--fin")
            if idx + 1 < len(partes):
                fin = partes[idx + 1]

        print(f"\n[SpotDark] Recibido. Enviando a descargador.py...")
        
        descargador.descargar_video(url, resolucion, inicio, fin, solo_audio)

        self.senales.descarga_finalizada.emit()
    
    def cerrar_aplicacion(self):
        print("\n[SpotDark] Proceso terminado. Cerrando aplicación...")
        QApplication.quit()

    def keyPressEvent(self, evento):
        if evento.key() == Qt.Key.Key_Escape:
            self.cerrar_aplicacion()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ventana = BarraSpotlight()
    ventana.show()
    sys.exit(app.exec())