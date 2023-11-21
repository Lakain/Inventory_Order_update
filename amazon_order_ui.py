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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QSpacerItem,
    QTabWidget, QTableView, QWidget)

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
        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.label_2.setFont(font)

        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)

        self.pushButton_apply = QPushButton(Form)
        self.pushButton_apply.setObjectName(u"pushButton_apply")

        self.gridLayout.addWidget(self.pushButton_apply, 0, 6, 1, 1)

        self.lineEdit = QLineEdit(Form)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setClearButtonEnabled(False)

        self.gridLayout.addWidget(self.lineEdit, 0, 4, 1, 2)

        self.pushButton_add = QPushButton(Form)
        self.pushButton_add.setObjectName(u"pushButton_add")

        self.gridLayout.addWidget(self.pushButton_add, 6, 8, 1, 1)

        self.pushButton_del = QPushButton(Form)
        self.pushButton_del.setObjectName(u"pushButton_del")

        self.gridLayout.addWidget(self.pushButton_del, 6, 9, 1, 1)

        self.label_3 = QLabel(Form)
        self.label_3.setObjectName(u"label_3")
        font1 = QFont()
        font1.setPointSize(12)
        font1.setBold(True)
        self.label_3.setFont(font1)

        self.gridLayout.addWidget(self.label_3, 3, 8, 1, 3)

        self.pushButton_clr = QPushButton(Form)
        self.pushButton_clr.setObjectName(u"pushButton_clr")

        self.gridLayout.addWidget(self.pushButton_clr, 6, 10, 1, 1)

        self.pushButton_refresh = QPushButton(Form)
        self.pushButton_refresh.setObjectName(u"pushButton_refresh")

        self.gridLayout.addWidget(self.pushButton_refresh, 0, 10, 1, 1)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 3, 1, 1)

        self.tableView_2 = QTableView(Form)
        self.tableView_2.setObjectName(u"tableView_2")
        self.tableView_2.setMinimumSize(QSize(300, 0))
        self.tableView_2.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView_2.setSortingEnabled(True)
        self.tableView_2.horizontalHeader().setMinimumSectionSize(37)
        self.tableView_2.horizontalHeader().setDefaultSectionSize(80)
        self.tableView_2.horizontalHeader().setStretchLastSection(True)

        self.gridLayout.addWidget(self.tableView_2, 2, 8, 1, 3)

        self.pushButton_create = QPushButton(Form)
        self.pushButton_create.setObjectName(u"pushButton_create")
        font2 = QFont()
        font2.setBold(True)
        self.pushButton_create.setFont(font2)

        self.gridLayout.addWidget(self.pushButton_create, 8, 8, 1, 3)

        self.label_4 = QLabel(Form)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)

        self.gridLayout.addWidget(self.label_4, 0, 8, 1, 2)

        self.tabWidget = QTabWidget(Form)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setTabPosition(QTabWidget.North)
        self.tabWidget.setTabShape(QTabWidget.Rounded)
        self.tabWidget.setTabsClosable(False)
        self.tabWidget.setTabBarAutoHide(False)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.tab.sizePolicy().hasHeightForWidth())
        self.tab.setSizePolicy(sizePolicy1)
        self.horizontalLayout_2 = QHBoxLayout(self.tab)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.tableView = QTableView(self.tab)
        self.tableView.setObjectName(u"tableView")
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.setEditTriggers(QAbstractItemView.AnyKeyPressed|QAbstractItemView.EditKeyPressed)
        self.tableView.setSortingEnabled(True)
        self.tableView.setCornerButtonEnabled(True)
        self.tableView.horizontalHeader().setCascadingSectionResizes(False)
        self.tableView.horizontalHeader().setDefaultSectionSize(100)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.verticalHeader().setCascadingSectionResizes(False)

        self.horizontalLayout_2.addWidget(self.tableView)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.horizontalLayout = QHBoxLayout(self.tab_2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.tableView_3 = QTableView(self.tab_2)
        self.tableView_3.setObjectName(u"tableView_3")
        self.tableView_3.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView_3.setEditTriggers(QAbstractItemView.AnyKeyPressed|QAbstractItemView.EditKeyPressed)
        self.tableView_3.horizontalHeader().setStretchLastSection(True)

        self.horizontalLayout.addWidget(self.tableView_3)

        self.tabWidget.addTab(self.tab_2, "")

        self.gridLayout.addWidget(self.tabWidget, 2, 1, 7, 6)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 0, 2, 1, 1)

        self.listWidget = QListWidget(Form)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.gridLayout.addWidget(self.listWidget, 4, 8, 1, 3)

        QWidget.setTabOrder(self.lineEdit, self.pushButton_apply)
        QWidget.setTabOrder(self.pushButton_apply, self.tabWidget)
        QWidget.setTabOrder(self.tabWidget, self.tableView)
        QWidget.setTabOrder(self.tableView, self.tableView_2)
        QWidget.setTabOrder(self.tableView_2, self.listWidget)
        QWidget.setTabOrder(self.listWidget, self.pushButton_add)
        QWidget.setTabOrder(self.pushButton_add, self.pushButton_del)
        QWidget.setTabOrder(self.pushButton_del, self.pushButton_clr)
        QWidget.setTabOrder(self.pushButton_clr, self.pushButton_create)
        QWidget.setTabOrder(self.pushButton_create, self.pushButton_refresh)
        QWidget.setTabOrder(self.pushButton_refresh, self.tableView_3)

        self.retranslateUi(Form)
        self.lineEdit.editingFinished.connect(self.pushButton_apply.click)
        self.pushButton_clr.clicked.connect(self.listWidget.clear)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Amazon Order", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"MM/DD/YYYY", None))
        self.pushButton_apply.setText(QCoreApplication.translate("Form", u"Apply", None))
        self.pushButton_add.setText(QCoreApplication.translate("Form", u"Add", None))
        self.pushButton_del.setText(QCoreApplication.translate("Form", u"Delete", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Order List", None))
        self.pushButton_clr.setText(QCoreApplication.translate("Form", u"Clear", None))
        self.pushButton_refresh.setText(QCoreApplication.translate("Form", u"Refresh", None))
        self.label.setText(QCoreApplication.translate("Form", u"sku Filter", None))
        self.pushButton_create.setText(QCoreApplication.translate("Form", u"Create Form", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Order History", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("Form", u"Unshipped", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("Form", u"Preshipped", None))
    # retranslateUi

