# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'salesUpdate.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDateEdit, QGridLayout, QLabel,
    QProgressBar, QPushButton, QSizePolicy, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(400, 120)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QSize(400, 120))
        Form.setMaximumSize(QSize(400, 120))
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_3 = QLabel(Form)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 4)

        self.createButton = QPushButton(Form)
        self.createButton.setObjectName(u"createButton")

        self.gridLayout.addWidget(self.createButton, 5, 1, 1, 1)

        self.closeButton = QPushButton(Form)
        self.closeButton.setObjectName(u"closeButton")

        self.gridLayout.addWidget(self.closeButton, 5, 2, 1, 1)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.dateEdit_2 = QDateEdit(Form)
        self.dateEdit_2.setObjectName(u"dateEdit_2")
        self.dateEdit_2.setCalendarPopup(True)

        self.gridLayout.addWidget(self.dateEdit_2, 0, 3, 1, 1)

        self.dateEdit = QDateEdit(Form)
        self.dateEdit.setObjectName(u"dateEdit")
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setTimeSpec(Qt.LocalTime)

        self.gridLayout.addWidget(self.dateEdit, 0, 1, 1, 1)

        self.progressBar = QProgressBar(Form)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)
        self.progressBar.setAlignment(Qt.AlignCenter)
        self.progressBar.setTextVisible(True)

        self.gridLayout.addWidget(self.progressBar, 4, 0, 1, 4)

        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.label_2, 0, 2, 1, 1)


        self.retranslateUi(Form)
        self.closeButton.clicked.connect(Form.close)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Store Sales Update", None))
        self.label_3.setText("")
        self.createButton.setText(QCoreApplication.translate("Form", u"Create", None))
        self.closeButton.setText(QCoreApplication.translate("Form", u"Close", None))
        self.label.setText(QCoreApplication.translate("Form", u"From", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"To", None))
    # retranslateUi

