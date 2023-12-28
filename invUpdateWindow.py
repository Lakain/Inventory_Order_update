from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QWidget, QMessageBox
from sp_api.api import Reports
from sp_api.base.reportTypes import ReportType
import pandas as pd
import datetime, json, webbrowser
from inventoryUpdate_ui import Ui_Form
from time import sleep
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# root_path = "Z:/excel files/00 RMH Sale report/"
# root_path = ''

class Worker(QObject):
    finished = Signal()
    task = Signal(str)
    progress = Signal(int)

    createReportResponse = None
    reportResponse = None
    report = None

    def __init__(self, root_path):
        super().__init__()
        self._root_path = root_path

        with open(self._root_path+'appdata/api_keys.json') as f:
            temp = json.load(f)
            self.credentials = temp['credentials']
            self.refresh_token = temp['refresh_token']

    def run(self):
        # InvUpdateWindow.start_update(self)
        self.createReportResponse = Reports(credentials=self.credentials, refresh_token=self.refresh_token).create_report(reportType=ReportType.GET_MERCHANT_LISTINGS_ALL_DATA)
        self.update_history = pd.read_excel(self._root_path+'appdata/update_history.xlsx')

        self.task.emit('Loading all_upc_inv')
        InvUpdateWindow.load_all_upc_inv(self)
        self.progress.emit(5)

        self.task.emit('Updating AL inventory')
        InvUpdateWindow.update_AL(self)
        self.update_history.loc[self.update_history['Initial']=='AL', 'Date'] = datetime.date.today().strftime("%d-%b")
        self.progress.emit(10)

        self.task.emit('Updating VF inventory')
        InvUpdateWindow.update_VF(self)
        self.update_history.loc[self.update_history['Initial']=='VF', 'Date'] = datetime.date.today().strftime("%d-%b")
        self.progress.emit(15)

        self.task.emit('Updating BY inventory')
        InvUpdateWindow.update_BY(self)
        self.update_history.loc[self.update_history['Initial']=='BY', 'Date'] = datetime.date.today().strftime("%d-%b")
        self.progress.emit(20)

        self.task.emit('Updating NBF inventory')
        InvUpdateWindow.update_NBF(self)
        self.update_history.loc[self.update_history['Initial']=='NBF', 'Date'] = datetime.date.today().strftime("%d-%b")
        self.progress.emit(25)

        self.task.emit('Updating OUTRE inventory')
        InvUpdateWindow.update_OUTRE(self)
        self.update_history.loc[self.update_history['Initial']=='OUTRE', 'Date'] = datetime.date.today().strftime("%d-%b")
        self.progress.emit(30)

        self.task.emit('Updating HZ inventory')
        InvUpdateWindow.update_HZ(self)
        self.update_history.loc[self.update_history['Initial']=='HZ', 'Date'] = datetime.date.today().strftime("%d-%b")
        self.progress.emit(35)

        self.task.emit('Updating SNG inventory')
        InvUpdateWindow.update_SNG(self)
        self.update_history.loc[self.update_history['Initial']=='SNG', 'Date'] = datetime.date.today().strftime("%d-%b")
        self.progress.emit(40)

        self.task.emit('Updating backorded items')
        InvUpdateWindow.update_backord(self)
        self.progress.emit(45)

        self.task.emit('Updating duplicate items')
        InvUpdateWindow.update_duplicate(self)
        self.progress.emit(50)

        self.task.emit('Updating POS inventory')
        InvUpdateWindow.update_POS(self)
        self.progress.emit(55)

        self.reportResponse = Reports(credentials=self.credentials, refresh_token=self.refresh_token).get_report(self.createReportResponse.payload['reportId'])
        while('reportDocumentId' not in self.reportResponse.payload):
            sleep(5)
            self.reportResponse = Reports(credentials=self.credentials, refresh_token=self.refresh_token).get_report(self.createReportResponse.payload['reportId'])
        f = open(self._root_path+"inv_data\Amazon_All+Listings+Report.txt", "w", encoding='utf-8')
        Reports(credentials=self.credentials, refresh_token=self.refresh_token).get_report_document(self.reportResponse.payload['reportDocumentId'], file=f)
        f.close()

        self.task.emit('Updating Amazon List')
        InvUpdateWindow.update_amazon(self)
        self.progress.emit(60)

        self.task.emit('Updating Amazon unshipped list')
        InvUpdateWindow.update_amazon_ord(self)
        self.progress.emit(65)

        self.update_history.to_excel(self._root_path+'appdata/update_history.xlsx', index=False)

        self.task.emit('Saving inventory data')
        InvUpdateWindow.save_data(self)
        self.progress.emit(100)

        self.task.emit('Done!')
        self.finished.emit()

class InvUpdateWindow(QWidget):
    def __init__(self, root_path):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._root_path = root_path

        # self.ui.pushButton.setDisabled(True)
        self.ui.pushButton_2.clicked.connect(self.start_update)

        self.ui.pushButton_AL.clicked.connect(lambda: webbrowser.open('https://mail.google.com/mail/u/0/#search/kjo%40aliciaintl.com'))
        self.ui.pushButton_VF.clicked.connect(lambda: webbrowser.open('https://mail.google.com/mail/u/0/?tab=rm&ogbl#search/no-reply%40amekor.com'))
        self.ui.pushButton_BY.clicked.connect(lambda: webbrowser.open('https://mail.google.com/mail/u/0/?tab=rm&ogbl#search/superjoshuadad%40gmail.com'))
        self.ui.pushButton_NBF.clicked.connect(lambda: webbrowser.open('https://mail.google.com/mail/u/0/?tab=rm&ogbl#search/jokim%40chade.com'))
        self.ui.pushButton_OUTRE.clicked.connect(lambda: webbrowser.open('https://mail.google.com/mail/u/0/?tab=rm&ogbl#label/Company%2FOutre'))
        self.ui.pushButton_HZ.clicked.connect(lambda: webbrowser.open('https://mail.google.com/mail/u/0/?tab=rm&ogbl#label/Company%2FSensationnel'))
        self.ui.pushButton_SNG.clicked.connect(lambda: webbrowser.open('https://mail.google.com/mail/u/0/?tab=rm&ogbl#search/sampark%40snghair.com'))
        self.ui.pushButton_bord.clicked.connect(lambda: webbrowser.open('https://docs.google.com/spreadsheets/d/1QAl-guabl4lCe83mRXjK7-51ZaSl-xEpC3v_3XrktE8/edit?usp=sharing'))

    def reportTask(self, s):
        self.ui.label.setText(s)

    def reportProgress(self, n):
        self.ui.progressBar.setValue(n)

    def start_update(self):
        self.thread = QThread()
        self.worker = Worker(self._root_path)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.reportProgress)
        self.worker.task.connect(self.reportTask)

        self.thread.start()
        
        self.ui.pushButton_2.setEnabled(False)
        self.ui.pushButton.setEnabled(False)

        self.thread.finished.connect(lambda: self.ui.pushButton.setEnabled(True))
        self.thread.finished.connect(lambda: self.ui.pushButton_2.setEnabled(True))
        self.thread.finished.connect(lambda: QMessageBox.information(self, "Info", "Update Finished"))

    def load_all_upc_inv(self):
        # all upc inv import
        # filename = QFileDialog.getOpenFileName(self, "Select File", "./", "Any Files (*)")
        # self.all_upc_inv = pd.read_excel(filename[0], sheet_name=3)
        self.all_upc_inv = pd.read_excel(self._root_path+"appdata/all_upc_inv.xlsx")

        # delete unnecessary columns
        self.all_upc_inv.drop(self.all_upc_inv.columns[5:], axis=1, inplace=True)

        # save column name for future use
        self.column_name = self.all_upc_inv.columns

        # if filename != None:
        #     QMessageBox.information(self, "Info", "Updated")
        # QMessageBox.information(self, "Info", "Updated")
    
    def update_AL(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File ALICIA (AL) brs inv", "./", "Any Files (*)")
        # temp1 = pd.read_excel(filename[0])
        temp1 = pd.read_excel(self._root_path+'inv_data\AL_brs inv.xls')

        # filename = QFileDialog.getOpenFileName(self, "Select File ALICIA (AL) inv", "./", "Any Files (*)")
        # temp2 = pd.read_excel(filename[0])
        temp2 = pd.read_excel(self._root_path+'inv_data\AL_inv.xls')

        new_inv = pd.concat([temp1, temp2], ignore_index=True)
        # get column name for choose upc / company inventory / description / extended description columns
        column_list = list(new_inv.columns)

        # Select Company name
        # company_list = ['AL', 'VF', 'BY', 'OUTRE','HZ']
        comp_name = 'AL'

        # Select UPC column
        itemlookupcode = 'AliasItemNo'

        # Select Company Inventory column
        comp_inv = 'OnHand Customer'

        # Select Description column
        description = 'ItemCode'

        # Select Extended Description column
        ext_desc = 'ItemCodeDesc'

        # Merge needed columns
        new_inv = new_inv[[itemlookupcode, comp_inv, description, ext_desc]]

        new_inv.insert(0, 'Company', comp_name)

        # rename columns
        new_inv.columns = self.column_name

        # pre processing
        new_inv.dropna(subset=['UPC', 'company Inventory'])
        new_inv['company Inventory'] = new_inv['company Inventory'].astype('int')

        # delete exist data
        self.all_upc_inv.drop(self.all_upc_inv[self.all_upc_inv['COMPAY']==comp_name].index, inplace=True)

        # 
        self.all_upc_inv = pd.concat([self.all_upc_inv, new_inv])

        # reset index
        self.all_upc_inv = self.all_upc_inv.reset_index(drop=True)

        # self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")
        
        # QMessageBox.information(self, "Info", "Updated")

    def update_VF(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File AMEKOR (VF)", "./", "Any Files (*)")
        # new_inv = pd.read_excel(filename[0])
        new_inv = pd.read_excel(self._root_path+'inv_data\VF_Inventory.xls', dtype={'Barcode':str})

        # get column name for choose upc / company inventory / description / extended description columns
        column_list = list(new_inv.columns)

        # Select Company name
        # company_list = ['AL', 'VF', 'BY', 'OUTRE','HZ']
        comp_name = 'VF'

        # Select UPC column
        itemlookupcode = 'Barcode'

        # Select Company Inventory column
        comp_inv = 'On hand'

        # Select Description column
        description = 'Product ID'

        # Select Extended Description column
        ext_desc = 'SKU'

        # Merge needed columns
        new_inv = new_inv[[itemlookupcode, comp_inv, description, ext_desc]]
        new_inv.insert(0, 'Company', comp_name)

        # cast data float to int
        new_inv.loc[new_inv[itemlookupcode].str.isnumeric()==False, 'Barcode'] = pd.NA
        new_inv[itemlookupcode]=pd.to_numeric(new_inv[itemlookupcode], downcast='integer')

        # rename columns
        new_inv.columns =self.column_name

        # pre processing
        new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
        new_inv['company Inventory'] = new_inv['company Inventory'].astype('int')
        new_inv['UPC'] = new_inv['UPC'].astype('int64')
        new_inv.loc[new_inv['company Inventory']<10, 'company Inventory'] = 0

        # delete exist data
        self.all_upc_inv.drop(self.all_upc_inv[self.all_upc_inv['COMPAY']==comp_name].index, inplace=True)

        # 
        self.all_upc_inv = pd.concat([self.all_upc_inv, new_inv])

        # reset index
        self.all_upc_inv = self.all_upc_inv.reset_index(drop=True)

        # self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")
        # QMessageBox.information(self, "Info", "Updated")

    def update_BY(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File BOYANG (BY)", "./", "Any Files (*)")
        # new_inv = pd.read_excel(filename[0], skiprows=3)
        new_inv = pd.read_excel(self._root_path+'inv_data\BY_InventoryListAll.xls', skiprows=3)

        # get column name for choose upc / company inventory / description / extended description columns
        column_list = list(new_inv.columns)

        # Select Company name
        # company_list = ['AL', 'VF', 'BY', 'OUTRE','HZ']
        comp_name = 'BY'

        # Select UPC column
        itemlookupcode = 'Barcode'

        # Select Company Inventory column
        comp_inv = 'O/H'

        # Select Description column
        description = 'Item Name'

        # Select Extended Description column
        ext_desc = 'Color'

        # Merge needed columns
        new_inv = new_inv[[itemlookupcode, comp_inv, description, ext_desc]]

        new_inv.insert(0, 'Company', comp_name)

        # rename columns
        new_inv.columns = self.column_name

        # pre processing
        new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
        new_inv['company Inventory'] = new_inv['company Inventory'].astype('int')
        # new_inv['UPC'] = new_inv['UPC'].astype('int64')
        new_inv.loc[new_inv['company Inventory']<10, 'company Inventory'] = 0

        # delete exist data
        self.all_upc_inv.drop(self.all_upc_inv[self.all_upc_inv['COMPAY']==comp_name].index, inplace=True)

        # 
        self.all_upc_inv = pd.concat([self.all_upc_inv, new_inv])

        # reset index
        self.all_upc_inv = self.all_upc_inv.reset_index(drop=True)

        # self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")
        # QMessageBox.information(self, "Info", "Updated")

    def update_NBF(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File CHADE (NBF)", "./", "Any Files (*)")
        # new_inv = pd.read_excel(filename[0])
        new_inv = pd.read_excel(self._root_path+'inv_data/NBF_Chade Fashions.xlsx')

        # get column name for choose upc / company inventory / description / extended description columns
        column_list = list(new_inv.columns)

        # Select Company name
        # company_list = ['AL', 'VF', 'BY', 'NBF', 'OUTRE','HZ']
        comp_name = 'NBF'

        # Select UPC column
        itemlookupcode = 'UPC Code'

        # Select Company Inventory column
        comp_inv = 'Unnamed: 6'

        # Select Description column
        description = 'No.'

        # Select Extended Description column
        ext_desc = 'Description'

        # Merge needed columns
        new_inv = new_inv[[itemlookupcode, comp_inv, description, ext_desc]]
        new_inv.insert(0, 'Company', comp_name)

        # rename columns
        new_inv.columns = self.column_name

        # pre processing
        new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
        new_inv[['company Inventory']] = new_inv[['company Inventory']].replace({'A':20, 'B':5, 'C':0, 'X':0})

        # delete exist data
        self.all_upc_inv.drop(self.all_upc_inv[self.all_upc_inv['COMPAY']==comp_name].index, inplace=True)

        # 
        self.all_upc_inv = pd.concat([self.all_upc_inv, new_inv])

        # reset index
        self.all_upc_inv = self.all_upc_inv.reset_index(drop=True)

        # self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")
        # QMessageBox.information(self, "Info", "Updated")

    def update_OUTRE(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File SUN TAIYANG (OUTRE)", "./", "Any Files (*)")
        # new_inv = pd.read_csv(filename[0], sep='\t', encoding='utf_16', on_bad_lines='warn', skiprows=[1], skipfooter=1)
        new_inv = pd.read_csv(self._root_path+'inv_data\OUTRE_StockAvailability.csv', sep='\t', encoding='utf_16', on_bad_lines='warn', skiprows=[1], skipfooter=1, engine='python')

        # get column name for choose upc / company inventory / description / extended description columns
        column_list = list(new_inv.columns)
        
        # Select Company name
        # company_list = ['AL', 'VF', 'BY', 'NBF', 'OUTRE','HZ']
        comp_name = 'OUTRE'

        # Select UPC column
        itemlookupcode = 'BARCODE'

        # Select Company Inventory column
        comp_inv = 'AVAIL'

        # Select Description column
        description = 'ITEM'

        # Select Extended Description column
        ext_desc = 'COLOR'

        # Merge needed columns
        new_inv = new_inv[[itemlookupcode, comp_inv, description, ext_desc]]

        new_inv.insert(0, 'Company', comp_name)

        # cast data float to int
        # new_inv[comp_inv] = new_inv[comp_inv].astype('Int32')

        # rename columns
        new_inv.columns =self.column_name

        # pre processing
        new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
        new_inv[['company Inventory']] = new_inv[['company Inventory']].replace({'Y':20,'N':0})

        # delete exist data
        self.all_upc_inv.drop(self.all_upc_inv[self.all_upc_inv['COMPAY']==comp_name].index, inplace=True)

        # 
        self.all_upc_inv = pd.concat([self.all_upc_inv, new_inv])

        # reset index
        self.all_upc_inv = self.all_upc_inv.reset_index(drop=True)

        # self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")
        # QMessageBox.information(self, "Info", "Updated")

    def update_HZ(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File SENSATIONNEL (HZ)", "./", "Any Files (*)")
        # new_inv = pd.read_csv(filename[0], sep='\t', encoding='utf_16', on_bad_lines='warn', skiprows=[1], skipfooter=1)
        new_inv = pd.read_csv(self._root_path+'inv_data\HZ_StockAvailability.csv', sep='\t', encoding='utf_16', on_bad_lines='warn', skiprows=[1], skipfooter=1, engine='python')

        # get column name for choose upc / company inventory / description / extended description columns
        column_list = list(new_inv.columns)

        # Select Company name
        # company_list = ['AL', 'VF', 'BY', 'NBF', 'OUTRE','HZ']
        comp_name = 'HZ'

        # Select UPC column
        itemlookupcode = 'BARCODE'

        # Select Company Inventory column
        comp_inv = 'AVAIL'

        # Select Description column
        description = 'ITEM'

        # Select Extended Description column
        ext_desc = 'COLOR'

        # Merge needed columns
        new_inv = new_inv[[itemlookupcode, comp_inv, description, ext_desc]]

        new_inv.insert(0, 'Company', comp_name)

        # cast data float to int
        # new_inv[comp_inv] = new_inv[comp_inv].astype('Int32')

        # rename columns
        new_inv.columns = self.column_name

        # pre processing
        new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
        new_inv[['company Inventory']] = new_inv[['company Inventory']].replace({'Y':20,'N':0})
        #######################

        # delete exist data
        self.all_upc_inv.drop(self.all_upc_inv[self.all_upc_inv['COMPAY']==comp_name].index, inplace=True)

        # 
        self.all_upc_inv = pd.concat([self.all_upc_inv, new_inv])

        # reset index
        self.all_upc_inv = self.all_upc_inv.reset_index(drop=True)

        # self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")
        # QMessageBox.information(self, "Info", "Updated")

    def update_SNG(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File SHAKE-N-GO (SNG)", "./", "Any Files (*)")
        # new_inv = pd.read_excel(filename[0])
        new_inv = pd.read_excel(self._root_path+'inv_data\SNG_inv.xlsx')

        # get column name for choose upc / company inventory / description / extended description columns
        column_list = list(new_inv.columns)

        # Select Company name
        # company_list = ['AL', 'VF', 'BY', 'NBF', 'OUTRE','HZ']
        comp_name = 'SNG'

        # Select UPC column
        itemlookupcode = 'Barcode'

        # Select Company Inventory column
        comp_inv = 'Available'

        # Select Description column
        description = 'Item'

        # Select Extended Description column
        ext_desc = 'Descrip'

        # Merge needed columns
        new_inv = new_inv[[itemlookupcode, comp_inv, description, ext_desc]]

        new_inv.insert(0, 'Company', comp_name)

        # rename columns
        new_inv.columns =self.column_name

        # pre processing
        new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
        new_inv[['company Inventory']] = new_inv[['company Inventory']].replace({'Y':20,'N':0})

        # delete exist data
        self.all_upc_inv.drop(self.all_upc_inv[self.all_upc_inv['COMPAY']==comp_name].index, inplace=True)

        # 
        self.all_upc_inv = pd.concat([self.all_upc_inv, new_inv])

        # reset index
        self.all_upc_inv = self.all_upc_inv.reset_index(drop=True)

        # self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")
        # QMessageBox.information(self, "Info", "Updated")

    def update_backord(self):
        # filename = QFileDialog.getOpenFileName(self, "Select File backorded_list", "./", "Any Files (*)")
        # backorder_list = pd.read_csv(filename[0], dtype={'upc':str})
        backorder_list = pd.read_excel(self._root_path+'appdata/backorder_list.xlsx', dtype={'upc':str})
        self.all_upc_inv['UPC'] = self.all_upc_inv['UPC'].astype(str)
        self.all_upc_inv['DESCRIPTION'] = self.all_upc_inv['DESCRIPTION'].astype(str)
        self.all_upc_inv['EXTENDED DESCRIPTION'] = self.all_upc_inv['EXTENDED DESCRIPTION'].astype(str)
        print(self.all_upc_inv.loc[self.all_upc_inv["UPC"].isin(backorder_list['upc'])])
        self.all_upc_inv.loc[self.all_upc_inv["UPC"].isin(backorder_list['upc']) , "company Inventory"] = 0
        self.all_upc_inv[self.all_upc_inv['UPC'].isin(backorder_list['upc'])]

        # QMessageBox.information(self, "Info", "Updated")

    def update_duplicate(self):
        # filename = QFileDialog.getOpenFileName(self, "Select File dulplicate_list", "./", "Any Files (*)")
        # duplicate_list = pd.read_csv(filename[0], dtype={'UPC': str, 'DESCRIPTION':str,'EXTENDED DESCRIPTION':str})
        duplicate_list = pd.read_excel(self._root_path+'appdata/duplicate_list.xlsx', dtype={'UPC': str, 'DESCRIPTION':str,'EXTENDED DESCRIPTION':str})

        duplicate_index = self.all_upc_inv[(self.all_upc_inv['UPC'].isin(duplicate_list['UPC'])&(self.all_upc_inv['DESCRIPTION'].isin(duplicate_list['DESCRIPTION'])&(self.all_upc_inv['EXTENDED DESCRIPTION'].isin(duplicate_list['EXTENDED DESCRIPTION']))))].index
        self.all_upc_inv.drop(duplicate_index, inplace=True)

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_dup.setDisabled(True)

    def update_POS(self):
        with open(self._root_path+'appdata/db_auth.json') as f:
            temp = json.load(f)
            server = temp['server']
            database = temp['database'] 
            username = temp['username'] 
            password = temp['password']

        connection_string = 'DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password
        connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})

        engine = create_engine(connection_url)

        query = "SELECT ItemLookupCode, Price, Quantity, SubDescription3, SubDescription2, Description, ExtendedDescription, BinLocation, ReorderNumber, SubDescription1, dp.Name, sp.Code, sp.SupplierName\
                FROM dbo.Item Item \
                LEFT JOIN dbo.SupplierList sl \
                ON Item.ID=sl.ItemID AND Item.SupplierID=sl.SupplierID\
                LEFT JOIN dbo.Department dp\
                ON Item.DepartmentID=dp.ID\
                LEFT JOIN dbo.Supplier sp\
                ON Item.SupplierID=sp.ID\
                WHERE Item.DepartmentID IN (2, 4, 6) AND Item.Inactive = 0\
                ORDER BY ItemLookupCode;"

        with engine.connect() as conn, conn.begin():  
            fromPOS = pd.read_sql(query, conn, dtype={'Quantity':'int64'})

        fromPOS.fillna('', inplace=True)

        fromPOS.columns=['Item Lookup Code', 'Price', 'Qty On Hand', 'Display', f'Comp Inv {datetime.date.today().strftime("%m%d")}',
            'Description', 'Extended Description', 'Bin Location', 'Reorder Number',
            'BRAND', 'Departments', 'Supplier Code', 'Supplier Name']

        # save column name for future use
        column_name = fromPOS.columns

        # fromPOS['Display'].replace(regex=['\(.\)'], value='', inplace=True)

        # fromPOS['Display'] = fromPOS['Display'].str.strip()

        # fromPOS['Display'].fillna('0', inplace=True)
        fromPOS['Display'] = fromPOS['Display'].str.strip()
        fromPOS.loc[fromPOS['Display'].str.startswith('0'), 'Display'] = '0'
        fromPOS.loc[fromPOS['Display'].str.startswith('1'), 'Display'] = '1'
        # fromPOS.loc[fromPOS['Display'].str.startswith('C'), 'Display'] = '0'
        fromPOS.loc[fromPOS['Display']=='', 'Display'] = '0'

        fromPOS['Display'] = fromPOS['Display'].astype(int)

        fromPOS['A'] = ''

        fromPOS['FIN QTY'] = fromPOS['Qty On Hand']-fromPOS['Display']
        fromPOS.loc[fromPOS['FIN QTY']<0, 'FIN QTY'] = 0

        # update comp inv
        comp_inv_data = self.all_upc_inv[['UPC', 'company Inventory']].rename(columns={'UPC': 'Item Lookup Code'})

        fromPOS['Item Lookup Code'] = fromPOS['Item Lookup Code'].astype(str)
        comp_inv_data['Item Lookup Code'] = comp_inv_data['Item Lookup Code'].astype(str)

        if len(fromPOS.merge(comp_inv_data, how='left', on='Item Lookup Code')) != len(fromPOS):
            print('\033[31m'+'check duplicate UPC (POS - all_upc_inv)'+'\033[0m')
        fromPOS[column_name[4]] = fromPOS.merge(comp_inv_data, how='left', on='Item Lookup Code')['company Inventory']

        fromPOS[column_name[4]].fillna(0, inplace=True)

        self.fromPOS = fromPOS
        #fromPOS.to_csv('fromPOS'+datetime.date.today().strftime("%Y-%m-%d")+'.csv', index=False)
        #######################

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_POS.setDisabled(True)

    def update_amazon(self):
        # filename = QFileDialog.getOpenFileName(self, "Select File Amazon All List Report", "./", "Any Files (*)")
        # all_amazon = pd.read_csv(filename[0], sep='\t')
        all_amazon = pd.read_csv(self._root_path+'inv_data\Amazon_All+Listings+Report.txt', sep='\t')
        all_amazon = all_amazon[['seller-sku', 'asin1', 'item-name', 'item-description', 'listing-id',
       'price', 'quantity', 'open-date', 'product-id-type', 'item-note',
       'item-condition', 'will-ship-internationally', 'expedited-shipping',
       'product-id', 'pending-quantity', 'fulfillment-channel', 'status']]
        all_amazon['product-id'] = all_amazon['product-id'].astype(str)
        all_amazon['inv_Sum'] = 0
        all_amazon['inv_comp'] = 0
        all_amazon['inv_store'] = 0

        # merge comp inv
        all_upc_inv = self.all_upc_inv

        comp_inv_data = all_upc_inv[['UPC', 'company Inventory']].rename(columns={'UPC': 'product-id'})
        comp_inv_data['product-id'] = comp_inv_data['product-id'].astype(str)


        if len(all_amazon.merge(comp_inv_data, how='left', on='product-id')) != len(all_amazon):
            print('\033[31m'+'check duplicate UPC (all_amazon - all_upc_inv)'+'\033[0m')
        
        all_amazon['inv_comp'] = all_amazon.merge(comp_inv_data, how='left', on='product-id')['company Inventory']

        all_amazon['inv_comp'].fillna(0, inplace=True)
        all_amazon['inv_comp'] = all_amazon['inv_comp'].astype(int)

        # merge store inv
        fromPOS = self.fromPOS

        store_inv_data = fromPOS[['Item Lookup Code', 'FIN QTY']].rename(columns={'Item Lookup Code': 'product-id'})
        store_inv_data['product-id'] = store_inv_data['product-id'].astype(str)

        all_amazon['inv_store'] = all_amazon.merge(store_inv_data, how='left', on='product-id')['FIN QTY']
        #print(all_amazon.merge(store_inv_data, how='left', on='product-id')['FIN QTY'].len())

        all_amazon['inv_store'].fillna(0, inplace=True)
        all_amazon['inv_store'] = all_amazon['inv_store'].astype(int)

        # calc inv_sum
        all_amazon['inv_Sum'] = all_amazon['inv_store'] + all_amazon['inv_comp']

        self.all_amazon = all_amazon
        # all_amazon.to_csv('all_amazon.csv', index=False)

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_amazon.setDisabled(True)

    def update_amazon_ord(self):
        # filename = QFileDialog.getOpenFileName(self, "Select File Amazon unsshipped order list", "./", "Any Files (*)")
        # unshipped_data = pd.read_csv(filename[0], sep='\t', dtype={'product-id':str})
        unshipped_data = pd.read_csv(self._root_path+'inv_data\Amazon_unshipped_report.txt', sep='\t', dtype={'product-id':str})

        all_amazon = self.all_amazon[['seller-sku', 'inv_comp', 'inv_store', 'product-id', 'item-name']]

        merged_data = unshipped_data.merge(all_amazon, how='left', left_on='sku', right_on='seller-sku')
        merged_data.drop('seller-sku', axis=1, inplace=True)

        fromPOS = self.fromPOS[['Item Lookup Code', 'Bin Location']]
        fromPOS = fromPOS.astype(str)
        
        all_upc_inv = self.all_upc_inv[['UPC', 'DESCRIPTION']]
        all_upc_inv = all_upc_inv.astype(str)

        merged_data = merged_data.merge(fromPOS, how='left', left_on='product-id', right_on='Item Lookup Code')
        merged_data.drop('Item Lookup Code', axis=1, inplace=True)
        merged_data = merged_data.merge(all_upc_inv, how='left', left_on='product-id', right_on='UPC')
        merged_data.drop('UPC', axis=1, inplace=True)
        merged_data['ORD'] = merged_data['quantity-purchased']
        # merged_data['link'] = "https://sellercentral.amazon.com/orders-v3/order/"+merged_data['order-id']
        # '''<a href='http://stackoverflow.com'>stackoverflow</a>'''

        # self.amazon_order = merged_data[['inv_comp','inv_store','sku','ORD','quantity-purchased', 'Bin Location', 'product-id', 'ship-service-level', 'DESCRIPTION','order-id', 'purchase-date','link']]
        self.amazon_order = merged_data[['inv_comp','inv_store','sku','ORD','quantity-purchased', 'Bin Location', 'product-id', 'ship-service-level', 'DESCRIPTION','order-id', 'purchase-date','item-name']]

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_amazon_ord.setDisabled(True)

    def save_data(self):
        # self.all_upc_inv.to_csv("all_upc_inv"+datetime.date.today().strftime("%m%d%y")+".csv", index=False)
        self.all_upc_inv.to_excel(self._root_path+"appdata/all_upc_inv.xlsx", index=False)
        self.all_upc_inv.to_excel(self._root_path+"appdata/all_upc_inv_backup.xlsx", index=False)
        self.fromPOS.to_csv(self._root_path+'fromPOS'+datetime.date.today().strftime("%m%d%y")+'.csv', index=False)
        # self.all_amazon.to_csv('all_amazon'+datetime.date.today().strftime("%m%d%y")+'.csv', index=False)
        self.amazon_order.to_excel(self._root_path+'amazon_order'+datetime.date.today().strftime("%m%d%y")+'.xlsx', index=False, freeze_panes=(1,0))
        # self.update_history.to_excel('appdata/update_history.xlsx', index=False)
        self.update_history = pd.read_excel(self._root_path+'appdata/update_history.xlsx')

        try:
            with pd.ExcelWriter(self._root_path+'All_Listings_Report_'+datetime.date.today().strftime("%m_%d_%Y")+'.xlsx') as writer:
                self.all_amazon.to_excel(writer, sheet_name='All_Amazon', index=False, freeze_panes=(3,1))
                self.amazon_order.to_excel(writer, sheet_name='order', index=False, freeze_panes=(1,0))
                self.fromPOS.to_excel(writer, sheet_name='from POS'+datetime.date.today().strftime("%m_%d_%Y"), index=False, freeze_panes=(3,0))
                # self.fromPOS.style.set_properties(format="Comma").to_excel(writer, sheet_name='from POS'+datetime.date.today().strftime("%m_%d_%Y"), index=False, freeze_panes=(3,0))
                self.all_upc_inv.to_excel(writer, sheet_name='all_upc_inv', index=False, freeze_panes=(1,0))
                self.update_history.to_excel(writer, sheet_name='update_history', index=False)
        except:
            print('\033[31m'+f'Error occured while saveing file. Save file as "All_Listings_Report_{datetime.date.today().strftime("%m_%d_%Y")}_new.xlsx"'+'\033[0m')
            with pd.ExcelWriter(self._root_path+'All_Listings_Report_'+datetime.date.today().strftime("%m_%d_%Y")+'_new.xlsx') as writer:
                self.all_amazon.to_excel(writer, sheet_name='All_Amazon', index=False, freeze_panes=(3,1))
                self.amazon_order.to_excel(writer, sheet_name='order', index=False, freeze_panes=(1,0))
                self.fromPOS.to_excel(writer, sheet_name='from POS'+datetime.date.today().strftime("%m_%d_%Y"), index=False, freeze_panes=(3,0))
                # self.fromPOS.style.set_properties(format="Comma").to_excel(writer, sheet_name='from POS'+datetime.date.today().strftime("%m_%d_%Y"), index=False, freeze_panes=(3,0))
                self.all_upc_inv.to_excel(writer, sheet_name='all_upc_inv', index=False, freeze_panes=(1,0))
                self.update_history.to_excel(writer, sheet_name='update_history', index=False)