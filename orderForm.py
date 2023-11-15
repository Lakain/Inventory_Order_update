import pandas as pd
import datetime
import os

from orderForm_ui import Ui_Form
from pandasModel import PandasModel
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import  QSortFilterProxyModel

root_path = "Z:/excel files/00 RMH Sale report/"
# root_path = ''

class orderForm(QWidget):
    def __init__(self, order_list:list, df: pd.DataFrame):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        df = df[['sku','ORD', 'DESCRIPTION']]

        self.model = PandasModel(df[df['sku'].isin(order_list)].drop_duplicates())
        self.proxymodel = QSortFilterProxyModel()
        self.proxymodel.setSourceModel(self.model)
        self.ui.tableView.setModel(self.proxymodel)

        self.ui.save_Button.clicked.connect(self.save_button_clicked)

    def save_button_clicked(self):
        history = pd.read_excel(root_path+'appdata/order_history.xlsx', dtype=str)
        new_history = self.model._data[['sku']]
        new_history['order date'] = datetime.date.today().strftime("%m/%d/%Y")
        new_history['qty'] = self.model._data[['ORD']]
        history = pd.concat([history, new_history], ignore_index=True)
        history.to_excel(root_path+'appdata/order_history.xlsx', index=False)
        print(history)
        self.model._data.style.set_properties(border="thin solid black").to_excel(root_path+'appdata/orderForm.xlsx', index=False, engine='openpyxl')
        # os.system('"'+os.getcwd()+'/appdata/orderForm.xlsx"')
        os.system('"'+root_path+'/appdata/orderForm.xlsx"')
