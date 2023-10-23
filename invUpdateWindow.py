from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QWidget
import pandas as pd
import datetime
import webbrowser
from inventoryUpdate_ui import Ui_Form

class Worker(QObject):
    finished = Signal()
    task = Signal(str)
    progress = Signal(int)

    def run(self):
        # InvUpdateWindow.start_update(self)
        self.update_history = pd.read_excel('appdata/update_history.xlsx')

        self.task.emit('Loading all_upc_inv')
        InvUpdateWindow.load_all_upc_inv(self)
        self.progress.emit(5)

        self.task.emit('Updating AL inventory')
        InvUpdateWindow.update_AL(self)
        self.progress.emit(10)

        self.task.emit('Updating VF inventory')
        InvUpdateWindow.update_VF(self)
        self.progress.emit(15)

        self.task.emit('Updating BY inventory')
        InvUpdateWindow.update_BY(self)
        self.progress.emit(20)

        self.task.emit('Updating NBF inventory')
        InvUpdateWindow.update_NBF(self)
        self.progress.emit(25)

        self.task.emit('Updating OUTRE inventory')
        InvUpdateWindow.update_OUTRE(self)
        self.progress.emit(30)

        self.task.emit('Updating HZ inventory')
        InvUpdateWindow.update_HZ(self)
        self.progress.emit(35)

        self.task.emit('Updating SNG inventory')
        InvUpdateWindow.update_SNG(self)
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

        self.task.emit('Updating Updating Amazon List')
        InvUpdateWindow.update_amazon(self)
        self.progress.emit(60)

        self.task.emit('Updating Amazon unshipped list')
        InvUpdateWindow.update_amazon_ord(self)
        self.progress.emit(65)

        self.task.emit('Saving inventory data')
        InvUpdateWindow.save_data(self)
        self.progress.emit(100)

        self.task.emit('Done!')
        self.finished.emit()

        self.update_history.to_excel('appdata/update_history.xlsx', index=False)

class InvUpdateWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

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
        self.worker = Worker()
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
        

    def load_all_upc_inv(self):
        # all upc inv import
        # filename = QFileDialog.getOpenFileName(self, "Select File", "./", "Any Files (*)")
        # self.all_upc_inv = pd.read_excel(filename[0], sheet_name=3)
        self.all_upc_inv = pd.read_excel("appdata/all_upc_inv.xlsx")

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
        temp1 = pd.read_excel('inv_data\AL_brs inv.xls')

        # filename = QFileDialog.getOpenFileName(self, "Select File ALICIA (AL) inv", "./", "Any Files (*)")
        # temp2 = pd.read_excel(filename[0])
        temp2 = pd.read_excel('inv_data\AL_inv.xls')

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

        self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")
        
        # QMessageBox.information(self, "Info", "Updated")

        # self.button_AL.setDisabled(True)

    def update_VF(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File AMEKOR (VF)", "./", "Any Files (*)")
        # new_inv = pd.read_excel(filename[0])
        new_inv = pd.read_excel('inv_data\VF_Inventory.xls')

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

        self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_VF.setDisabled(True)

    def update_BY(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File BOYANG (BY)", "./", "Any Files (*)")
        # new_inv = pd.read_excel(filename[0], skiprows=3)
        new_inv = pd.read_excel('inv_data\BY_InventoryListAll.xls', skiprows=3)

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

        self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_BY.setDisabled(True)

    def update_NBF(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File CHADE (NBF)", "./", "Any Files (*)")
        # new_inv = pd.read_excel(filename[0])
        new_inv = pd.read_excel('inv_data/NBF_Chade Fashions.xlsx')

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

        self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_NBF.setDisabled(True)

    def update_OUTRE(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File SUN TAIYANG (OUTRE)", "./", "Any Files (*)")
        # new_inv = pd.read_csv(filename[0], sep='\t', encoding='utf_16', on_bad_lines='warn', skiprows=[1], skipfooter=1)
        new_inv = pd.read_csv('inv_data\OUTRE_StockAvailability.csv', sep='\t', encoding='utf_16', on_bad_lines='warn', skiprows=[1], skipfooter=1)

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

        self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_OUTRE.setDisabled(True)

    def update_HZ(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File SENSATIONNEL (HZ)", "./", "Any Files (*)")
        # new_inv = pd.read_csv(filename[0], sep='\t', encoding='utf_16', on_bad_lines='warn', skiprows=[1], skipfooter=1)
        new_inv = pd.read_csv('inv_data\HZ_StockAvailability.csv', sep='\t', encoding='utf_16', on_bad_lines='warn', skiprows=[1], skipfooter=1)

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

        self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_HZ.setDisabled(True)

    def update_SNG(self):
        # load new inv data
        # filename = QFileDialog.getOpenFileName(self, "Select File SHAKE-N-GO (SNG)", "./", "Any Files (*)")
        # new_inv = pd.read_excel(filename[0])
        new_inv = pd.read_excel('inv_data\SNG_inv.xlsx')

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

        self.update_history.loc[self.update_history['Initial']==comp_name, 'Date'] = datetime.date.today().strftime("%d-%b")

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_SNG.setDisabled(True)

    def update_backord(self):
        # filename = QFileDialog.getOpenFileName(self, "Select File backorded_list", "./", "Any Files (*)")
        # backorder_list = pd.read_csv(filename[0], dtype={'upc':str})
        backorder_list = pd.read_excel('appdata/backorder_list.xlsx', dtype={'upc':str})
        self.all_upc_inv['UPC'] = self.all_upc_inv['UPC'].astype(str)
        self.all_upc_inv['DESCRIPTION'] = self.all_upc_inv['DESCRIPTION'].astype(str)
        self.all_upc_inv['EXTENDED DESCRIPTION'] = self.all_upc_inv['EXTENDED DESCRIPTION'].astype(str)
        self.all_upc_inv.loc[self.all_upc_inv["UPC"].isin(backorder_list['upc']) , "company Inventory"] = 0
        self.all_upc_inv[self.all_upc_inv['UPC'].isin(backorder_list['upc'])]

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_backord.setDisabled(True)

    def update_duplicate(self):
        # filename = QFileDialog.getOpenFileName(self, "Select File dulplicate_list", "./", "Any Files (*)")
        # duplicate_list = pd.read_csv(filename[0], dtype={'UPC': str, 'DESCRIPTION':str,'EXTENDED DESCRIPTION':str})
        duplicate_list = pd.read_excel('appdata/duplicate_list.xlsx', dtype={'UPC': str, 'DESCRIPTION':str,'EXTENDED DESCRIPTION':str})

        duplicate_index = self.all_upc_inv[(self.all_upc_inv['UPC'].isin(duplicate_list['UPC'])&(self.all_upc_inv['DESCRIPTION'].isin(duplicate_list['DESCRIPTION'])&(self.all_upc_inv['EXTENDED DESCRIPTION'].isin(duplicate_list['EXTENDED DESCRIPTION']))))].index
        self.all_upc_inv.drop(duplicate_index, inplace=True)

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_dup.setDisabled(True)

    def update_POS(self):
        # filename = QFileDialog.getOpenFileName(self, "Select File POS", "./", "Any Files (*)")
        # fromPOS = pd.read_excel(filename[0])
        fromPOS = pd.read_excel('inv_data\POS.xls')

        # save column name for future use
        column_name = fromPOS.columns

        fromPOS['Display'].fillna('0', inplace=True)

        fromPOS['Display'].replace(regex=['\(.\)'], value='', inplace=True)

        fromPOS['Display'] = fromPOS['Display'].str.strip()

        fromPOS.loc[fromPOS['Display'].str.startswith('0'), 'Display'] = '0'
        fromPOS.loc[fromPOS['Display'].str.startswith('S'), 'Display'] = '0'
        fromPOS.loc[fromPOS['Display'].str.startswith('C'), 'Display'] = '0'
        fromPOS.loc[fromPOS['Display']=='', 'Display'] = '0'

        fromPOS['Display'] = fromPOS['Display'].astype(int)

        fromPOS['A'] = ''

        fromPOS['FIN QTY'] = fromPOS['Qty On Hand']-fromPOS['Display']
        fromPOS.loc[fromPOS['FIN QTY']<0, 'FIN QTY'] = 0

        # update comp inv
        comp_inv_data = self.all_upc_inv[['UPC', 'company Inventory']].rename(columns={'UPC': 'Item Lookup Code'})

        fromPOS['Item Lookup Code'] = fromPOS['Item Lookup Code'].astype(str)
        comp_inv_data['Item Lookup Code'] = comp_inv_data['Item Lookup Code'].astype(str)

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
        all_amazon = pd.read_csv('inv_data\Amazon_All+Listings+Report.txt', sep='\t')
        all_amazon['product-id'] = all_amazon['product-id'].astype(str)
        all_amazon['inv_Sum'] = 0
        all_amazon['inv_comp'] = 0
        all_amazon['inv_store'] = 0

        # merge comp inv
        all_upc_inv = self.all_upc_inv

        comp_inv_data = all_upc_inv[['UPC', 'company Inventory']].rename(columns={'UPC': 'product-id'})
        comp_inv_data['product-id'] = comp_inv_data['product-id'].astype(str)

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
        unshipped_data = pd.read_csv('inv_data\Amazon_unshipped_report.txt', sep='\t', dtype={'product-id':str})

        all_amazon = self.all_amazon[['seller-sku', 'inv_comp', 'inv_store', 'product-id']]

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
        merged_data['link'] = "https://sellercentral.amazon.com/orders-v3/order/"+merged_data['order-id']
        # '''<a href='http://stackoverflow.com'>stackoverflow</a>'''

        self.amazon_order = merged_data[['inv_comp','inv_store','sku','ORD','quantity-purchased', 'Bin Location', 'product-id', 'ship-service-level', 'DESCRIPTION','order-id', 'purchase-date','link']]

        # QMessageBox.information(self, "Info", "Updated")
        # self.button_amazon_ord.setDisabled(True)

    def save_data(self):
        # self.all_upc_inv.to_csv("all_upc_inv"+datetime.date.today().strftime("%m%d%y")+".csv", index=False)
        self.all_upc_inv.to_excel("appdata/all_upc_inv.xlsx", index=False)
        self.all_upc_inv.to_excel("appdata/all_upc_inv_backup.xlsx", index=False)
        self.fromPOS.to_csv('fromPOS'+datetime.date.today().strftime("%m%d%y")+'.csv', index=False)
        # self.all_amazon.to_csv('all_amazon'+datetime.date.today().strftime("%m%d%y")+'.csv', index=False)
        self.amazon_order.to_csv('amazon_order'+datetime.date.today().strftime("%m%d%y")+'.csv', index=False)
        # self.update_history.to_excel('appdata/update_history.xlsx', index=False)
        self.update_history = pd.read_excel('appdata/update_history.xlsx')

        with pd.ExcelWriter('All_Listings_Report_'+datetime.date.today().strftime("%m_%d_%Y")+'.xlsx') as writer:
            self.all_amazon.to_excel(writer, sheet_name='All_Amazon', index=False)
            self.amazon_order.to_excel(writer, sheet_name='order', index=False)
            self.fromPOS.to_excel(writer, sheet_name='from POS'+datetime.date.today().strftime("%m_%d_%Y"), index=False)
            self.all_upc_inv.to_excel(writer, sheet_name='all_upc_inv', index=False)
            self.update_history.to_excel(writer, sheet_name='update_history', index=False)

        # QMessageBox.information(self, "Info", "Saved")
