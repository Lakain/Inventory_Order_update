"""
Data processing service for handling supplier inventory files and data transformations.
Extracted from invUpdateWindow.py various update methods and data processing logic.
"""

import pandas as pd
import datetime
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class DataService:
    """Service for standardized data processing and transformation."""
    
    def __init__(self, root_path: str = ''):
        self.root_path = root_path
        self.column_names = ['COMPAY', 'UPC', 'company Inventory', 'DESCRIPTION', 'EXTENDED DESCRIPTION']
        self._supplier_processors = self._initialize_processors()
    
    def _initialize_processors(self) -> Dict[str, 'SupplierProcessor']:
        """Initialize supplier-specific processors."""
        return {
            'AL': AliciaProcessor(self.root_path, self.column_names),
            'VF': AmekorProcessor(self.root_path, self.column_names),
            'BY': BoyangProcessor(self.root_path, self.column_names),
            'NBF': ChadeProcessor(self.root_path, self.column_names),
            'OUTRE': OutreProcessor(self.root_path, self.column_names),
            'HZ': SensationnelProcessor(self.root_path, self.column_names),
            'SNG': ShakeNGoProcessor(self.root_path, self.column_names),
            'MANE': ManeProcessor(self.root_path, self.column_names)
        }
    
    def load_base_inventory(self) -> pd.DataFrame:
        """
        Load base inventory data.
        Extracted from invUpdateWindow.py load_all_upc_inv() method.
        """
        try:
            all_upc_inv = pd.read_excel(f"{self.root_path}appdata/all_upc_inv.xlsx")
            
            # Delete unnecessary columns (keep only first 5)
            all_upc_inv.drop(all_upc_inv.columns[5:], axis=1, inplace=True)
            
            # Ensure column names match expected format
            all_upc_inv.columns = self.column_names
            
            logger.info(f"Loaded base inventory with {len(all_upc_inv)} records")
            return all_upc_inv
            
        except FileNotFoundError:
            logger.warning("Base inventory file not found, creating empty DataFrame")
            return pd.DataFrame(columns=self.column_names)
        except Exception as e:
            logger.error(f"Error loading base inventory: {e}")
            raise
    
    def process_supplier_file(self, supplier_code: str, file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Process supplier inventory file using supplier-specific processor.
        """
        if supplier_code not in self._supplier_processors:
            raise ValueError(f"Unknown supplier code: {supplier_code}")
        
        processor = self._supplier_processors[supplier_code]
        return processor.process_file(file_path)
    
    def update_supplier_inventory(self, all_inventory: pd.DataFrame, supplier_code: str, 
                                new_data: pd.DataFrame) -> pd.DataFrame:
        """
        Update inventory with new supplier data.
        Extracted from common pattern in update_XX() methods.
        """
        try:
            # Remove existing data for this supplier
            all_inventory.drop(
                all_inventory[all_inventory['COMPAY'] == supplier_code].index, 
                inplace=True
            )
            
            # Append new data
            updated_inventory = pd.concat([all_inventory, new_data], ignore_index=True)
            
            # Reset index
            updated_inventory.reset_index(drop=True, inplace=True)
            
            logger.info(f"Updated inventory for {supplier_code}: {len(new_data)} records")
            return updated_inventory
            
        except Exception as e:
            logger.error(f"Error updating supplier inventory for {supplier_code}: {e}")
            raise
    
    def update_backorder_items(self, all_inventory: pd.DataFrame) -> pd.DataFrame:
        """
        Update backorder items to zero inventory.
        Extracted from invUpdateWindow.py update_backord() method.
        """
        try:
            backorder_list = pd.read_excel(
                f'{self.root_path}appdata/backorder_list.xlsx', 
                dtype={'upc': str}
            )
            
            # Ensure UPC columns are strings for comparison
            all_inventory['UPC'] = all_inventory['UPC'].astype(str)
            all_inventory['DESCRIPTION'] = all_inventory['DESCRIPTION'].astype(str)
            all_inventory['EXTENDED DESCRIPTION'] = all_inventory['EXTENDED DESCRIPTION'].astype(str)
            
            # Set inventory to 0 for backorder items
            backorder_mask = all_inventory["UPC"].isin(backorder_list['upc'])
            all_inventory.loc[backorder_mask, "company Inventory"] = 0
            
            backorder_count = backorder_mask.sum()
            logger.info(f"Updated {backorder_count} backorder items")
            
            return all_inventory
            
        except FileNotFoundError:
            logger.warning("Backorder list file not found, skipping backorder update")
            return all_inventory
        except Exception as e:
            logger.error(f"Error updating backorder items: {e}")
            return all_inventory
    
    def remove_duplicate_items(self, all_inventory: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate items from inventory.
        Extracted from invUpdateWindow.py update_duplicate() method.
        """
        try:
            duplicate_list = pd.read_excel(
                f'{self.root_path}appdata/duplicate_list.xlsx',
                dtype={'UPC': str, 'DESCRIPTION': str, 'EXTENDED DESCRIPTION': str}
            )
            
            # Find duplicate indices
            duplicate_mask = (
                all_inventory['UPC'].isin(duplicate_list['UPC']) &
                all_inventory['DESCRIPTION'].isin(duplicate_list['DESCRIPTION']) &
                all_inventory['EXTENDED DESCRIPTION'].isin(duplicate_list['EXTENDED DESCRIPTION'])
            )
            
            duplicate_indices = all_inventory[duplicate_mask].index
            all_inventory.drop(duplicate_indices, inplace=True)
            
            logger.info(f"Removed {len(duplicate_indices)} duplicate items")
            return all_inventory
            
        except FileNotFoundError:
            logger.warning("Duplicate list file not found, skipping duplicate removal")
            return all_inventory
        except Exception as e:
            logger.error(f"Error removing duplicate items: {e}")
            return all_inventory
    
    def process_amazon_listings(self, all_inventory: pd.DataFrame, pos_data: pd.DataFrame) -> pd.DataFrame:
        """
        Process Amazon listings with inventory data.
        Extracted from invUpdateWindow.py update_amazon() method.
        """
        try:
            # Load Amazon listings report
            all_amazon = pd.read_csv(
                f'{self.root_path}inv_data/Amazon_All+Listings+Report.txt', 
                sep='\t'
            )
            
            # Select relevant columns
            amazon_columns = [
                'seller-sku', 'asin1', 'item-name', 'item-description', 'listing-id',
                'price', 'quantity', 'open-date', 'product-id-type', 'item-note',
                'item-condition', 'will-ship-internationally', 'expedited-shipping',
                'product-id', 'pending-quantity', 'fulfillment-channel', 'status'
            ]
            all_amazon = all_amazon[amazon_columns]
            
            # Initialize inventory columns
            all_amazon['product-id'] = all_amazon['product-id'].astype(str)
            all_amazon['inv_Sum'] = 0
            all_amazon['inv_comp'] = 0
            all_amazon['inv_store'] = 0
            
            # Merge company inventory
            comp_inv_data = all_inventory[['UPC', 'company Inventory']].rename(
                columns={'UPC': 'product-id'}
            )
            comp_inv_data['product-id'] = comp_inv_data['product-id'].astype(str)
            
            all_amazon = all_amazon.merge(comp_inv_data, how='left', on='product-id')
            all_amazon['inv_comp'] = all_amazon['company Inventory'].fillna(0).astype(int)
            all_amazon.drop('company Inventory', axis=1, inplace=True)
            
            # Merge store inventory
            store_inv_data = pos_data[['Item Lookup Code', 'FIN QTY']].rename(
                columns={'Item Lookup Code': 'product-id'}
            )
            store_inv_data['product-id'] = store_inv_data['product-id'].astype(str)
            
            all_amazon = all_amazon.merge(store_inv_data, how='left', on='product-id')
            all_amazon['inv_store'] = all_amazon['FIN QTY'].fillna(0).astype(int)
            all_amazon.drop('FIN QTY', axis=1, inplace=True)
            
            # Calculate total inventory
            all_amazon['inv_Sum'] = all_amazon['inv_store'] + all_amazon['inv_comp']
            
            logger.info(f"Processed {len(all_amazon)} Amazon listings")
            return all_amazon
            
        except Exception as e:
            logger.error(f"Error processing Amazon listings: {e}")
            raise
    
    def process_amazon_orders(self, amazon_listings: pd.DataFrame, pos_data: pd.DataFrame, 
                            all_inventory: pd.DataFrame) -> pd.DataFrame:
        """
        Process Amazon unshipped orders.
        Extracted from invUpdateWindow.py update_amazon_ord() method.
        """
        try:
            # Load unshipped orders
            unshipped_data = pd.read_csv(
                f'{self.root_path}inv_data/Amazon_unshipped_report.txt',
                sep='\t',
                dtype={'product-id': str}
            )
            
            # Merge with Amazon listings
            amazon_subset = amazon_listings[['seller-sku', 'inv_comp', 'inv_store', 'product-id', 'item-name']]
            merged_data = unshipped_data.merge(amazon_subset, how='left', left_on='sku', right_on='seller-sku')
            merged_data.drop('seller-sku', axis=1, inplace=True)
            
            # Merge with POS data for bin location
            pos_subset = pos_data[['Item Lookup Code', 'Bin Location']].astype(str)
            merged_data = merged_data.merge(pos_subset, how='left', left_on='product-id', right_on='Item Lookup Code')
            merged_data.drop('Item Lookup Code', axis=1, inplace=True)
            
            # Merge with inventory for description
            inv_subset = all_inventory[['UPC', 'DESCRIPTION']].astype(str)
            merged_data = merged_data.merge(inv_subset, how='left', left_on='product-id', right_on='UPC')
            merged_data.drop('UPC', axis=1, inplace=True)
            
            # Add order quantity column
            merged_data['ORD'] = merged_data['quantity-purchased']
            
            # Select final columns
            final_columns = [
                'inv_comp', 'inv_store', 'sku', 'ORD', 'quantity-purchased',
                'Bin Location', 'product-id', 'ship-service-level', 'DESCRIPTION',
                'order-id', 'purchase-date', 'item-name'
            ]
            
            result = merged_data[final_columns]
            logger.info(f"Processed {len(result)} Amazon orders")
            return result
            
        except Exception as e:
            logger.error(f"Error processing Amazon orders: {e}")
            raise
    
    def save_inventory_data(self, all_inventory: pd.DataFrame, pos_data: pd.DataFrame,
                          amazon_listings: pd.DataFrame, amazon_orders: pd.DataFrame,
                          update_history: pd.DataFrame) -> bool:
        """
        Save all inventory data to files.
        Extracted from invUpdateWindow.py save_data() method.
        """
        try:
            date_str = datetime.date.today().strftime("%m%d%y")
            date_str_long = datetime.date.today().strftime("%m_%d_%Y")
            
            # Save main inventory files
            all_inventory.to_excel(f"{self.root_path}appdata/all_upc_inv.xlsx", index=False)
            all_inventory.to_excel(f"{self.root_path}appdata/all_upc_inv_backup.xlsx", index=False)
            
            # Save POS data
            pos_data.to_csv(f'{self.root_path}fromPOS{date_str}.csv', index=False)
            
            # Save Amazon orders
            amazon_orders.to_excel(
                f'{self.root_path}amazon_order{date_str}.xlsx',
                index=False,
                freeze_panes=(1, 0)
            )
            
            # Save comprehensive Excel file
            excel_path = f'{self.root_path}All_Listings_Report_{date_str_long}.xlsx'
            try:
                with pd.ExcelWriter(excel_path) as writer:
                    amazon_listings.to_excel(writer, sheet_name='All_Amazon', index=False, freeze_panes=(3, 1))
                    amazon_orders.to_excel(writer, sheet_name='order', index=False, freeze_panes=(1, 0))
                    pos_data.to_excel(writer, sheet_name=f'from POS{date_str_long}', index=False, freeze_panes=(3, 0))
                    all_inventory.to_excel(writer, sheet_name='all_upc_inv', index=False, freeze_panes=(1, 0))
                    update_history.to_excel(writer, sheet_name='update_history', index=False)
            except Exception as e:
                # Fallback with different filename
                logger.warning(f"Error saving to {excel_path}, trying alternative filename: {e}")
                excel_path_alt = f'{self.root_path}All_Listings_Report_{date_str_long}_new.xlsx'
                with pd.ExcelWriter(excel_path_alt) as writer:
                    amazon_listings.to_excel(writer, sheet_name='All_Amazon', index=False, freeze_panes=(3, 1))
                    amazon_orders.to_excel(writer, sheet_name='order', index=False, freeze_panes=(1, 0))
                    pos_data.to_excel(writer, sheet_name=f'from POS{date_str_long}', index=False, freeze_panes=(3, 0))
                    all_inventory.to_excel(writer, sheet_name='all_upc_inv', index=False, freeze_panes=(1, 0))
                    update_history.to_excel(writer, sheet_name='update_history', index=False)
            
            logger.info("Successfully saved all inventory data")
            return True
            
        except Exception as e:
            logger.error(f"Error saving inventory data: {e}")
            return False
    
    def validate_data(self, data: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
        """Validate data structure and content."""
        errors = []
        
        # Check required columns
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            errors.append(f"Missing columns: {missing_columns}")
        
        # Check for empty data
        if data.empty:
            errors.append("Data is empty")
        
        # Check for null values in critical columns
        critical_columns = ['UPC', 'company Inventory'] if 'UPC' in data.columns else []
        for col in critical_columns:
            if col in data.columns and data[col].isnull().any():
                errors.append(f"Null values found in critical column: {col}")
        
        return len(errors) == 0, errors
    
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize data."""
        cleaned_data = data.copy()
        
        # Remove leading/trailing whitespace from string columns
        string_columns = cleaned_data.select_dtypes(include=['object']).columns
        for col in string_columns:
            cleaned_data[col] = cleaned_data[col].astype(str).str.strip()
        
        # Handle missing values
        cleaned_data.fillna('', inplace=True)
        
        return cleaned_data


class SupplierProcessor:
    """Base class for supplier-specific data processing."""
    
    def __init__(self, root_path: str, column_names: List[str]):
        self.root_path = root_path
        self.column_names = column_names
    
    def process_file(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Process supplier file and return standardized DataFrame."""
        raise NotImplementedError


class AliciaProcessor(SupplierProcessor):
    """Processor for Alicia (AL) supplier files."""
    
    def process_file(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Process AL inventory files (both brs and regular inv)."""
        try:
            # Load both files
            temp1 = pd.read_excel(f'{self.root_path}inv_data/AL_brs inv.xls')
            temp2 = pd.read_excel(f'{self.root_path}inv_data/AL_inv.xls')
            
            # Combine files
            new_inv = pd.concat([temp1, temp2], ignore_index=True)
            
            # Select and rename columns
            new_inv = new_inv[['AliasItemNo', 'OnHand Customer', 'ItemCode', 'ItemCodeDesc']]
            new_inv.insert(0, 'Company', 'AL')
            new_inv.columns = self.column_names
            
            # Clean data
            new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
            new_inv['company Inventory'] = new_inv['company Inventory'].astype('int')
            
            return new_inv
            
        except Exception as e:
            logger.error(f"Error processing AL files: {e}")
            raise


class AmekorProcessor(SupplierProcessor):
    """Processor for Amekor (VF) supplier files."""
    
    def process_file(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Process VF inventory file."""
        try:
            new_inv = pd.read_excel(f'{self.root_path}inv_data/VF_Inventory.xls', dtype={'Barcode': str})
            
            # Select and rename columns
            new_inv = new_inv[['Barcode', 'On hand', 'Product ID', 'SKU']]
            new_inv.insert(0, 'Company', 'VF')
            
            # Clean barcode data
            new_inv.loc[new_inv['Barcode'].str.isnumeric() == False, 'Barcode'] = pd.NA
            new_inv['Barcode'] = pd.to_numeric(new_inv['Barcode'], downcast='integer')
            
            new_inv.columns = self.column_names
            
            # Clean data
            new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
            new_inv['company Inventory'] = new_inv['company Inventory'].astype('int')
            new_inv['UPC'] = new_inv['UPC'].astype('int64')
            new_inv.loc[new_inv['company Inventory'] < 10, 'company Inventory'] = 0
            
            return new_inv
            
        except Exception as e:
            logger.error(f"Error processing VF file: {e}")
            raise


class BoyangProcessor(SupplierProcessor):
    """Processor for Boyang (BY) supplier files."""
    
    def process_file(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Process BY inventory file."""
        try:
            new_inv = pd.read_excel(f'{self.root_path}inv_data/BY_InventoryListAll.xls', skiprows=3)
            
            # Select and rename columns
            new_inv = new_inv[['Barcode', 'O/H', 'Item Name', 'Color']]
            new_inv.insert(0, 'Company', 'BY')
            new_inv.columns = self.column_names
            
            # Clean data
            new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
            new_inv['company Inventory'] = new_inv['company Inventory'].astype('int')
            new_inv.loc[new_inv['company Inventory'] < 10, 'company Inventory'] = 0
            
            return new_inv
            
        except Exception as e:
            logger.error(f"Error processing BY file: {e}")
            raise


class ChadeProcessor(SupplierProcessor):
    """Processor for Chade (NBF) supplier files."""
    
    def process_file(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Process NBF inventory file."""
        try:
            new_inv = pd.read_excel(f'{self.root_path}inv_data/NBF_Chade Fashions.xlsx')
            
            # Select and rename columns
            new_inv = new_inv[['UPC Code', 'Unnamed: 6', 'No.', 'Description']]
            new_inv.insert(0, 'Company', 'NBF')
            new_inv.columns = self.column_names
            
            # Clean data
            new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
            new_inv[['company Inventory']] = new_inv[['company Inventory']].replace({'A': 20, 'B': 5, 'C': 0, 'X': 0})
            
            return new_inv
            
        except Exception as e:
            logger.error(f"Error processing NBF file: {e}")
            raise


class OutreProcessor(SupplierProcessor):
    """Processor for Outre supplier files."""
    
    def process_file(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Process OUTRE inventory file."""
        try:
            new_inv = pd.read_csv(
                f'{self.root_path}inv_data/OUTRE_StockAvailability.csv',
                sep='\t', encoding='utf_16', on_bad_lines='warn',
                skiprows=[1], skipfooter=1, engine='python'
            )
            
            # Select and rename columns
            new_inv = new_inv[['BARCODE', 'AVAIL', 'ITEM', 'COLOR']]
            new_inv.insert(0, 'Company', 'OUTRE')
            new_inv.columns = self.column_names
            
            # Clean data
            new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
            new_inv[['company Inventory']] = new_inv[['company Inventory']].replace({'Y': 20, 'N': 0})
            
            return new_inv
            
        except Exception as e:
            logger.error(f"Error processing OUTRE file: {e}")
            raise


class SensationnelProcessor(SupplierProcessor):
    """Processor for Sensationnel (HZ) supplier files."""
    
    def process_file(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Process HZ inventory file."""
        try:
            new_inv = pd.read_csv(
                f'{self.root_path}inv_data/HZ_StockAvailability.csv',
                sep='\t', encoding='utf_16', on_bad_lines='warn',
                skiprows=[1], skipfooter=1, engine='python'
            )
            
            # Select and rename columns
            new_inv = new_inv[['BARCODE', 'AVAIL', 'ITEM', 'COLOR']]
            new_inv.insert(0, 'Company', 'HZ')
            new_inv.columns = self.column_names
            
            # Clean data
            new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
            new_inv[['company Inventory']] = new_inv[['company Inventory']].replace({'Y': 20, 'N': 0})
            
            return new_inv
            
        except Exception as e:
            logger.error(f"Error processing HZ file: {e}")
            raise


class ShakeNGoProcessor(SupplierProcessor):
    """Processor for Shake-N-Go (SNG) supplier files."""
    
    def process_file(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Process SNG inventory file."""
        try:
            new_inv = pd.read_excel(f'{self.root_path}inv_data/SNG_inv.xlsx')
            
            # Select and rename columns
            new_inv = new_inv[['Barcode', 'Available', 'Item', 'Descrip']]
            new_inv.insert(0, 'Company', 'SNG')
            new_inv.columns = self.column_names
            
            # Clean data
            new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
            new_inv[['company Inventory']] = new_inv[['company Inventory']].replace({'Y': 20, 'N': 0})
            
            return new_inv
            
        except Exception as e:
            logger.error(f"Error processing SNG file: {e}")
            raise


class ManeProcessor(SupplierProcessor):
    """Processor for Mane supplier files."""
    
    def process_file(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """Process MANE inventory file."""
        try:
            new_inv = pd.read_excel(f'{self.root_path}inv_data/MANE_inv.xlsx', dtype={'Barcode': str})
            
            # Select and rename columns
            new_inv = new_inv[['Barcode', 'AQOH', 'Item', 'Color']]
            new_inv.insert(0, 'Company', 'MANE')
            new_inv.columns = self.column_names
            
            # Clean data
            new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
            new_inv['company Inventory'] = new_inv['company Inventory'].astype('int')
            new_inv['UPC'] = new_inv['UPC'].astype('int64')
            new_inv.loc[new_inv['company Inventory'] < 10, 'company Inventory'] = 0
            
            return new_inv
            
        except Exception as e:
            logger.error(f"Error processing MANE file: {e}")
            raise