from PySide6.QtCore import Qt ,QSortFilterProxyModel
from PySide6.QtWidgets import QWidget
from amazon_order_ui import Ui_Form
from orderForm import orderForm
from pandasModel import PandasModel
import pandas as pd
import datetime
import webbrowser


class AmazonOrderWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        

        df = pd.read_csv('amazon_order'+datetime.date.today().strftime("%m%d%y")+'.csv', dtype=str)
        self.model = PandasModel(df)
        self.proxymodel = QSortFilterProxyModel()
        self.proxymodel.setSourceModel(self.model)
        self.proxymodel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.ui.tableView.setModel(self.proxymodel)

        df_history = pd.read_excel('appdata/order_history.xlsx')
        self.model_history = PandasModel(df_history)
        self.proxymodel_history = QSortFilterProxyModel()
        self.proxymodel_history.setSourceModel(self.model_history)
        self.ui.tableView_2.setModel(self.proxymodel_history)
        self.proxymodel_history.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.ui.label_2.setText(datetime.date.today().strftime("%m/%d/%Y"))

        # self.ui.pushButton.clicked.connect(self.save_button_clicked)
        self.ui.pushButton_apply.clicked.connect(self.apply_button_clicked)
        self.ui.pushButton_add.clicked.connect(self.add_button_clicked)
        self.ui.pushButton_del.clicked.connect(self.del_button_clicked)
        self.ui.pushButton_create.clicked.connect(self.create_button_clicked)
        self.ui.pushButton_refresh.clicked.connect(self.refresh_button_clicked)

        self.ui.tableView.doubleClicked.connect(self.table_double_clicked)

    def table_double_clicked(self,item):
        if item.data().lower().startswith(('http://','https://')):
            webbrowser.open(item.data())
        if item.column() == 2:
            self.proxymodel_history.setFilterKeyColumn(0)
            self.proxymodel_history.setFilterFixedString(item.data())


    def apply_button_clicked(self):
        filter_input = self.ui.lineEdit.text()
        
        self.proxymodel.setFilterKeyColumn(2) # 'sku' column
        self.proxymodel.setFilterFixedString(filter_input)
        
        # QMessageBox.information(self, "Info", self.ui.lineEdit.text())

    def add_button_clicked(self):
        if self.ui.tableView.currentIndex().column()==2:
            self.ui.listWidget.addItem(self.ui.tableView.model().data(self.ui.tableView.currentIndex()))
            # self.ui.listWidget.addItem(self.ui.tableView.selectedIndexes)
        # QMessageBox.information(self, "Info", "Add")

    def del_button_clicked(self):
        self.ui.listWidget.takeItem(self.ui.listWidget.currentRow())
        # QMessageBox.information(self, "Info", "Delete")


    def create_button_clicked(self):
        order_list = []
        for i in range(self.ui.listWidget.count()):
            order_list.append(self.ui.listWidget.item(i).text())
        self.orderForm = orderForm(order_list, self.model._data)
        self.orderForm.show()
        # QMessageBox.information(self, "Info", str(order_list))

    def refresh_button_clicked(self):
        df_history = pd.read_excel('appdata/order_history.xlsx')
        self.model_history = PandasModel(df_history)
        self.proxymodel_history = QSortFilterProxyModel()
        self.proxymodel_history.setSourceModel(self.model_history)
        self.ui.tableView_2.setModel(self.proxymodel_history)
        self.ui.tableView_2.resizeColumnsToContents()
        # QMessageBox.information(self, "Info", "Refresh")