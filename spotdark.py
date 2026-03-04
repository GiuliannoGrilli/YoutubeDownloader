import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout
from PyQt6.QtCore import Qt

class BarraSpotlight(QWidget):
    def __init__(self):
        super().__init__()
        self.configurar_ventana()

    def configurar_ventana(self):
        # 1. Hacemos la ventana "invisible" (sin barra de título ni bordes) y siempre al frente
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 2. Tamaño inicial y centrado en la pantalla
        self.resize(700, 80)
        self.centrar_en_pantalla()

        # 3. Creamos el diseño (Layout)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 4. Creamos la barra de texto (QLineEdit)
        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("Pega el link de YouTube y presiona Enter...")
        
        # 5. ¡Le damos estilo con CSS! Tonos oscuros estilo Mac
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
                border: 1px solid #007aff; /* Borde azul al seleccionarlo, estilo macOS */
            }
        """)

        # 6. Conectamos la tecla "Enter" a una función
        self.input_box.returnPressed.connect(self.procesar_input)

        layout.addWidget(self.input_box)
        self.setLayout(layout)

    def centrar_en_pantalla(self):
        # Obtenemos la geometría de la pantalla y movemos nuestra ventana al centro exacto
        geometria_ventana = self.frameGeometry()
        centro_pantalla = self.screen().availableGeometry().center()
        geometria_ventana.moveCenter(centro_pantalla)
        self.move(geometria_ventana.topLeft())

    def procesar_input(self):
        # Esta función se ejecuta al presionar Enter
        texto = self.input_box.text().strip()
        if texto:
            print(f"URL recibida en la UI: {texto}")
            # Limpiamos la caja para la próxima vez y ocultamos la ventana
            self.input_box.clear()
            self.hide()

    def keyPressEvent(self, evento):
        # Permitimos cerrar la barra presionando la tecla "Escape" (ESC)
        if evento.key() == Qt.Key.Key_Escape:
            self.close()

if __name__ == '__main__':
    # Todo programa de PyQt necesita una QApplication corriendo de fondo
    app = QApplication(sys.argv)
    
    # Creamos nuestra ventana y la mostramos
    ventana = BarraSpotlight()
    ventana.show()
    
    # Mantenemos el programa en ejecución hasta que lo cerremos
    sys.exit(app.exec())