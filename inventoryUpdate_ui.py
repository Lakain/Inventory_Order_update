# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'inventoryUpdate.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QHBoxLayout,
    QLabel, QLayout, QProgressBar, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(372, 363)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.pushButton_2 = QPushButton(Form)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.gridLayout.addWidget(self.pushButton_2, 5, 1, 1, 1)

        self.progressBar = QProgressBar(Form)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        self.progressBar.setOrientation(Qt.Horizontal)
        self.progressBar.setInvertedAppearance(False)
        self.progressBar.setTextDirection(QProgressBar.TopToBottom)

        self.gridLayout.addWidget(self.progressBar, 4, 0, 1, 4)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 5, 3, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 5, 0, 1, 1)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setFamilies([u"\ub9d1\uc740 \uace0\ub515"])
        font.setPointSize(9)
        self.label.setFont(font)

        self.gridLayout.addWidget(self.label, 3, 0, 1, 4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.checkBox_AL = QCheckBox(Form)
        self.checkBox_AL.setObjectName(u"checkBox_AL")

        self.verticalLayout.addWidget(self.checkBox_AL)

        self.checkBox_VF = QCheckBox(Form)
        self.checkBox_VF.setObjectName(u"checkBox_VF")

        self.verticalLayout.addWidget(self.checkBox_VF)

        self.checkBox_BY = QCheckBox(Form)
        self.checkBox_BY.setObjectName(u"checkBox_BY")

        self.verticalLayout.addWidget(self.checkBox_BY)

        self.checkBox_NBF = QCheckBox(Form)
        self.checkBox_NBF.setObjectName(u"checkBox_NBF")

        self.verticalLayout.addWidget(self.checkBox_NBF)

        self.checkBox_OUTRE = QCheckBox(Form)
        self.checkBox_OUTRE.setObjectName(u"checkBox_OUTRE")

        self.verticalLayout.addWidget(self.checkBox_OUTRE)

        self.checkBox_HZ = QCheckBox(Form)
        self.checkBox_HZ.setObjectName(u"checkBox_HZ")

        self.verticalLayout.addWidget(self.checkBox_HZ)

        self.checkBox_SNG = QCheckBox(Form)
        self.checkBox_SNG.setObjectName(u"checkBox_SNG")

        self.verticalLayout.addWidget(self.checkBox_SNG)

        self.checkBox_bord = QCheckBox(Form)
        self.checkBox_bord.setObjectName(u"checkBox_bord")

        self.verticalLayout.addWidget(self.checkBox_bord)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(-1, -1, -1, 155)
        self.checkBox_POS = QCheckBox(Form)
        self.checkBox_POS.setObjectName(u"checkBox_POS")

        self.verticalLayout_4.addWidget(self.checkBox_POS)

        self.checkBox_Amazon = QCheckBox(Form)
        self.checkBox_Amazon.setObjectName(u"checkBox_Amazon")

        self.verticalLayout_4.addWidget(self.checkBox_Amazon)

        self.pushButton_bord = QPushButton(Form)
        self.pushButton_bord.setObjectName(u"pushButton_bord")

        self.verticalLayout_4.addWidget(self.pushButton_bord)


        self.horizontalLayout.addLayout(self.verticalLayout_4)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 4)

        self.pushButton = QPushButton(Form)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setCheckable(False)

        self.gridLayout.addWidget(self.pushButton, 5, 2, 1, 1)

        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        font1 = QFont()
        font1.setPointSize(10)
        font1.setBold(True)
        self.label_2.setFont(font1)
        self.label_2.setScaledContents(False)
        self.label_2.setWordWrap(True)

        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 4)


        self.retranslateUi(Form)
        self.pushButton.clicked.connect(Form.close)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Inventory Update", None))
        self.pushButton_2.setText(QCoreApplication.translate("Form", u"Update", None))
        self.label.setText(QCoreApplication.translate("Form", u"Initialize...", None))
        self.checkBox_AL.setText(QCoreApplication.translate("Form", u"AL - ALICIA", None))
        self.checkBox_VF.setText(QCoreApplication.translate("Form", u"VF - AMEKOR", None))
        self.checkBox_BY.setText(QCoreApplication.translate("Form", u"BY - BOYANG", None))
        self.checkBox_NBF.setText(QCoreApplication.translate("Form", u"NBF - CHADE", None))
        self.checkBox_OUTRE.setText(QCoreApplication.translate("Form", u"OUTRE - SUNTAIYANG", None))
        self.checkBox_HZ.setText(QCoreApplication.translate("Form", u"HZ - SENSATIONNEL", None))
        self.checkBox_SNG.setText(QCoreApplication.translate("Form", u"SNG - SHAKE-N-GO", None))
        self.checkBox_bord.setText(QCoreApplication.translate("Form", u"Backorder List", None))
        self.checkBox_POS.setText(QCoreApplication.translate("Form", u"POS Inventory", None))
        self.checkBox_Amazon.setText(QCoreApplication.translate("Form", u"Amazon Unshipped", None))
        self.pushButton_bord.setText(QCoreApplication.translate("Form", u"Backorder List", None))
        self.pushButton.setText(QCoreApplication.translate("Form", u"Close", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"If you want to skip downloading data from email, use a check box.", None))
    # retranslateUi

