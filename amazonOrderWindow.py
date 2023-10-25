from PySide6.QtCore import Qt ,QSortFilterProxyModel, QModelIndex
from PySide6.QtWidgets import QWidget, QMenu
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

        preshipped = pd.read_excel('appdata/preshipped.xlsx', dtype=str)
        preshipped.fillna('', inplace=True)
        self.model_preshipped = PandasModel(preshipped)
        self.proxymodel_preshipped = QSortFilterProxyModel()
        self.proxymodel_preshipped.setSourceModel(self.model_preshipped)
        self.ui.tableView_3.setModel(self.proxymodel_preshipped)
        self.ui.tableView_3.resizeColumnsToContents()
        # self.proxymodel_history.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.ui.label_2.setText(datetime.date.today().strftime("%m/%d/%Y"))

        # self.ui.pushButton.clicked.connect(self.save_button_clicked)
        self.ui.pushButton_apply.clicked.connect(self.apply_button_clicked)
        self.ui.pushButton_add.clicked.connect(self.add_button_clicked)
        self.ui.pushButton_del.clicked.connect(self.del_button_clicked)
        self.ui.pushButton_create.clicked.connect(self.create_button_clicked)
        self.ui.pushButton_refresh.clicked.connect(self.refresh_button_clicked)

        self.ui.tableView.doubleClicked.connect(self.table_double_clicked)
        self.ui.tableView_3.doubleClicked.connect(self.preshipped_double_clicked)

        self.ui.tableView.customContextMenuRequested.connect(self.table_context_menu)
        self.ui.tabWidget.tabBarClicked.connect(self.refresh_table)
        self.ui.tableView_3.customContextMenuRequested.connect(self.table3_context_menu)

    def table_context_menu(self, point):
        point.setX(point.x()+253)
        point.setY(point.y()+164)
        self.context_menu = QMenu()

        add_list = self.context_menu.addAction('Add to preshipped list')
        add_list.triggered.connect(self.add_to_preshipped)

        self.context_menu.exec(point)

    def table3_context_menu(self, point):
        point.setX(point.x()+253)
        point.setY(point.y()+164)
        self.context_menu = QMenu()

        add_list = self.context_menu.addAction('Delete')
        add_list.triggered.connect(self.delete_preshipped)

        self.context_menu.exec(point)
        
    def add_to_preshipped(self):
        r = self.ui.tableView.currentIndex().row()
        c = self.ui.tableView.currentIndex().column()
        order_id = self.ui.tableView.model().data(self.ui.tableView.model().index(r, 9))
        sku = self.ui.tableView.model().data(self.ui.tableView.model().index(r, 2))
        memo = ''
        # print(r, c)
        self.model_preshipped._data = pd.concat([self.model_preshipped._data, pd.Series([order_id, sku, memo], index=self.model_preshipped._data.columns).to_frame().T], ignore_index=True)
        self.model_preshipped._data.to_excel('appdata/preshipped.xlsx', index=False, engine='openpyxl')

    def delete_preshipped(self):
        r = self.ui.tableView_3.currentIndex().row()
        c = self.ui.tableView_3.currentIndex().column()
        self.model_preshipped._data.drop(r, inplace=True)
        self.model_preshipped = PandasModel(self.model_preshipped._data)
        self.proxymodel_preshipped = QSortFilterProxyModel()
        self.proxymodel_preshipped.setSourceModel(self.model_preshipped)
        self.ui.tableView_3.setModel(self.proxymodel_preshipped)
        self.model_preshipped._data.to_excel('appdata/preshipped.xlsx', index=False, engine='openpyxl')
        
    def refresh_table(self):
        self.model_preshipped = PandasModel(self.model_preshipped._data)
        self.proxymodel_preshipped = QSortFilterProxyModel()
        self.proxymodel_preshipped.setSourceModel(self.model_preshipped)
        self.ui.tableView_3.setModel(self.proxymodel_preshipped)
        self.ui.tableView_3.resizeColumnsToContents()
        

    def preshipped_double_clicked(self, item):
        if item.column() == 0:
            webbrowser.open("https://sellercentral.amazon.com/orders-v3/order/"+item.data())

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