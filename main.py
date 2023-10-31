from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QVBoxLayout
from PySide6.QtCore import QSize
from invUpdateWindow import InvUpdateWindow
from amazonOrderWindow import AmazonOrderWindow
  
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.setMinimumSize(QSize(400,200))

        button_1 = QPushButton("Inventory Update")
        button_2 = QPushButton("Amazon Order")

        button_1.clicked.connect(self.button_1_clicked)
        button_2.clicked.connect(self.button_2_clicked)

        layout = QVBoxLayout()

        layout.addWidget(button_1)
        layout.addWidget(button_2)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
    
    def button_1_clicked(self):
        self.w = InvUpdateWindow()
        self.w.show()

    def button_2_clicked(self):
        self.w2 = AmazonOrderWindow()
        self.w2.showMaximized()

if __name__ == '__main__':
    app = QApplication()
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    app.exec()