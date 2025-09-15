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
        Includes validation and standardization.
        """
        if supplier_code not in self._supplier_processors:
            raise ValueError(f"Unknown supplier code: {supplier_code}")
        
        try:
            # Process file using supplier-specific processor
            processor = self._supplier_processors[supplier_code]
            processed_data = processor.process_file(file_path)
            
            # Apply additional standardization
            processed_data = self.standardize_supplier_data(processed_data, supplier_code)
            
            # Clean the data
            processed_data = self.clean_data(processed_data)
            
            # Validate the processed data
            is_valid, errors = self.validate_data(processed_data, self.column_names)
            if not is_valid:
                logger.warning(f"Data validation issues for {supplier_code}: {errors}")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing supplier file for {supplier_code}: {e}")
            raise
    
    def transform_data_types(self, data: pd.DataFrame, type_mappings: Dict[str, str]) -> pd.DataFrame:
        """
        Transform data types based on mapping specifications.
        Handles common data type conversions from original code.
        """
        transformed_data = data.copy()
        
        for column, target_type in type_mappings.items():
            if column not in transformed_data.columns:
                continue
                
            try:
                if target_type == 'string':
                    transformed_data[column] = transformed_data[column].astype(str)
                elif target_type == 'int':
                    transformed_data[column] = pd.to_numeric(
                        transformed_data[column], errors='coerce'
                    ).fillna(0).astype(int)
                elif target_type == 'int64':
                    transformed_data[column] = pd.to_numeric(
                        transformed_data[column], errors='coerce'
                    ).fillna(0).astype('int64')
                elif target_type == 'float':
                    transformed_data[column] = pd.to_numeric(
                        transformed_data[column], errors='coerce'
                    ).fillna(0.0)
                elif target_type == 'datetime':
                    transformed_data[column] = pd.to_datetime(
                        transformed_data[column], errors='coerce'
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to convert column {column} to {target_type}: {e}")
        
        return transformed_data
    
    def process_multiple_suppliers(self, supplier_codes: List[str], 
                                 progress_callback: Optional[callable] = None) -> pd.DataFrame:
        """
        Process multiple suppliers and combine their data.
        Useful for batch processing operations.
        """
        all_supplier_data = []
        total_suppliers = len(supplier_codes)
        
        for i, supplier_code in enumerate(supplier_codes):
            try:
                if progress_callback:
                    progress_callback(f"Processing {supplier_code}", i / total_suppliers)
                
                supplier_data = self.process_supplier_file(supplier_code)
                all_supplier_data.append(supplier_data)
                
                logger.info(f"Successfully processed {supplier_code}: {len(supplier_data)} records")
                
            except Exception as e:
                logger.error(f"Failed to process {supplier_code}: {e}")
                # Continue with other suppliers even if one fails
                continue
        
        if not all_supplier_data:
            logger.warning("No supplier data was successfully processed")
            return pd.DataFrame(columns=self.column_names)
        
        # Combine all supplier data
        combined_data = pd.concat(all_supplier_data, ignore_index=True)
        
        if progress_callback:
            progress_callback("Combining supplier data", 1.0)
        
        logger.info(f"Combined data from {len(all_supplier_data)} suppliers: {len(combined_data)} total records")
        return combined_data
    
    def get_supplier_summary(self, data: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Generate summary statistics for each supplier in the dataset.
        """
        if 'COMPAY' not in data.columns:
            return {}
        
        summary = {}
        for supplier in data['COMPAY'].unique():
            supplier_data = data[data['COMPAY'] == supplier]
            summary[supplier] = {
                'record_count': len(supplier_data),
                'unique_upcs': supplier_data['UPC'].nunique() if 'UPC' in data.columns else 0,
                'total_inventory': supplier_data['company Inventory'].sum() if 'company Inventory' in data.columns else 0,
                'avg_inventory': supplier_data['company Inventory'].mean() if 'company Inventory' in data.columns else 0,
                'zero_inventory_items': (supplier_data['company Inventory'] == 0).sum() if 'company Inventory' in data.columns else 0
            }
        
        return summary
    
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
        """
        Validate data structure and content.
        Enhanced validation for supplier inventory data.
        """
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
                null_count = data[col].isnull().sum()
                errors.append(f"Null values found in critical column '{col}': {null_count} records")
        
        # Validate UPC format (should be numeric or convertible to numeric)
        if 'UPC' in data.columns:
            try:
                # Test if UPC can be converted to numeric (allowing for string representation)
                test_upc = pd.to_numeric(data['UPC'], errors='coerce')
                invalid_upc_count = test_upc.isnull().sum()
                if invalid_upc_count > 0:
                    errors.append(f"Invalid UPC format in {invalid_upc_count} records")
            except Exception as e:
                errors.append(f"UPC validation error: {str(e)}")
        
        # Validate inventory quantities (should be non-negative integers)
        if 'company Inventory' in data.columns:
            try:
                non_numeric_inv = pd.to_numeric(data['company Inventory'], errors='coerce').isnull().sum()
                if non_numeric_inv > 0:
                    errors.append(f"Non-numeric inventory values in {non_numeric_inv} records")
                
                # Check for negative inventory values
                numeric_inv = pd.to_numeric(data['company Inventory'], errors='coerce')
                negative_inv = (numeric_inv < 0).sum()
                if negative_inv > 0:
                    errors.append(f"Negative inventory values in {negative_inv} records")
            except Exception as e:
                errors.append(f"Inventory validation error: {str(e)}")
        
        return len(errors) == 0, errors
    
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize data.
        Enhanced cleaning based on patterns from original update methods.
        """
        cleaned_data = data.copy()
        
        # Remove leading/trailing whitespace from string columns
        string_columns = cleaned_data.select_dtypes(include=['object']).columns
        for col in string_columns:
            cleaned_data[col] = cleaned_data[col].astype(str).str.strip()
        
        # Handle missing values appropriately by column type
        for col in cleaned_data.columns:
            if col in ['UPC', 'DESCRIPTION', 'EXTENDED DESCRIPTION', 'COMPAY']:
                # String columns - fill with empty string
                cleaned_data[col] = cleaned_data[col].fillna('')
            elif col == 'company Inventory':
                # Inventory column - fill with 0
                cleaned_data[col] = cleaned_data[col].fillna(0)
        
        # Standardize UPC format (ensure consistent string representation)
        if 'UPC' in cleaned_data.columns:
            # Convert to string, removing any decimal points from float representation
            cleaned_data['UPC'] = cleaned_data['UPC'].astype(str).str.replace('.0', '', regex=False)
        
        # Standardize inventory values
        if 'company Inventory' in cleaned_data.columns:
            # Ensure inventory is numeric and non-negative
            cleaned_data['company Inventory'] = pd.to_numeric(
                cleaned_data['company Inventory'], errors='coerce'
            ).fillna(0).astype(int)
            # Set negative values to 0
            cleaned_data.loc[cleaned_data['company Inventory'] < 0, 'company Inventory'] = 0
        
        return cleaned_data
    
    def standardize_supplier_data(self, data: pd.DataFrame, supplier_code: str) -> pd.DataFrame:
        """
        Apply supplier-specific data standardization rules.
        Extracted from common patterns in update_XX() methods.
        """
        standardized_data = data.copy()
        
        # Apply supplier-specific rules based on original logic
        if supplier_code in ['VF', 'BY', 'MANE']:
            # These suppliers set inventory to 0 if less than 10
            mask = standardized_data['company Inventory'] < 10
            standardized_data.loc[mask, 'company Inventory'] = 0
        
        elif supplier_code == 'NBF':
            # NBF uses letter codes for inventory levels
            inventory_mapping = {'A': 20, 'B': 5, 'C': 0, 'X': 0}
            standardized_data['company Inventory'] = standardized_data['company Inventory'].replace(inventory_mapping).infer_objects(copy=False)
        
        elif supplier_code in ['OUTRE', 'HZ', 'SNG']:
            # These suppliers use Y/N for availability
            availability_mapping = {'Y': 20, 'N': 0}
            standardized_data['company Inventory'] = standardized_data['company Inventory'].replace(availability_mapping).infer_objects(copy=False)
        
        return standardized_data
    
    def process_pos_data(self, pos_data: pd.DataFrame, all_inventory: pd.DataFrame) -> pd.DataFrame:
        """
        Process POS data with inventory integration.
        Extracted from invUpdateWindow.py update_POS() method.
        """
        try:
            # Fill missing values - exact pattern from original
            pos_data.fillna('', inplace=True)
            
            # Process Display column - exact logic from original
            pos_data['Display'] = pos_data['Display'].str.strip()
            
            # Handle parenthetical expressions in Display column
            index = pos_data.loc[pos_data['Display'].str.contains(r'\(\d*\)', regex=True)].index
            pos_data.loc[index, 'Display'] = pos_data.loc[index, 'Display'].str.replace('(', ' ').str.strip(')').str.split()
            
            for i in index:
                try:
                    pos_data.loc[i, 'Display'] = str(sum([eval(a) for a in pos_data.loc[i, 'Display']]))
                except:
                    pos_data.loc[i, 'Display'] = '0'
            
            # Handle empty Display values
            pos_data.loc[pos_data['Display'] == '', 'Display'] = '0'
            pos_data['Display'] = pos_data['Display'].astype(int)
            
            # Add empty column A (from original pattern)
            pos_data['A'] = ''
            
            # Calculate FIN QTY - exact formula from original
            pos_data['FIN QTY'] = pos_data['Qty On Hand'] + pos_data['Display']
            
            # Merge company inventory data - exact pattern from original
            comp_inv_data = all_inventory[['UPC', 'company Inventory']].rename(
                columns={'UPC': 'Item Lookup Code'}
            )
            
            pos_data['Item Lookup Code'] = pos_data['Item Lookup Code'].astype(str)
            comp_inv_data['Item Lookup Code'] = comp_inv_data['Item Lookup Code'].astype(str)
            
            # Get today's date for column naming
            date_str = datetime.date.today().strftime("%m%d")
            comp_inv_col = f'Comp Inv {date_str}'
            
            # Merge and fill missing values
            merged_comp_inv = pos_data.merge(comp_inv_data, how='left', on='Item Lookup Code')['company Inventory']
            pos_data[comp_inv_col] = merged_comp_inv.fillna(0)
            
            logger.info(f"Processed POS data: {len(pos_data)} records")
            return pos_data
            
        except Exception as e:
            logger.error(f"Error processing POS data: {e}")
            raise
    
    def get_data_quality_report(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a data quality report for processed inventory data.
        """
        report = {
            'total_records': len(data),
            'columns': list(data.columns),
            'missing_values': data.isnull().sum().to_dict(),
            'data_types': data.dtypes.to_dict(),
        }
        
        # Add specific checks for inventory data
        if 'UPC' in data.columns:
            report['unique_upcs'] = data['UPC'].nunique()
            report['duplicate_upcs'] = len(data) - data['UPC'].nunique()
        
        if 'company Inventory' in data.columns:
            report['inventory_stats'] = {
                'min': data['company Inventory'].min(),
                'max': data['company Inventory'].max(),
                'mean': data['company Inventory'].mean(),
                'zero_inventory_count': (data['company Inventory'] == 0).sum()
            }
        
        if 'COMPAY' in data.columns:
            report['suppliers'] = data['COMPAY'].value_counts().to_dict()
        
        return report


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
        """
        Process AL inventory files (both brs and regular inv).
        Extracted from invUpdateWindow.py update_AL() method.
        """
        try:
            # Load both files - exact pattern from original code
            temp1 = pd.read_excel(f'{self.root_path}inv_data/AL_brs inv.xls')
            temp2 = pd.read_excel(f'{self.root_path}inv_data/AL_inv.xls')
            
            # Combine files
            new_inv = pd.concat([temp1, temp2], ignore_index=True)
            
            # Select and rename columns - exact mapping from original
            new_inv = new_inv[['AliasItemNo', 'OnHand Customer', 'ItemCode', 'ItemCodeDesc']]
            new_inv.insert(0, 'Company', 'AL')
            new_inv.columns = self.column_names
            
            # Pre-processing - exact pattern from original code
            new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
            new_inv['company Inventory'] = new_inv['company Inventory'].astype('int')
            
            logger.info(f"Processed AL inventory: {len(new_inv)} records")
            return new_inv
            
        except Exception as e:
            logger.error(f"Error processing AL files: {e}")
            raise


class AmekorProcessor(SupplierProcessor):
    """Processor for Amekor (VF) supplier files."""
    
    def process_file(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Process VF inventory file.
        Extracted from invUpdateWindow.py update_VF() method.
        """
        try:
            # Load file with specific dtype - exact pattern from original
            new_inv = pd.read_excel(f'{self.root_path}inv_data/VF_Inventory.xls', dtype={'Barcode': str})
            
            # Select and rename columns - exact mapping from original
            new_inv = new_inv[['Barcode', 'On hand', 'Product ID', 'SKU']]
            new_inv.insert(0, 'Company', 'VF')
            
            # Clean barcode data - exact logic from original
            new_inv.loc[new_inv['Barcode'].str.isnumeric() == False, 'Barcode'] = pd.NA
            new_inv['Barcode'] = pd.to_numeric(new_inv['Barcode'], downcast='integer')
            
            new_inv.columns = self.column_names
            
            # Pre-processing - exact pattern from original code
            new_inv = new_inv.dropna(subset=['UPC', 'company Inventory'])
            new_inv['company Inventory'] = new_inv['company Inventory'].astype('int')
            new_inv['UPC'] = new_inv['UPC'].astype('int64')
            new_inv.loc[new_inv['company Inventory'] < 10, 'company Inventory'] = 0
            
            logger.info(f"Processed VF inventory: {len(new_inv)} records")
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