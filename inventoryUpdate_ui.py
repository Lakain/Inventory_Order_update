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
        Form.resize(409, 347)
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
        self.checkBox_8 = QCheckBox(Form)
        self.checkBox_8.setObjectName(u"checkBox_8")

        self.verticalLayout.addWidget(self.checkBox_8)

        self.checkBox_7 = QCheckBox(Form)
        self.checkBox_7.setObjectName(u"checkBox_7")

        self.verticalLayout.addWidget(self.checkBox_7)

        self.checkBox_6 = QCheckBox(Form)
        self.checkBox_6.setObjectName(u"checkBox_6")

        self.verticalLayout.addWidget(self.checkBox_6)

        self.checkBox_5 = QCheckBox(Form)
        self.checkBox_5.setObjectName(u"checkBox_5")

        self.verticalLayout.addWidget(self.checkBox_5)

        self.checkBox_4 = QCheckBox(Form)
        self.checkBox_4.setObjectName(u"checkBox_4")

        self.verticalLayout.addWidget(self.checkBox_4)

        self.checkBox_3 = QCheckBox(Form)
        self.checkBox_3.setObjectName(u"checkBox_3")

        self.verticalLayout.addWidget(self.checkBox_3)

        self.checkBox_2 = QCheckBox(Form)
        self.checkBox_2.setObjectName(u"checkBox_2")

        self.verticalLayout.addWidget(self.checkBox_2)

        self.checkBox = QCheckBox(Form)
        self.checkBox.setObjectName(u"checkBox")

        self.verticalLayout.addWidget(self.checkBox)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.pushButton_AL = QPushButton(Form)
        self.pushButton_AL.setObjectName(u"pushButton_AL")
        self.pushButton_AL.setEnabled(True)

        self.verticalLayout_3.addWidget(self.pushButton_AL)

        self.pushButton_VF = QPushButton(Form)
        self.pushButton_VF.setObjectName(u"pushButton_VF")

        self.verticalLayout_3.addWidget(self.pushButton_VF)

        self.pushButton_BY = QPushButton(Form)
        self.pushButton_BY.setObjectName(u"pushButton_BY")

        self.verticalLayout_3.addWidget(self.pushButton_BY)

        self.pushButton_NBF = QPushButton(Form)
        self.pushButton_NBF.setObjectName(u"pushButton_NBF")

        self.verticalLayout_3.addWidget(self.pushButton_NBF)

        self.pushButton_OUTRE = QPushButton(Form)
        self.pushButton_OUTRE.setObjectName(u"pushButton_OUTRE")

        self.verticalLayout_3.addWidget(self.pushButton_OUTRE)

        self.pushButton_HZ = QPushButton(Form)
        self.pushButton_HZ.setObjectName(u"pushButton_HZ")

        self.verticalLayout_3.addWidget(self.pushButton_HZ)

        self.pushButton_SNG = QPushButton(Form)
        self.pushButton_SNG.setObjectName(u"pushButton_SNG")

        self.verticalLayout_3.addWidget(self.pushButton_SNG)

        self.pushButton_bord = QPushButton(Form)
        self.pushButton_bord.setObjectName(u"pushButton_bord")

        self.verticalLayout_3.addWidget(self.pushButton_bord)


        self.horizontalLayout.addLayout(self.verticalLayout_3)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(-1, -1, -1, 172)
        self.checkBox_11 = QCheckBox(Form)
        self.checkBox_11.setObjectName(u"checkBox_11")

        self.verticalLayout_4.addWidget(self.checkBox_11)

        self.checkBox_10 = QCheckBox(Form)
        self.checkBox_10.setObjectName(u"checkBox_10")

        self.verticalLayout_4.addWidget(self.checkBox_10)


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

        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 4)


        self.retranslateUi(Form)
        self.pushButton.clicked.connect(Form.close)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Inventory Update", None))
        self.pushButton_2.setText(QCoreApplication.translate("Form", u"Update", None))
        self.label.setText(QCoreApplication.translate("Form", u"Initialize...", None))
        self.checkBox_8.setText(QCoreApplication.translate("Form", u"AL - ALICIA", None))
        self.checkBox_7.setText(QCoreApplication.translate("Form", u"VF - AMEKOR", None))
        self.checkBox_6.setText(QCoreApplication.translate("Form", u"BY - BOYANG", None))
        self.checkBox_5.setText(QCoreApplication.translate("Form", u"NBF - CHADE", None))
        self.checkBox_4.setText(QCoreApplication.translate("Form", u"OUTRE - SUNTAIYANG", None))
        self.checkBox_3.setText(QCoreApplication.translate("Form", u"HZ - SENSATIONNEL", None))
        self.checkBox_2.setText(QCoreApplication.translate("Form", u"SNG - SHAKE-N-GO", None))
        self.checkBox.setText(QCoreApplication.translate("Form", u"Backorder List", None))
        self.pushButton_AL.setText(QCoreApplication.translate("Form", u"AL(Gmail)", None))
        self.pushButton_VF.setText(QCoreApplication.translate("Form", u"VF(Gmail)", None))
        self.pushButton_BY.setText(QCoreApplication.translate("Form", u"BY(Gmail)", None))
        self.pushButton_NBF.setText(QCoreApplication.translate("Form", u"NBF(Gmail)", None))
        self.pushButton_OUTRE.setText(QCoreApplication.translate("Form", u"OUTRE(Gmail)", None))
        self.pushButton_HZ.setText(QCoreApplication.translate("Form", u"HZ(Gmail)", None))
        self.pushButton_SNG.setText(QCoreApplication.translate("Form", u"SNG(Gmail)", None))
        self.pushButton_bord.setText(QCoreApplication.translate("Form", u"Backorder List", None))
        self.checkBox_11.setText(QCoreApplication.translate("Form", u"POS Inventory", None))
        self.checkBox_10.setText(QCoreApplication.translate("Form", u"Amazon Unshipped", None))
        self.pushButton.setText(QCoreApplication.translate("Form", u"Close", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Inventory Data Check List (Prepare before start update)", None))
    # retranslateUi

