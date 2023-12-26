from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QVBoxLayout, QMessageBox
from PySide6.QtCore import QSize, QObject
from invUpdateWindow import InvUpdateWindow
from amazonOrderWindow import AmazonOrderWindow
from salesUpdateWindow import SalesUpdateWindow
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import pandas as pd
import json, datetime

# root_path = "Z:/excel files/00 RMH Sale report/"
root_path = ''

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.setMinimumSize(QSize(400,200))

        button_1 = QPushButton("Inventory Update")
        button_2 = QPushButton("Amazon Order")
        button_3 = QPushButton("STORE Sales update (take about 5 min)")

        button_1.clicked.connect(self.button_1_clicked)
        button_2.clicked.connect(self.button_2_clicked)
        button_3.clicked.connect(self.button_3_clicked)

        layout = QVBoxLayout()

        layout.addWidget(button_1)
        layout.addWidget(button_2)
        layout.addWidget(button_3)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
    
    def button_1_clicked(self):
        self.w = InvUpdateWindow()
        self.w.show()

    def button_2_clicked(self):
        self.w2 = AmazonOrderWindow()
        self.w2.showMaximized()

    def button_3_clicked(self):

        self.w3 = SalesUpdateWindow(root_path)
        self.w3.show()
        

if __name__ == '__main__':
    app = QApplication()
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    app.exec()