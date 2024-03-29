from PySide6.QtCore import Qt ,QSortFilterProxyModel
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QWidget, QMenu, QApplication, QTableWidgetItem
from amazon_order_ui import Ui_Form
from orderForm import orderForm
from pandasModel import PandasModel
import pandas as pd
import datetime
import webbrowser


class AmazonOrderWindow(QWidget):
    def __init__(self, root_path):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._root_path = root_path

        df = pd.read_excel(root_path+'amazon_order'+datetime.date.today().strftime("%m%d%y")+'.xlsx', dtype=str)
        df_history = pd.read_excel(root_path+'appdata/order_history.xlsx')
        preshipped = pd.read_excel(root_path+'appdata/preshipped.xlsx', dtype=str)

        last_history = df_history.drop_duplicates(['sku','order-id'], keep='last')
        df.insert(0, 'Last Order', df.merge(last_history[['order-id','order date','sku']], on=['order-id', 'sku'], how='left')['order date'].fillna(''))
        preshipped.fillna('', inplace=True)
        
        self.model = PandasModel(df)
        self.proxymodel = QSortFilterProxyModel()
        self.proxymodel.setSourceModel(self.model)
        self.proxymodel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.ui.tableView.setModel(self.proxymodel)

        self.model_history = PandasModel(df_history)
        self.proxymodel_history = QSortFilterProxyModel()
        self.proxymodel_history.setSourceModel(self.model_history)
        self.ui.tableView_2.setModel(self.proxymodel_history)
        self.proxymodel_history.setFilterCaseSensitivity(Qt.CaseInsensitive)

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
        self.ui.pushButton_clr.clicked.connect(self.clr_button_clicked)
        self.ui.pushButton_create.clicked.connect(self.create_button_clicked)
        self.ui.pushButton_refresh.clicked.connect(self.refresh_button_clicked)

        self.ui.tableView.doubleClicked.connect(self.table_double_clicked)
        self.ui.tableView_3.doubleClicked.connect(self.preshipped_double_clicked)

        self.ui.tableView.customContextMenuRequested.connect(self.table_context_menu)
        self.ui.tabWidget.tabBarClicked.connect(self.refresh_table)
        self.ui.tableView_2.customContextMenuRequested.connect(self.table2_context_menu)
        self.ui.tableView_3.customContextMenuRequested.connect(self.table3_context_menu)

        self.model_preshipped.datamodified.connect(self.save_preshipped)

################################################################################################
#---------------------------- Unshipped Table(TableView_1) ------------------------------------#
################################################################################################
    def table_context_menu(self, point):
        point.setX(self.x() + self.ui.tableView.x() + point.x() + 30)
        point.setY(self.y() + self.ui.tableView.logicalDpiY() + point.y() + 25)
        self.context_menu = QMenu()

        add_list = self.context_menu.addAction('Add to preshipped list')
        add_list.triggered.connect(self.add_to_preshipped)
        add_list2 = self.context_menu.addAction('Add to order list')
        add_list2.triggered.connect(self.add_button_clicked)
        add_list3 = self.context_menu.addAction('Delete')
        add_list3.triggered.connect(self.delete_unshipped)

        self.context_menu.exec(point)
    
    def delete_unshipped(self):
        rows = []
        for item in self.ui.tableView.selectedIndexes():
            r = self.ui.tableView.model().headerData(item.row(), Qt.Vertical)
            if int(r) not in rows:
                rows.append(int(r))

        self.model._data.drop(rows, inplace=True)
        self.model._data.drop(columns=['Last Order']).to_excel(self._root_path+'amazon_order'+datetime.date.today().strftime("%m%d%y")+'.xlsx', index=False)

        self.model = PandasModel(self.model._data)
        self.proxymodel = QSortFilterProxyModel()
        self.proxymodel.setSourceModel(self.model)
        self.proxymodel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.ui.tableView.setModel(self.proxymodel)
        

    # Ctrl + C -> Copy function implement.
    def keyPressEvent(self, event) -> None:
        if event.matches(QKeySequence.StandardKey.Copy):
            values = []
            row_index = self.ui.tableView.selectedIndexes()[0].row()
            for item in self.ui.tableView.selectedIndexes():
                if row_index!=item.row():
                    values.append('\n'+item.data())
                    row_index = item.row()
                else:
                    if values==[]:
                        values.append(item.data())
                    else:
                        values.append('\t'+item.data())
            QApplication.clipboard().setText(''.join(values))
            return
        super().keyPressEvent(event)

    def table_double_clicked(self,item):
        # if item.data().lower().startswith(('http://','https://')):
        #     webbrowser.open(item.data())
        if item.column() == 3: # sku column
            self.proxymodel_history.setFilterKeyColumn(0)
            self.proxymodel_history.setFilterFixedString(item.data())
        if item.column() == 10: # order-id column
            webbrowser.open("https://sellercentral.amazon.com/orders-v3/order/"+item.data())


    def apply_button_clicked(self):
        filter_input = self.ui.lineEdit.text()
        
        self.proxymodel.setFilterKeyColumn(3) # 'sku' column
        self.proxymodel.setFilterFixedString(filter_input)

################################################################################################
#---------------------------- History Table(TableView_2) --------------------------------------#
################################################################################################
    def table2_context_menu(self, point):
        point.setX(self.x() + self.ui.tableView_2.x() + point.x() + 10)
        point.setY(self.y() + self.ui.tableView_2.y() + point.y() + 45)
        self.context2_menu = QMenu()

        add_list = self.context2_menu.addAction('Delete')
        add_list.triggered.connect(self.delete_history)

        self.context2_menu.exec(point)
    

    # Delete order history
    def delete_history(self):
        rows = []
        for item in self.ui.tableView_2.selectedIndexes():
            r = self.ui.tableView_2.model().headerData(item.row(), Qt.Vertical)
            if int(r) not in rows:
                rows.append(int(r))
        # print(rows)

        self.model_history._data.drop(rows, inplace=True)
        self.model_history._data.reset_index(drop=True, inplace=True)
        self.model_history._data.to_excel(self._root_path+'appdata/order_history.xlsx', index=False)
        
        self.refresh_button_clicked()


    def refresh_button_clicked(self):
        df_history = pd.read_excel(self._root_path+'appdata/order_history.xlsx')
        self.model_history = PandasModel(df_history)
        self.proxymodel_history = QSortFilterProxyModel()
        self.proxymodel_history.setSourceModel(self.model_history)
        self.ui.tableView_2.setModel(self.proxymodel_history)


################################################################################################
#---------------------------- Preshipped Table(TableView_3) -----------------------------------#
################################################################################################
    def table3_context_menu(self, point):
        point.setX(self.x() + self.ui.tableView_3.x() + point.x() + 30)
        point.setY(self.y() + self.ui.tableView_3.logicalDpiY() + point.y() + 25)
        self.context3_menu = QMenu()

        add_list = self.context3_menu.addAction('Delete')
        add_list.triggered.connect(self.delete_preshipped)

        self.context3_menu.exec(point)
        
    def add_to_preshipped(self):
        r = self.ui.tableView.currentIndex().row()
        c = self.ui.tableView.currentIndex().column()
        order_id = self.ui.tableView.model().data(self.ui.tableView.model().index(r, 10))
        sku = self.ui.tableView.model().data(self.ui.tableView.model().index(r, 3))
        memo = ''
        item_name = self.ui.tableView.model().data(self.ui.tableView.model().index(r, 12))
        # print(r, c)
        self.model_preshipped._data = pd.concat([self.model_preshipped._data, pd.Series([order_id, sku, memo, item_name], index=self.model_preshipped._data.columns).to_frame().T], ignore_index=True)
        self.model_preshipped._data.to_excel(self._root_path+'appdata/preshipped.xlsx', index=False, engine='openpyxl')

    def delete_preshipped(self):
        r = self.ui.tableView_3.currentIndex().row()
        c = self.ui.tableView_3.currentIndex().column()
        self.model_preshipped._data.drop(r, inplace=True)
        self.model_preshipped._data.reset_index(drop=True, inplace=True)
        self.model_preshipped = PandasModel(self.model_preshipped._data)
        self.model_preshipped.datamodified.connect(self.save_preshipped)
        self.proxymodel_preshipped = QSortFilterProxyModel()
        self.proxymodel_preshipped.setSourceModel(self.model_preshipped)
        self.ui.tableView_3.setModel(self.proxymodel_preshipped)
        self.model_preshipped._data.to_excel(self._root_path+'appdata/preshipped.xlsx', index=False, engine='openpyxl')
        
    def refresh_table(self):
        self.model_preshipped = PandasModel(self.model_preshipped._data)
        self.model_preshipped.datamodified.connect(self.save_preshipped)
        self.proxymodel_preshipped = QSortFilterProxyModel()
        self.proxymodel_preshipped.setSourceModel(self.model_preshipped)
        self.ui.tableView_3.setModel(self.proxymodel_preshipped)
        self.ui.tableView_3.resizeColumnsToContents()
        

    def preshipped_double_clicked(self, item):
        if item.column() == 0: # order-id column
            webbrowser.open("https://sellercentral.amazon.com/orders-v3/order/"+item.data())

    # Save preshipped data to excel file.
    def save_preshipped(self):
        # print('saved')
        self.model_preshipped._data.to_excel(self._root_path+'appdata/preshipped.xlsx', index=False, engine='openpyxl')

    
################################################################################################
#---------------------------- Order Table(TableWidget) ----------------------------------------#
################################################################################################
    def add_button_clicked(self):
        for item in self.ui.tableView.selectedIndexes():
            if item.column()==3:
                r = self.ui.tableWidget.rowCount()
                self.ui.tableWidget.insertRow(r)
                self.ui.tableWidget.setItem(r, 0, QTableWidgetItem(self.ui.tableView.model().data(self.ui.tableView.model().index(item.row(), 3))))
                self.ui.tableWidget.setItem(r, 1, QTableWidgetItem(self.ui.tableView.model().data(self.ui.tableView.model().index(item.row(), 10))))


    def del_button_clicked(self):
        rows = []
        for item in self.ui.tableWidget.selectedIndexes():
            if item.row() not in rows:
                rows.append(item.row())
        for r in sorted(rows, reverse=True):
            self.ui.tableWidget.removeRow(r)


    def clr_button_clicked(self):
        for r in range(self.ui.tableWidget.rowCount()-1, -1, -1):
            self.ui.tableWidget.removeRow(r)


    def create_button_clicked(self):
        order_list = []
        for i in range(self.ui.tableWidget.rowCount()):
            order_list.append([self.ui.tableWidget.item(i, 0).text(), self.ui.tableWidget.item(i,1).text()])
        order_df = pd.DataFrame(order_list,columns=['sku', 'order-id'])
        self.orderForm = orderForm(order_df, self.model._data, self._root_path)
        self.orderForm.show()

