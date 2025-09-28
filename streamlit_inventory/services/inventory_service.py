"""
Inventory service coordinator for orchestrating all inventory update operations.
Extracted from invUpdateWindow.py Worker.run() method and refactored for Streamlit.
"""

import pandas as pd
import datetime
import logging
from typing import Dict, List, Optional, Callable, Any, Tuple
from pathlib import Path
import traceback
from time import sleep

from .email_service import EmailService
from .database_service import DatabaseService
from .amazon_service import AmazonService
from .data_service import DataService

logger = logging.getLogger(__name__)


class InventoryUpdateError(Exception):
    """Custom exception for inventory update errors."""
    pass


class InventoryService:
    """
    Service coordinator for orchestrating all inventory update operations.
    Extracted and refactored from invUpdateWindow.py Worker.run() method.
    
    This class coordinates the entire inventory update workflow:
    1. Load base inventory data
    2. Process each selected supplier
    3. Update backorder and duplicate items
    4. Process Amazon data
    5. Update POS integration
    6. Save all data
    """
    
    def __init__(self, root_path: str = ''):
        self.root_path = root_path
        
        # Initialize service dependencies
        self.email_service = EmailService(root_path)
        self.database_service = DatabaseService(root_path)
        self.amazon_service = AmazonService(root_path)
        self.data_service = DataService(root_path)
        
        # Workflow state
        self.all_upc_inv = None
        self.update_history = None
        self.from_pos = None
        self.all_amazon = None
        self.amazon_order = None
        
        # Progress tracking
        self.current_step = 0
        self.total_steps = 0
        self.progress_callback = None
        
        # Error handling
        self.errors = []
        self.warnings = []
        
        logger.info("InventoryService initialized")
    
    def update_inventory(self, selected_suppliers: Dict[str, bool], 
                        progress_callback: Optional[Callable[[str, float], None]] = None,
                        streamlit_mode: bool = True) -> Dict[str, Any]:
        """
        Main inventory update orchestration method.
        Extracted and refactored from Worker.run() method.
        
        Args:
            selected_suppliers: Dict mapping supplier codes to boolean selection status
            progress_callback: Optional callback for progress updates (message, progress_ratio)
            streamlit_mode: Whether running in Streamlit environment
            
        Returns:
            Dict containing operation results and status information
        """
        self.progress_callback = progress_callback
        self.errors = []
        self.warnings = []
        
        # Calculate total steps for progress tracking
        active_suppliers = [code for code, selected in selected_suppliers.items() if selected]
        self.total_steps = len(active_suppliers) + 8  # suppliers + additional processing steps
        self.current_step = 0
        
        try:
            logger.info(f"Starting inventory update for suppliers: {active_suppliers}")
            
            # Step 1: Initialize Amazon report generation
            self._update_progress("Initializing Amazon report generation", 0.02)
            amazon_report_id = self._initialize_amazon_report()
            
            # Step 2: Load update history
            self._update_progress("Loading update history", 0.05)
            self._load_update_history()
            
            # Step 3: Load base inventory
            self._update_progress("Loading base inventory data", 0.08)
            self._load_base_inventory()
            
            # Step 4: Process each selected supplier
            supplier_results = {}
            for supplier_code in active_suppliers:
                self.current_step += 1
                progress = self.current_step / self.total_steps
                self._update_progress(f"Updating {supplier_code} inventory", progress)
                
                try:
                    result = self._update_supplier_inventory(supplier_code, streamlit_mode)
                    supplier_results[supplier_code] = result
                    logger.info(f"Successfully updated {supplier_code}: {result.get('records', 0)} records")
                except Exception as e:
                    error_msg = f"Failed to update {supplier_code}: {str(e)}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
                    supplier_results[supplier_code] = {'success': False, 'error': str(e)}
            
            # Step 5: Update backorder items
            self.current_step += 1
            self._update_progress("Updating backorder items", self.current_step / self.total_steps)
            self._update_backorder_items()
            
            # Step 6: Remove duplicate items
            self.current_step += 1
            self._update_progress("Removing duplicate items", self.current_step / self.total_steps)
            self._remove_duplicate_items()
            
            # Step 7: Process POS data
            self.current_step += 1
            self._update_progress("Processing POS inventory data", self.current_step / self.total_steps)
            self._process_pos_data()
            
            # Step 8: Complete Amazon report processing
            self.current_step += 1
            self._update_progress("Processing Amazon listings", self.current_step / self.total_steps)
            self._complete_amazon_processing(amazon_report_id)
            
            # Step 9: Process Amazon orders
            self.current_step += 1
            self._update_progress("Processing Amazon orders", self.current_step / self.total_steps)
            self._process_amazon_orders()
            
            # Step 10: Save all data
            self.current_step += 1
            self._update_progress("Saving inventory data", self.current_step / self.total_steps)
            self._save_all_data()
            
            # Final step
            self._update_progress("Inventory update complete!", 1.0)
            
            # Prepare results summary
            results = {
                'success': True,
                'suppliers_processed': len([r for r in supplier_results.values() if r.get('success', False)]),
                'total_suppliers': len(active_suppliers),
                'supplier_results': supplier_results,
                'total_records': len(self.all_upc_inv) if self.all_upc_inv is not None else 0,
                'errors': self.errors,
                'warnings': self.warnings,
                'completion_time': datetime.datetime.now().isoformat()
            }
            
            logger.info(f"Inventory update completed successfully: {results['suppliers_processed']}/{results['total_suppliers']} suppliers processed")
            return results
            
        except Exception as e:
            error_msg = f"Critical error in inventory update: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.errors.append(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'errors': self.errors,
                'warnings': self.warnings,
                'completion_time': datetime.datetime.now().isoformat()
            }
    
    def _update_progress(self, message: str, progress: float):
        """Update progress with callback if available."""
        if self.progress_callback:
            self.progress_callback(message, progress)
        logger.info(f"Progress {progress:.1%}: {message}")
    
    def _initialize_amazon_report(self) -> Optional[str]:
        """Initialize Amazon report generation (non-blocking)."""
        try:
            report_id = self.amazon_service.create_inventory_report()
            if report_id:
                logger.info(f"Amazon report generation started: {report_id}")
                return report_id
            else:
                self.warnings.append("Failed to initialize Amazon report generation")
                return None
        except Exception as e:
            warning_msg = f"Amazon report initialization failed: {str(e)}"
            logger.warning(warning_msg)
            self.warnings.append(warning_msg)
            return None
    
    def _load_update_history(self):
        """Load update history from Excel file."""
        try:
            self.update_history = pd.read_excel(f'{self.root_path}appdata/update_history.xlsx')
            logger.info(f"Loaded update history: {len(self.update_history)} records")
        except FileNotFoundError:
            logger.warning("Update history file not found, creating empty history")
            # Create basic update history structure
            suppliers = ['AL', 'VF', 'BY', 'NBF', 'OUTRE', 'HZ', 'SNG', 'MANE']
            self.update_history = pd.DataFrame({
                'Initial': suppliers,
                'Date': [''] * len(suppliers)
            })
        except Exception as e:
            error_msg = f"Error loading update history: {str(e)}"
            logger.error(error_msg)
            self.warnings.append(error_msg)
            # Create minimal history as fallback
            self.update_history = pd.DataFrame({'Initial': [], 'Date': []})
    
    def _load_base_inventory(self):
        """Load base inventory data."""
        try:
            self.all_upc_inv = self.data_service.load_base_inventory()
            logger.info(f"Loaded base inventory: {len(self.all_upc_inv)} records")
        except Exception as e:
            error_msg = f"Error loading base inventory: {str(e)}"
            logger.error(error_msg)
            raise InventoryUpdateError(error_msg)
    
    def _update_supplier_inventory(self, supplier_code: str, streamlit_mode: bool = True) -> Dict[str, Any]:
        """
        Update inventory for a specific supplier.
        Combines email download and data processing.
        """
        try:
            # Download supplier files via email
            downloaded_files = []
            try:
                downloaded_files = self.email_service.download_supplier_files(
                    supplier_code, 
                    self.update_history,
                    streamlit_mode=streamlit_mode
                )
                logger.info(f"Downloaded {len(downloaded_files)} files for {supplier_code}")
            except Exception as e:
                warning_msg = f"Email download failed for {supplier_code}: {str(e)}"
                logger.warning(warning_msg)
                self.warnings.append(warning_msg)
                # Continue with existing files if email fails
            
            # Process supplier data
            try:
                new_data = self.data_service.process_supplier_file(supplier_code)
                
                # Update main inventory with new supplier data
                self.all_upc_inv = self.data_service.update_supplier_inventory(
                    self.all_upc_inv, supplier_code, new_data
                )
                
                return {
                    'success': True,
                    'records': len(new_data),
                    'files_downloaded': len(downloaded_files),
                    'downloaded_files': downloaded_files
                }
                
            except Exception as e:
                error_msg = f"Data processing failed for {supplier_code}: {str(e)}"
                logger.error(error_msg)
                raise InventoryUpdateError(error_msg)
                
        except Exception as e:
            logger.error(f"Supplier update failed for {supplier_code}: {str(e)}")
            raise
    
    def process_supplier_inventory(self, supplier_code: str, uploaded_file_path: Optional[str] = None, 
                                 streamlit_mode: bool = True) -> Dict[str, Any]:
        """
        Process inventory for a specific supplier with manual file upload support.
        
        Args:
            supplier_code: Supplier code (AL, VF, BY, NBF, OUTRE, HZ, SNG, MANE)
            uploaded_file_path: Optional path to manually uploaded file
            streamlit_mode: Whether running in Streamlit environment
            
        Returns:
            Dict containing processing results and status information
        """
        try:
            logger.info(f"Processing supplier inventory for {supplier_code}")
            
            # Initialize base inventory if not loaded
            if self.all_upc_inv is None:
                self._load_base_inventory()
            
            downloaded_files = []
            processing_source = "email"
            
            # Try email download first if no manual file provided
            if uploaded_file_path is None:
                try:
                    downloaded_files = self.email_service.download_supplier_files(
                        supplier_code, 
                        self.update_history,
                        streamlit_mode=streamlit_mode
                    )
                    logger.info(f"Downloaded {len(downloaded_files)} files for {supplier_code}")
                except Exception as e:
                    warning_msg = f"Email download failed for {supplier_code}: {str(e)}"
                    logger.warning(warning_msg)
                    self.warnings.append(warning_msg)
                    processing_source = "existing_files"
            else:
                # Use manually uploaded file
                processing_source = "manual_upload"
                logger.info(f"Using manually uploaded file for {supplier_code}: {uploaded_file_path}")
            
            # Process supplier data
            try:
                new_data = self.data_service.process_supplier_file(supplier_code, uploaded_file_path)
                
                # Validate processed data
                is_valid, validation_errors = self.data_service.validate_data(
                    new_data, self.data_service.column_names
                )
                
                if not is_valid:
                    warning_msg = f"Data validation issues for {supplier_code}: {validation_errors}"
                    logger.warning(warning_msg)
                    self.warnings.extend(validation_errors)
                
                # Update main inventory with new supplier data
                original_count = len(self.all_upc_inv)
                self.all_upc_inv = self.data_service.update_supplier_inventory(
                    self.all_upc_inv, supplier_code, new_data
                )
                
                # Apply supplier-specific post-processing
                self._apply_supplier_post_processing(supplier_code, new_data)
                
                return {
                    'success': True,
                    'supplier_code': supplier_code,
                    'records_processed': len(new_data),
                    'total_inventory_records': len(self.all_upc_inv),
                    'records_added': len(self.all_upc_inv) - original_count + len(new_data),
                    'files_downloaded': len(downloaded_files),
                    'downloaded_files': downloaded_files,
                    'processing_source': processing_source,
                    'validation_warnings': validation_errors if not is_valid else [],
                    'data_quality': self.data_service.get_data_quality_report(new_data)
                }
                
            except Exception as e:
                error_msg = f"Data processing failed for {supplier_code}: {str(e)}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'supplier_code': supplier_code,
                    'error': error_msg,
                    'processing_source': processing_source
                }
                
        except Exception as e:
            error_msg = f"Supplier processing failed for {supplier_code}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'supplier_code': supplier_code,
                'error': error_msg
            }
    
    def process_multiple_suppliers(self, supplier_selections: Dict[str, bool], 
                                 uploaded_files: Optional[Dict[str, str]] = None,
                                 progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Any]:
        """
        Process multiple suppliers with individual file upload support.
        
        Args:
            supplier_selections: Dict mapping supplier codes to selection status
            uploaded_files: Optional dict mapping supplier codes to uploaded file paths
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict containing results for all processed suppliers
        """
        try:
            # Initialize base inventory if not loaded
            if self.all_upc_inv is None:
                self._load_base_inventory()
            
            active_suppliers = [code for code, selected in supplier_selections.items() if selected]
            total_suppliers = len(active_suppliers)
            
            if total_suppliers == 0:
                return {
                    'success': True,
                    'message': 'No suppliers selected for processing',
                    'supplier_results': {}
                }
            
            supplier_results = {}
            successful_suppliers = 0
            
            logger.info(f"Processing {total_suppliers} suppliers: {active_suppliers}")
            
            for i, supplier_code in enumerate(active_suppliers):
                try:
                    # Update progress
                    progress = i / total_suppliers
                    if progress_callback:
                        progress_callback(f"Processing {supplier_code} inventory", progress)
                    
                    # Get uploaded file path if provided
                    uploaded_file = uploaded_files.get(supplier_code) if uploaded_files else None
                    
                    # Process supplier
                    result = self.process_supplier_inventory(
                        supplier_code, 
                        uploaded_file_path=uploaded_file,
                        streamlit_mode=True
                    )
                    
                    supplier_results[supplier_code] = result
                    
                    if result['success']:
                        successful_suppliers += 1
                        logger.info(f"Successfully processed {supplier_code}: {result.get('records_processed', 0)} records")
                    else:
                        logger.error(f"Failed to process {supplier_code}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    error_msg = f"Unexpected error processing {supplier_code}: {str(e)}"
                    logger.error(error_msg)
                    supplier_results[supplier_code] = {
                        'success': False,
                        'supplier_code': supplier_code,
                        'error': error_msg
                    }
            
            # Final progress update
            if progress_callback:
                progress_callback("Supplier processing complete", 1.0)
            
            # Apply post-processing operations
            self._apply_inventory_post_processing()
            
            return {
                'success': True,
                'suppliers_processed': successful_suppliers,
                'total_suppliers': total_suppliers,
                'supplier_results': supplier_results,
                'total_inventory_records': len(self.all_upc_inv) if self.all_upc_inv is not None else 0,
                'completion_time': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Multiple supplier processing failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'supplier_results': supplier_results if 'supplier_results' in locals() else {}
            }
    
    def _apply_supplier_post_processing(self, supplier_code: str, new_data: pd.DataFrame):
        """Apply supplier-specific post-processing rules."""
        try:
            # Update history with current date
            if self.update_history is not None:
                current_date = datetime.date.today().strftime("%m/%d/%Y")
                mask = self.update_history['Initial'] == supplier_code
                if mask.any():
                    self.update_history.loc[mask, 'Date'] = current_date
                else:
                    # Add new supplier to history
                    new_row = pd.DataFrame({'Initial': [supplier_code], 'Date': [current_date]})
                    self.update_history = pd.concat([self.update_history, new_row], ignore_index=True)
                
                logger.info(f"Updated history for {supplier_code}")
            
        except Exception as e:
            warning_msg = f"Post-processing failed for {supplier_code}: {str(e)}"
            logger.warning(warning_msg)
            self.warnings.append(warning_msg)
    
    def _apply_inventory_post_processing(self):
        """Apply inventory-wide post-processing operations."""
        try:
            if self.all_upc_inv is None:
                return
            
            original_count = len(self.all_upc_inv)
            
            # Update backorder items
            logger.info("Applying backorder updates")
            self.all_upc_inv = self.data_service.update_backorder_items(self.all_upc_inv)
            
            # Remove duplicate items
            logger.info("Removing duplicate items")
            self.all_upc_inv = self.data_service.remove_duplicate_items(self.all_upc_inv)
            
            final_count = len(self.all_upc_inv)
            removed_count = original_count - final_count
            
            if removed_count > 0:
                logger.info(f"Post-processing removed {removed_count} items (backorders/duplicates)")
            
        except Exception as e:
            warning_msg = f"Inventory post-processing failed: {str(e)}"
            logger.warning(warning_msg)
            self.warnings.append(warning_msg)
    
    def merge_inventory_data(self, primary_data: pd.DataFrame, secondary_data: pd.DataFrame, 
                           merge_strategy: str = 'replace') -> pd.DataFrame:
        """
        Merge inventory data from multiple sources with configurable strategy.
        
        Args:
            primary_data: Primary inventory DataFrame
            secondary_data: Secondary inventory DataFrame to merge
            merge_strategy: 'replace', 'add', or 'max' for handling duplicate UPCs
            
        Returns:
            Merged DataFrame
        """
        try:
            if primary_data.empty:
                return secondary_data.copy()
            
            if secondary_data.empty:
                return primary_data.copy()
            
            # Ensure both DataFrames have the same columns
            common_columns = list(set(primary_data.columns) & set(secondary_data.columns))
            if not common_columns:
                logger.warning("No common columns found for merging")
                return primary_data
            
            primary_subset = primary_data[common_columns].copy()
            secondary_subset = secondary_data[common_columns].copy()
            
            # Handle merge based on strategy
            if merge_strategy == 'replace':
                # Remove existing records for suppliers in secondary data
                if 'COMPAY' in common_columns:
                    suppliers_to_replace = secondary_subset['COMPAY'].unique()
                    mask = ~primary_subset['COMPAY'].isin(suppliers_to_replace)
                    merged_data = pd.concat([primary_subset[mask], secondary_subset], ignore_index=True)
                else:
                    # Simple concatenation if no company column
                    merged_data = pd.concat([primary_subset, secondary_subset], ignore_index=True)
            
            elif merge_strategy == 'add':
                # Add inventory quantities for matching UPCs
                if 'UPC' in common_columns and 'company Inventory' in common_columns:
                    merged_data = primary_subset.merge(
                        secondary_subset[['UPC', 'company Inventory']], 
                        on='UPC', 
                        how='outer', 
                        suffixes=('', '_add')
                    )
                    merged_data['company Inventory'] = (
                        merged_data['company Inventory'].fillna(0) + 
                        merged_data['company Inventory_add'].fillna(0)
                    )
                    merged_data.drop('company Inventory_add', axis=1, inplace=True)
                else:
                    merged_data = pd.concat([primary_subset, secondary_subset], ignore_index=True)
            
            elif merge_strategy == 'max':
                # Take maximum inventory for matching UPCs
                if 'UPC' in common_columns and 'company Inventory' in common_columns:
                    merged_data = primary_subset.merge(
                        secondary_subset[['UPC', 'company Inventory']], 
                        on='UPC', 
                        how='outer', 
                        suffixes=('', '_max')
                    )
                    merged_data['company Inventory'] = np.maximum(
                        merged_data['company Inventory'].fillna(0),
                        merged_data['company Inventory_max'].fillna(0)
                    )
                    merged_data.drop('company Inventory_max', axis=1, inplace=True)
                else:
                    merged_data = pd.concat([primary_subset, secondary_subset], ignore_index=True)
            
            else:
                # Default to simple concatenation
                merged_data = pd.concat([primary_subset, secondary_subset], ignore_index=True)
            
            # Clean and validate merged data
            merged_data = self.data_service.clean_data(merged_data)
            
            logger.info(f"Merged inventory data: {len(primary_data)} + {len(secondary_data)} = {len(merged_data)} records")
            return merged_data
            
        except Exception as e:
            logger.error(f"Error merging inventory data: {e}")
            raise
    
    def deduplicate_inventory(self, data: pd.DataFrame, 
                            dedup_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Remove duplicate inventory records based on specified columns.
        
        Args:
            data: DataFrame to deduplicate
            dedup_columns: Columns to use for deduplication (default: ['UPC', 'COMPAY'])
            
        Returns:
            Deduplicated DataFrame
        """
        try:
            if data.empty:
                return data
            
            if dedup_columns is None:
                dedup_columns = ['UPC', 'COMPAY'] if 'COMPAY' in data.columns else ['UPC']
            
            # Filter to only use columns that exist in the data
            available_columns = [col for col in dedup_columns if col in data.columns]
            
            if not available_columns:
                logger.warning("No deduplication columns found in data")
                return data
            
            original_count = len(data)
            
            # Remove duplicates, keeping the last occurrence (most recent)
            deduplicated_data = data.drop_duplicates(subset=available_columns, keep='last')
            
            removed_count = original_count - len(deduplicated_data)
            
            if removed_count > 0:
                logger.info(f"Removed {removed_count} duplicate records based on {available_columns}")
            
            return deduplicated_data
            
        except Exception as e:
            logger.error(f"Error deduplicating inventory: {e}")
            return data
    
    def handle_backorder_items(self, data: pd.DataFrame, 
                             backorder_action: str = 'zero_inventory') -> pd.DataFrame:
        """
        Handle backorder items according to specified action.
        
        Args:
            data: Inventory DataFrame
            backorder_action: 'zero_inventory', 'remove', or 'flag'
            
        Returns:
            Processed DataFrame
        """
        try:
            if data.empty:
                return data
            
            # Load backorder list
            try:
                backorder_list = pd.read_excel(
                    f'{self.root_path}appdata/backorder_list.xlsx', 
                    dtype={'upc': str}
                )
                
                if 'UPC' not in data.columns:
                    logger.warning("No UPC column found for backorder processing")
                    return data
                
                # Ensure UPC columns are strings for comparison
                data['UPC'] = data['UPC'].astype(str)
                backorder_upcs = set(backorder_list['upc'].astype(str))
                
                # Find backorder items
                backorder_mask = data['UPC'].isin(backorder_upcs)
                backorder_count = backorder_mask.sum()
                
                if backorder_count == 0:
                    logger.info("No backorder items found in inventory")
                    return data
                
                # Apply backorder action
                if backorder_action == 'zero_inventory':
                    if 'company Inventory' in data.columns:
                        data.loc[backorder_mask, 'company Inventory'] = 0
                        logger.info(f"Set inventory to 0 for {backorder_count} backorder items")
                
                elif backorder_action == 'remove':
                    data = data[~backorder_mask]
                    logger.info(f"Removed {backorder_count} backorder items from inventory")
                
                elif backorder_action == 'flag':
                    data['is_backorder'] = backorder_mask
                    logger.info(f"Flagged {backorder_count} backorder items")
                
                return data
                
            except FileNotFoundError:
                logger.warning("Backorder list file not found, skipping backorder processing")
                return data
                
        except Exception as e:
            logger.error(f"Error handling backorder items: {e}")
            return data
    
    def _update_backorder_items(self):
        """Update backorder items to zero inventory."""
        try:
            self.all_upc_inv = self.data_service.update_backorder_items(self.all_upc_inv)
            logger.info("Updated backorder items")
        except Exception as e:
            warning_msg = f"Backorder update failed: {str(e)}"
            logger.warning(warning_msg)
            self.warnings.append(warning_msg)
    
    def _remove_duplicate_items(self):
        """Remove duplicate items from inventory."""
        try:
            original_count = len(self.all_upc_inv)
            self.all_upc_inv = self.data_service.remove_duplicate_items(self.all_upc_inv)
            removed_count = original_count - len(self.all_upc_inv)
            logger.info(f"Removed {removed_count} duplicate items")
        except Exception as e:
            warning_msg = f"Duplicate removal failed: {str(e)}"
            logger.warning(warning_msg)
            self.warnings.append(warning_msg)
    
    def _process_pos_data(self):
        """Process POS inventory data."""
        try:
            # Get POS data from database
            pos_data = self.database_service.get_pos_inventory_data()
            
            # Process POS data with inventory integration
            self.from_pos = self.data_service.process_pos_data(pos_data, self.all_upc_inv)
            
            logger.info(f"Processed POS data: {len(self.from_pos)} records")
            
        except Exception as e:
            error_msg = f"POS data processing failed: {str(e)}"
            logger.error(error_msg)
            raise InventoryUpdateError(error_msg)
    
    def _complete_amazon_processing(self, report_id: Optional[str]):
        """Complete Amazon report processing and generate listings data."""
        try:
            if report_id:
                # Wait for report completion and download
                document_id = self.amazon_service.wait_for_report_completion(report_id, max_wait_time=300)
                if document_id:
                    report_path = f"{self.root_path}inv_data/Amazon_All+Listings+Report.txt"
                    if self.amazon_service.download_report_document(document_id, report_path):
                        logger.info("Amazon report downloaded successfully")
                    else:
                        self.warnings.append("Failed to download Amazon report")
                else:
                    self.warnings.append("Amazon report did not complete in time")
            
            # Process Amazon listings with current inventory data
            if self.from_pos is not None:
                self.all_amazon = self.data_service.process_amazon_listings(
                    self.all_upc_inv, self.from_pos
                )
                logger.info(f"Processed Amazon listings: {len(self.all_amazon)} records")
            else:
                self.warnings.append("Cannot process Amazon listings without POS data")
                
        except Exception as e:
            warning_msg = f"Amazon processing failed: {str(e)}"
            logger.warning(warning_msg)
            self.warnings.append(warning_msg)
    
    def _process_amazon_orders(self):
        """Process Amazon unshipped orders."""
        try:
            if self.all_amazon is not None and self.from_pos is not None:
                self.amazon_order = self.data_service.process_amazon_orders(
                    self.all_amazon, self.from_pos, self.all_upc_inv
                )
                logger.info(f"Processed Amazon orders: {len(self.amazon_order)} records")
            else:
                self.warnings.append("Cannot process Amazon orders without listings and POS data")
                
        except Exception as e:
            warning_msg = f"Amazon order processing failed: {str(e)}"
            logger.warning(warning_msg)
            self.warnings.append(warning_msg)
    
    def _save_all_data(self):
        """Save all processed data to files."""
        try:
            # Update history with current date
            self.update_history.to_excel(f'{self.root_path}appdata/update_history.xlsx', index=False)
            
            # Save all data using data service
            success = self.data_service.save_inventory_data(
                self.all_upc_inv,
                self.from_pos or pd.DataFrame(),
                self.all_amazon or pd.DataFrame(),
                self.amazon_order or pd.DataFrame(),
                self.update_history
            )
            
            if success:
                logger.info("All data saved successfully")
            else:
                self.warnings.append("Some data files may not have been saved correctly")
                
        except Exception as e:
            error_msg = f"Data saving failed: {str(e)}"
            logger.error(error_msg)
            raise InventoryUpdateError(error_msg)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status for all services."""
        try:
            return {
                'email': self.email_service.get_connection_status(),
                'database': self.database_service.get_connection_status(),
                'amazon': self.amazon_service.get_connection_status(),
                'last_check': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'error': str(e),
                'last_check': datetime.datetime.now().isoformat()
            }
    
    def test_all_connections(self) -> Dict[str, bool]:
        """Test all service connections."""
        try:
            return {
                'email': self.email_service.test_connection(),
                'database': self.database_service.test_connection(),
                'amazon': self.amazon_service.test_connection()
            }
        except Exception as e:
            logger.error(f"Error testing connections: {e}")
            return {
                'email': False,
                'database': False,
                'amazon': False
            }
    
    def get_supplier_configs(self) -> Dict[str, Dict]:
        """Get all supplier configurations."""
        try:
            return self.email_service.get_supplier_configs()
        except Exception as e:
            logger.error(f"Error getting supplier configs: {e}")
            return {}
    
    def validate_prerequisites(self) -> Tuple[bool, List[str]]:
        """
        Validate that all prerequisites are met for inventory update.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            # Check if base inventory file exists
            base_inv_path = Path(f"{self.root_path}appdata/all_upc_inv.xlsx")
            if not base_inv_path.exists():
                issues.append("Base inventory file (all_upc_inv.xlsx) not found")
            
            # Test service connections
            connections = self.test_all_connections()
            if not connections.get('database', False):
                issues.append("Database connection failed")
            if not connections.get('email', False):
                issues.append("Email connection failed (manual file upload will be required)")
            if not connections.get('amazon', False):
                issues.append("Amazon API connection failed (Amazon features will be limited)")
            
            # Check for required directories
            inv_data_path = Path(f"{self.root_path}inv_data")
            if not inv_data_path.exists():
                inv_data_path.mkdir(parents=True, exist_ok=True)
                logger.info("Created inv_data directory")
            
            appdata_path = Path(f"{self.root_path}appdata")
            if not appdata_path.exists():
                issues.append("appdata directory not found")
            
            # Check for required configuration files
            required_configs = [
                'appdata/db_auth.json',
                'appdata/gmail_auth.json',
                'appdata/api_keys.json',
                'appdata/keyword_mailadd.json'
            ]
            
            for config_file in required_configs:
                config_path = Path(f"{self.root_path}{config_file}")
                if not config_path.exists():
                    issues.append(f"Configuration file missing: {config_file}")
            
        except Exception as e:
            issues.append(f"Error during prerequisite validation: {str(e)}")
        
        return len(issues) == 0, issues
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get summary of current inventory data."""
        try:
            if self.all_upc_inv is None:
                self.all_upc_inv = self.data_service.load_base_inventory()
            
            return self.data_service.get_supplier_summary(self.all_upc_inv)
        except Exception as e:
            logger.error(f"Error getting inventory summary: {e}")
            return {}
    
    def cleanup_old_files(self, days_old: int = 30) -> int:
        """
        Clean up old generated files to save disk space.
        
        Args:
            days_old: Remove files older than this many days
            
        Returns:
            Number of files removed
        """
        try:
            removed_count = 0
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)
            
            # Patterns for files to clean up
            cleanup_patterns = [
                f"{self.root_path}fromPOS*.csv",
                f"{self.root_path}amazon_order*.xlsx",
                f"{self.root_path}All_Listings_Report_*.xlsx"
            ]
            
            import glob
            for pattern in cleanup_patterns:
                for file_path in glob.glob(pattern):
                    file_path_obj = Path(file_path)
                    if file_path_obj.stat().st_mtime < cutoff_date.timestamp():
                        file_path_obj.unlink()
                        removed_count += 1
                        logger.info(f"Removed old file: {file_path}")
            
            logger.info(f"Cleanup completed: {removed_count} files removed")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error during file cleanup: {e}")
            return 0
    
    def get_last_update_info(self) -> Dict[str, Any]:
        """Get information about the last inventory update."""
        try:
            # Check for most recent generated files
            import glob
            
            # Find most recent all_upc_inv backup
            backup_files = glob.glob(f"{self.root_path}appdata/all_upc_inv_backup.xlsx")
            last_backup = None
            if backup_files:
                backup_path = Path(backup_files[0])
                last_backup = datetime.datetime.fromtimestamp(backup_path.stat().st_mtime)
            
            # Find most recent report file
            report_files = glob.glob(f"{self.root_path}All_Listings_Report_*.xlsx")
            last_report = None
            if report_files:
                # Get the most recent report file
                report_files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
                report_path = Path(report_files[0])
                last_report = datetime.datetime.fromtimestamp(report_path.stat().st_mtime)
            
            # Load update history for supplier dates
            supplier_dates = {}
            try:
                history = pd.read_excel(f'{self.root_path}appdata/update_history.xlsx')
                supplier_dates = dict(zip(history['Initial'], history['Date']))
            except:
                pass
            
            return {
                'last_backup': last_backup.isoformat() if last_backup else None,
                'last_report': last_report.isoformat() if last_report else None,
                'supplier_dates': supplier_dates,
                'check_time': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting last update info: {e}")
            return {'error': str(e)}
    
    def validate_uploaded_file(self, file_path: str, supplier_code: str) -> Tuple[bool, List[str]]:
        """
        Validate an uploaded file for a specific supplier.
        
        Args:
            file_path: Path to the uploaded file
            supplier_code: Supplier code to validate against
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            # Check if file exists
            if not Path(file_path).exists():
                issues.append("File does not exist")
                return False, issues
            
            # Check file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in ['.xlsx', '.xls', '.csv']:
                issues.append(f"Unsupported file format: {file_ext}")
                return False, issues
            
            # Try to load the file
            try:
                if file_ext in ['.xlsx', '.xls']:
                    test_df = pd.read_excel(file_path, nrows=5)  # Just read first few rows for validation
                else:
                    test_df = pd.read_csv(file_path, nrows=5)
                
                if test_df.empty:
                    issues.append("File appears to be empty")
                    return False, issues
                
            except Exception as e:
                issues.append(f"Cannot read file: {str(e)}")
                return False, issues
            
            # Check if supplier processor can handle the file
            try:
                processor = self.data_service._supplier_processors.get(supplier_code)
                if not processor:
                    issues.append(f"No processor available for supplier: {supplier_code}")
                    return False, issues
                
                # Try to detect columns (this will vary by supplier)
                if hasattr(processor, f'_detect_{supplier_code.lower()}_columns'):
                    detect_method = getattr(processor, f'_detect_{supplier_code.lower()}_columns')
                    column_mapping = detect_method(test_df.columns.tolist())
                    if not column_mapping:
                        issues.append(f"Could not identify {supplier_code} file format")
                        return False, issues
                
            except Exception as e:
                issues.append(f"File format validation failed: {str(e)}")
                return False, issues
            
            logger.info(f"File validation passed for {supplier_code}: {file_path}")
            return True, []
            
        except Exception as e:
            issues.append(f"Validation error: {str(e)}")
            return False, issues
    
    def get_supported_file_formats(self, supplier_code: str) -> Dict[str, Any]:
        """
        Get information about supported file formats for a supplier.
        
        Args:
            supplier_code: Supplier code
            
        Returns:
            Dict with format information
        """
        format_info = {
            'AL': {
                'formats': ['.xls', '.xlsx'],
                'expected_columns': ['AliasItemNo', 'OnHand Customer', 'ItemCode', 'ItemCodeDesc'],
                'description': 'Alicia inventory files with UPC, quantity, and description columns'
            },
            'VF': {
                'formats': ['.xls', '.xlsx'],
                'expected_columns': ['Barcode', 'On hand', 'Product ID', 'SKU'],
                'description': 'Amekor inventory files with barcode and stock information'
            },
            'BY': {
                'formats': ['.xls', '.xlsx'],
                'expected_columns': ['Barcode', 'O/H', 'Item Name', 'Color'],
                'description': 'Boyang inventory files (may have header rows to skip)'
            },
            'NBF': {
                'formats': ['.xlsx'],
                'expected_columns': ['UPC Code', 'Unnamed: 6', 'No.', 'Description'],
                'description': 'Chade Fashions files with letter-coded inventory levels (A/B/C/X)'
            },
            'OUTRE': {
                'formats': ['.csv', '.xlsx'],
                'expected_columns': ['BARCODE', 'AVAIL', 'ITEM', 'COLOR'],
                'description': 'Outre files with Y/N availability indicators'
            },
            'HZ': {
                'formats': ['.csv', '.xlsx'],
                'expected_columns': ['BARCODE', 'AVAIL', 'ITEM', 'COLOR'],
                'description': 'Sensationnel files with Y/N availability indicators'
            },
            'SNG': {
                'formats': ['.xlsx'],
                'expected_columns': ['Barcode', 'Available', 'Item', 'Descrip'],
                'description': 'Shake-N-Go files with Y/N availability indicators'
            },
            'MANE': {
                'formats': ['.xlsx'],
                'expected_columns': ['Barcode', 'AQOH', 'Item', 'Color'],
                'description': 'Mane files with numeric quantity values'
            }
        }
        
        return format_info.get(supplier_code, {
            'formats': ['.xlsx', '.xls', '.csv'],
            'expected_columns': [],
            'description': 'Standard inventory file with UPC and quantity columns'
        })
    
    def preview_uploaded_file(self, file_path: str, supplier_code: str, num_rows: int = 10) -> Dict[str, Any]:
        """
        Preview an uploaded file to help users verify the format.
        
        Args:
            file_path: Path to the uploaded file
            supplier_code: Supplier code
            num_rows: Number of rows to preview
            
        Returns:
            Dict with preview information
        """
        try:
            # Load preview data
            file_ext = Path(file_path).suffix.lower()
            if file_ext in ['.xlsx', '.xls']:
                preview_df = pd.read_excel(file_path, nrows=num_rows)
            else:
                preview_df = pd.read_csv(file_path, nrows=num_rows)
            
            # Get column mapping if available
            processor = self.data_service._supplier_processors.get(supplier_code)
            column_mapping = None
            if processor and hasattr(processor, f'_detect_{supplier_code.lower()}_columns'):
                detect_method = getattr(processor, f'_detect_{supplier_code.lower()}_columns')
                column_mapping = detect_method(preview_df.columns.tolist())
            
            return {
                'success': True,
                'columns': preview_df.columns.tolist(),
                'data_types': preview_df.dtypes.to_dict(),
                'sample_data': preview_df.to_dict('records'),
                'total_rows': len(preview_df),
                'column_mapping': column_mapping,
                'file_info': {
                    'size': Path(file_path).stat().st_size,
                    'format': file_ext,
                    'name': Path(file_path).name
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }