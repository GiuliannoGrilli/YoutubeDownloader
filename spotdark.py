import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLineEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QGraphicsDropShadowEffect, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QFont

import descargador

# Resoluciones siempre visibles como botones fijos
RESOLUCIONES_FIJAS = [720, 1080]
# Resoluciones en el menú desplegable "Más"
RESOLUCIONES_EXTRA = [480, 1440, 2160]

ESTILO_MENU = """
    QMenu {
        background-color: #2c2c2e;
        color: white;
        border: 1px solid #3a3a3c;
        border-radius: 8px;
        padding: 4px 0px;
    }
    QMenu::item {
        padding: 6px 20px;
        font-size: 13px;
    }
    QMenu::item:selected {
        background-color: #007aff;
        border-radius: 4px;
    }
"""

class Senales(QObject):
    descarga_finalizada = pyqtSignal()

class CustomButton(QPushButton):
    def __init__(self, text, is_toggle=True):
        super().__init__(text)
        self.setCheckable(is_toggle)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2e;
                color: #ffffff;
                border: 1px solid #3a3a3c;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3a3a3c;
                border: 1px solid #48484a;
            }
            QPushButton:checked {
                background-color: #007aff;
                color: white;
                border: 1px solid #0a84ff;
            }
            QPushButton:pressed {
                background-color: #1c1c1e;
            }
            QPushButton:disabled {
                color: #555558;
                border-color: #2c2c2e;
            }
        """)

class BarraSpotlight(QWidget):
    def __init__(self):
        super().__init__()
        self.senales = Senales()
        self.senales.descarga_finalizada.connect(self.finalizar_proceso)

        self.resolucion_actual = 1080
        self.solo_audio = False

        self.configurar_ventana()
        self.crear_interfaz()

    def configurar_ventana(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(700, 160)
        self.centrar_en_pantalla()

    def centrar_en_pantalla(self):
        geo = self.frameGeometry()
        geo.moveCenter(self.screen().availableGeometry().center())
        self.move(geo.topLeft())

    def crear_interfaz(self):
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setGeometry(10, 10, 680, 140)
        self.main_frame.setStyleSheet("""
            QFrame#MainFrame {
                background-color: rgba(30, 30, 30, 240);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
            }
        """)

        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(20)
        sombra.setColor(QColor(0, 0, 0, 180))
        sombra.setOffset(0, 5)
        self.main_frame.setGraphicsEffect(sombra)

        layout_principal = QVBoxLayout(self.main_frame)
        layout_principal.setContentsMargins(20, 15, 20, 15)
        layout_principal.setSpacing(12)

        # --- Input URL ---
        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("Pega el link de YouTube aquí...")
        self.input_url.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                color: #ffffff;
                font-size: 20px;
                border: none;
                padding: 5px 0px;
                selection-background-color: #007aff;
            }
        """)
        self.input_url.returnPressed.connect(self.procesar_descarga)
        layout_principal.addWidget(self.input_url)

        # Separador
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setStyleSheet("background-color: rgba(255,255,255,0.1); max-height:1px; border:none;")
        layout_principal.addWidget(linea)

        # --- Fila de opciones ---
        layout_opciones = QHBoxLayout()
        layout_opciones.setSpacing(8)

        label_calidad = QLabel("CALIDAD:")
        label_calidad.setStyleSheet("color: #8e8e93; font-size: 11px; font-weight: bold;")
        layout_opciones.addWidget(label_calidad)

        # Botones fijos: 720p y 1080p
        self.btns_fijos: list[CustomButton] = []
        for res in RESOLUCIONES_FIJAS:
            btn = CustomButton(f"{res}p")
            btn.clicked.connect(lambda checked, r=res: self.set_resolucion(r))
            self.btns_fijos.append(btn)
            layout_opciones.addWidget(btn)

        # Botón "Más ▾" con dropdown para el resto
        self.btn_mas = CustomButton("Más ▾", is_toggle=False)
        self.menu_mas = QMenu(self)
        self.menu_mas.setStyleSheet(ESTILO_MENU)
        for res in RESOLUCIONES_EXTRA:
            accion = self.menu_mas.addAction(f"{res}p")
            accion.triggered.connect(lambda checked, r=res: self.set_resolucion(r))
        self.btn_mas.setMenu(self.menu_mas)
        layout_opciones.addWidget(self.btn_mas)

        layout_opciones.addSpacing(4)

        # Solo Audio
        self.btn_audio = CustomButton("Solo Audio")
        self.btn_audio.clicked.connect(self.toggle_audio)
        layout_opciones.addWidget(self.btn_audio)

        layout_opciones.addStretch()

        # Inputs de tiempo
        layout_tiempo = QHBoxLayout()
        layout_tiempo.setSpacing(5)
        self.input_inicio = QLineEdit()
        self.input_inicio.setPlaceholderText("Inicio (0:00)")
        self.input_fin = QLineEdit()
        self.input_fin.setPlaceholderText("Fin (1:30)")
        estilo_tiempo = """
            QLineEdit {
                background-color: #3a3a3c;
                color: white;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                max-width: 80px;
            }
        """
        self.input_inicio.setStyleSheet(estilo_tiempo)
        self.input_fin.setStyleSheet(estilo_tiempo)
        layout_tiempo.addWidget(QLabel("✂️"))
        layout_tiempo.addWidget(self.input_inicio)
        layout_tiempo.addWidget(QLabel("-"))
        layout_tiempo.addWidget(self.input_fin)
        layout_opciones.addLayout(layout_tiempo)

        layout_principal.addLayout(layout_opciones)

        # Selección inicial: 1080p
        self.set_resolucion(1080)

    # ------------------------------------------------------------------ #
    #  Gestión de resolución                                              #
    # ------------------------------------------------------------------ #

    def set_resolucion(self, res: int):
        self.resolucion_actual = res

        # Actualizar estado visual de botones fijos
        for btn in self.btns_fijos:
            btn.setChecked(btn.text() == f"{res}p")

        # Actualizar botón "Más": si la res es extra, lo mostramos activo
        es_extra = res in RESOLUCIONES_EXTRA
        self.btn_mas.setChecked(es_extra)
        if es_extra:
            self.btn_mas.setText(f"{res}p ▾")
        else:
            self.btn_mas.setText("Más ▾")

        # Negrita en la acción del menú seleccionada
        for accion in self.menu_mas.actions():
            f = accion.font()
            f.setBold(accion.text() == f"{res}p")
            accion.setFont(f)

    def toggle_audio(self):
        self.solo_audio = self.btn_audio.isChecked()
        for btn in self.btns_fijos:
            btn.setEnabled(not self.solo_audio)
        self.btn_mas.setEnabled(not self.solo_audio)

    # ------------------------------------------------------------------ #
    #  Descarga                                                           #
    # ------------------------------------------------------------------ #

    def procesar_descarga(self):
        url = self.input_url.text().strip()
        if not url:
            return

        inicio = self.input_inicio.text().strip() or None
        fin    = self.input_fin.text().strip() or None

        self.main_frame.setEnabled(False)
        self.input_url.setText("Descargando...")

        hilo = threading.Thread(
            target=self.ejecutar_descarga,
            args=(url, self.resolucion_actual, inicio, fin, self.solo_audio),
            daemon=True
        )
        hilo.start()

    def ejecutar_descarga(self, url, res, ini, fin, audio):
        print(f"\n[SpotDark] Iniciando: {url} | {res}p | {ini}-{fin} | Audio: {audio}")
        try:
            descargador.descargar_video(url, res, ini, fin, audio)
        finally:
            self.senales.descarga_finalizada.emit()

    def finalizar_proceso(self):
        print("\n[SpotDark] Proceso terminado.")
        QApplication.quit()

    def keyPressEvent(self, evento):
        if evento.key() == Qt.Key.Key_Escape:
            QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    fuente = QFont(".AppleSystemUIFont", 13)
    app.setFont(fuente)
    ventana = BarraSpotlight()
    ventana.show()
    sys.exit(app.exec())