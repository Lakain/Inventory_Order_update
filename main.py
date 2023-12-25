from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QVBoxLayout, QMessageBox
from PySide6.QtCore import QSize
from invUpdateWindow import InvUpdateWindow
from amazonOrderWindow import AmazonOrderWindow
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import pandas as pd
import json, datetime

# root_path = "Z:/excel files/00 RMH Sale report/"
root_path = ''


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.setMinimumSize(QSize(400,200))

        button_1 = QPushButton("Inventory Update")
        button_2 = QPushButton("Amazon Order")
        button_3 = QPushButton("STORE Sales update (take about 5 min)")

        button_1.clicked.connect(self.button_1_clicked)
        button_2.clicked.connect(self.button_2_clicked)
        button_3.clicked.connect(self.button_3_clicked)

        layout = QVBoxLayout()

        layout.addWidget(button_1)
        layout.addWidget(button_2)
        layout.addWidget(button_3)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
    
    def button_1_clicked(self):
        self.w = InvUpdateWindow()
        self.w.show()

    def button_2_clicked(self):
        self.w2 = AmazonOrderWindow()
        self.w2.showMaximized()

    def button_3_clicked(self):
        
        # Create RMN INV table
        with open(root_path+'appdata/db_auth.json') as f:
            temp = json.load(f)
            server = temp['server']
            database = temp['database'] 
            username = temp['username'] 
            password = temp['password']

        connection_string = 'DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password
        connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})

        engine = create_engine(connection_url)

        query = f"""
        SELECT 
            Item.ItemLookupCode AS 'Item Lookup Code',
            Item.Price AS 'Price',
            Item.Quantity AS 'Qty On Hand',
            Item.SubDescription3 AS 'Display',
            Item.SubDescription2 AS 'Comp Inv {datetime.date.today().strftime("%m%d")}',
            Item.Description AS 'Description',
            Item.ExtendedDescription AS 'Extended Description',
            Item.BinLocation AS 'Bin Location',
            sl.ReorderNumber AS 'Reorder Number',
            Item.SubDescription1 AS 'BRAND',
            dp.Name AS 'Departments',
            sp.Code AS 'Supplier Code',
            sp.SupplierName AS 'Supplier Name'
        FROM
            dbo.Item Item
            LEFT JOIN dbo.SupplierList sl ON Item.ID=sl.ItemID AND Item.SupplierID=sl.SupplierID
            LEFT JOIN dbo.Department dp ON Item.DepartmentID=dp.ID
            LEFT JOIN dbo.Supplier sp ON Item.SupplierID=sp.ID
        WHERE
            Item.DepartmentID IN (2, 4, 6) 
            AND Item.Inactive = 0
        ORDER BY
            ItemLookupCode;
        """

        with engine.connect() as conn, conn.begin():  
            fromPOS = pd.read_sql(query, conn, dtype={'Qty On Hand':'int64'},)

        fromPOS['Display'] = fromPOS['Display'].str.strip()
        fromPOS.loc[fromPOS['Display'].str.startswith('0'), 'Display'] = '0'
        fromPOS.loc[fromPOS['Display'].str.startswith('1'), 'Display'] = '1'
        fromPOS.loc[fromPOS['Display']=='', 'Display']='0'

        fromPOS['ITEM QTY'] = fromPOS['Qty On Hand']-fromPOS['Display'].astype('int64')
        fromPOS.loc[fromPOS['ITEM QTY']<0, 'ITEM QTY'] = 0

        temp = fromPOS[['Reorder Number', 'ITEM QTY']].groupby('Reorder Number').sum()
        temp.columns=['FIN TOT QTY']

        rmh_inv = fromPOS.merge(temp, on='Reorder Number', how='left')
        rmh_inv['FIN TOT QTY'] = rmh_inv['FIN TOT QTY'].fillna(0).astype('int64')

        # Create Sales
        query = """
        SELECT 
            FORMAT(hs.DateTransferred, 'yyyy-MM-dd') AS 'Date',
            hs.ItemLookupCode AS 'Item Lookup Code',
            hs.ItemDescription AS 'Description',
            hs.Quantity AS 'QTY SOLD',
            hs.DepartmentName AS 'Department',
            FORMAT(hs.DateTransferred, 'yyMM') AS 'yymm'
        FROM 
            dbo.ViewItemMovementHistory hs
        WHERE
            hs.DepartmentName IN ('Braids', 'Hair Extensions', 'Wigs')
            AND hs.Type=99
        ORDER BY
            hs.DateTransferred;
        """

        with engine.connect() as conn, conn.begin():  
            item_history = pd.read_sql(query, conn, dtype={'QTY SOLD': 'int64'})

        merged = item_history.merge(rmh_inv[['Item Lookup Code', 'Reorder Number', 'Supplier Name', 'Qty On Hand',\
                                    f'Comp Inv {datetime.date.today().strftime("%m%d")}', 'FIN TOT QTY']],
                                    how='inner', on='Item Lookup Code', sort='Date')
        
        merged.rename({'Reorder Number':'Item',
               'Supplier Name':'Company',
               'Qty On Hand':'RMH_Inv',
               f'Comp Inv {datetime.date.today().strftime("%m%d")}':'Comp Inv',
               'FIN TOT QTY':'Item Tot'}, axis='columns', inplace=True)
        
        merged.insert(7, 'Color', pd.NA)

        for i in range(len(merged)):
            merged.loc[i,'Color'] = merged.loc[i, 'Description'][len(merged['Item'][i])+1:]

        merged['Item_Inv'] = merged['Item']+'('+merged['Item Tot'].astype(str)+')'
        merged['Color_Inv'] = merged['Color']+'('+merged['RMH_Inv'].astype(str)+' - '+merged['Comp Inv'].astype(str)+') - '+merged['Item Lookup Code'].astype(str)
        merged['st_itm_cmp'] = '(' + merged['RMH_Inv'].astype(str) + ') ' + merged['Item'].astype(str) + ' ('+merged['Comp Inv'].astype(str) + ')'

        merged.sort_values(by="Date", ignore_index=True,inplace=True)

        # Create STORE Sales report
        wb = load_workbook(root_path+'appdata/STORE sales template.xlsx')

        ws1=wb.worksheets[1]
        ws2=wb.worksheets[2]

        ws1.delete_rows(2,ws1.max_row-1)
        ws2.delete_rows(2, ws2.max_row-1)

        for r in dataframe_to_rows(merged, index=False, header=False):
            ws1.append(r)

        for r in dataframe_to_rows(rmh_inv, index=False, header=False):
            ws2.append(r)

        wb.save(root_path+f'STORE Sales_{datetime.datetime.today().strftime("%m%d%y")}.xlsx')
        QMessageBox.information(self, "Info", "Updated")
        

if __name__ == '__main__':
    app = QApplication()
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    app.exec()