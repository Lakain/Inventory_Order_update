import pandas as pd
import datetime
import os
import openpyxl

from orderForm_ui import Ui_Form
from pandasModel import PandasModel
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import  QSortFilterProxyModel


class orderForm(QWidget):
    def __init__(self, order_df:pd.DataFrame, df: pd.DataFrame, root_path):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._root_path = root_path

        df = order_df.merge(df[['sku','ORD', 'DESCRIPTION','product-id', 'order-id']], on=['sku', 'order-id'], how='left')
        df = df[['sku','ORD', 'DESCRIPTION','product-id', 'order-id']]
        df['ORD'] = pd.to_numeric(df['ORD'], downcast='integer')
        df.sort_values('sku', inplace=True, ignore_index=True)

        self.model = PandasModel(df)
        self.proxymodel = QSortFilterProxyModel()
        self.proxymodel.setSourceModel(self.model)
        self.ui.tableView.setModel(self.proxymodel)

        self.ui.save_Button.clicked.connect(self.save_button_clicked)

    def save_button_clicked(self):
        history = pd.read_excel(self._root_path+'appdata/order_history.xlsx', dtype=str)
        new_history = self.model._data[['sku']]
        new_history['order date'] = datetime.date.today().strftime("%m/%d/%Y")
        new_history['qty'] = self.model._data[['ORD']]
        new_history['order-id'] = self.model._data['order-id']
        history = pd.concat([history, new_history], ignore_index=True)
        history.to_excel(self._root_path+'appdata/order_history.xlsx', index=False)
        print(history)
        self.model._data.style.set_properties(border="thin solid black").to_excel(self._root_path+'appdata/orderForm.xlsx', index=False, engine='openpyxl', startrow=2)
        
        workbook= openpyxl.load_workbook(self._root_path+'/appdata/orderForm.xlsx')
        # workbook= openpyxl.load_workbook(os.getcwd()+'/appdata/orderForm.xlsx')
        worksheet = workbook.get_sheet_by_name('Sheet1')
        worksheet['A1'] = datetime.date.today().strftime("%m/%d/%y") +" 7 MILE (651-290-0362)"
        workbook.save(self._root_path+'appdata/orderForm.xlsx')
        
        os.system('"'+self._root_path+'/appdata/orderForm.xlsx"')
        # os.system('"'+os.getcwd()+'/appdata/orderForm.xlsx"')