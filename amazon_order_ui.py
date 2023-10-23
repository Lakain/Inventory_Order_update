# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'amazon_order.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QGridLayout, QHeaderView,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QTableView,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1500, 900)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QSize(1024, 720))
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(6)
        self.label_3 = QLabel(Form)
        self.label_3.setObjectName(u"label_3")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label_3.setFont(font)

        self.gridLayout.addWidget(self.label_3, 2, 8, 1, 3)

        self.pushButton_del = QPushButton(Form)
        self.pushButton_del.setObjectName(u"pushButton_del")

        self.gridLayout.addWidget(self.pushButton_del, 5, 9, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 0, 2, 1, 1)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 3, 1, 1)

        self.tableView_2 = QTableView(Form)
        self.tableView_2.setObjectName(u"tableView_2")
        self.tableView_2.setMinimumSize(QSize(300, 0))
        self.tableView_2.setSortingEnabled(True)
        self.tableView_2.horizontalHeader().setMinimumSectionSize(37)
        self.tableView_2.horizontalHeader().setDefaultSectionSize(80)
        self.tableView_2.horizontalHeader().setStretchLastSection(True)

        self.gridLayout.addWidget(self.tableView_2, 1, 8, 1, 3)

        self.pushButton_clr = QPushButton(Form)
        self.pushButton_clr.setObjectName(u"pushButton_clr")

        self.gridLayout.addWidget(self.pushButton_clr, 5, 10, 1, 1)

        self.pushButton_create = QPushButton(Form)
        self.pushButton_create.setObjectName(u"pushButton_create")
        font1 = QFont()
        font1.setBold(True)
        self.pushButton_create.setFont(font1)

        self.gridLayout.addWidget(self.pushButton_create, 7, 8, 1, 3)

        self.pushButton_apply = QPushButton(Form)
        self.pushButton_apply.setObjectName(u"pushButton_apply")

        self.gridLayout.addWidget(self.pushButton_apply, 0, 6, 1, 1)

        self.lineEdit = QLineEdit(Form)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setClearButtonEnabled(False)

        self.gridLayout.addWidget(self.lineEdit, 0, 4, 1, 2)

        self.label_4 = QLabel(Form)
        self.label_4.setObjectName(u"label_4")
        font2 = QFont()
        font2.setPointSize(11)
        font2.setBold(True)
        self.label_4.setFont(font2)

        self.gridLayout.addWidget(self.label_4, 0, 8, 1, 2)

        self.tableView = QTableView(Form)
        self.tableView.setObjectName(u"tableView")
        self.tableView.setEditTriggers(QAbstractItemView.AnyKeyPressed|QAbstractItemView.EditKeyPressed)
        self.tableView.setSortingEnabled(True)
        self.tableView.setCornerButtonEnabled(True)
        self.tableView.horizontalHeader().setCascadingSectionResizes(False)
        self.tableView.horizontalHeader().setDefaultSectionSize(100)
        self.tableView.horizontalHeader().setStretchLastSection(True)

        self.gridLayout.addWidget(self.tableView, 1, 0, 7, 7)

        self.listWidget = QListWidget(Form)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.gridLayout.addWidget(self.listWidget, 3, 8, 1, 3)

        self.pushButton_add = QPushButton(Form)
        self.pushButton_add.setObjectName(u"pushButton_add")

        self.gridLayout.addWidget(self.pushButton_add, 5, 8, 1, 1)

        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font2)

        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)

        self.pushButton_refresh = QPushButton(Form)
        self.pushButton_refresh.setObjectName(u"pushButton_refresh")

        self.gridLayout.addWidget(self.pushButton_refresh, 0, 10, 1, 1)

        QWidget.setTabOrder(self.lineEdit, self.pushButton_apply)
        QWidget.setTabOrder(self.pushButton_apply, self.tableView)
        QWidget.setTabOrder(self.tableView, self.tableView_2)
        QWidget.setTabOrder(self.tableView_2, self.listWidget)
        QWidget.setTabOrder(self.listWidget, self.pushButton_create)

        self.retranslateUi(Form)
        self.lineEdit.editingFinished.connect(self.pushButton_apply.click)
        self.pushButton_clr.clicked.connect(self.listWidget.clear)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Amazon Order", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Order List", None))
        self.pushButton_del.setText(QCoreApplication.translate("Form", u"Delete", None))
        self.label.setText(QCoreApplication.translate("Form", u"sku Filter", None))
        self.pushButton_clr.setText(QCoreApplication.translate("Form", u"Clear", None))
        self.pushButton_create.setText(QCoreApplication.translate("Form", u"Create Form", None))
        self.pushButton_apply.setText(QCoreApplication.translate("Form", u"Apply", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Order History", None))
        self.pushButton_add.setText(QCoreApplication.translate("Form", u"Add", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"MM/DD/YYYY", None))
        self.pushButton_refresh.setText(QCoreApplication.translate("Form", u"Refresh", None))
    # retranslateUi

