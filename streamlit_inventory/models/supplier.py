"""
Supplier-specific data processing models and classes.

This module provides base classes and specific implementations for processing
inventory data from different suppliers based on their unique file formats
and processing requirements.
"""

import pandas as pd
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class InventoryItem:
    """Represents a single inventory item from a supplier."""
    upc: str
    description: str
    extended_description: str
    supplier_code: str
    quantity: int
    last_updated: datetime
    
    def __post_init__(self):
        """Validate inventory item data."""
        if not self.upc:
            raise ValueError("UPC cannot be empty")
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")


@dataclass
class SupplierInventory:
    """Container for all inventory items from a supplier."""
    supplier_code: str
    items: List[InventoryItem]
    last_sync: datetime
    file_sources: List[str]
    
    @property
    def item_count(self) -> int:
        """Get total number of items."""
        return len(self.items)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert inventory items to pandas DataFrame."""
        if not self.items:
            return pd.DataFrame(columns=['COMPAY', 'UPC', 'company Inventory', 'Description', 'Extended Description'])
        
        data = []
        for item in self.items:
            data.append({
                'COMPAY': item.supplier_code,
                'UPC': item.upc,
                'company Inventory': item.quantity,
                'Description': item.description,
                'Extended Description': item.extended_description
            })
        
        return pd.DataFrame(data)


class SupplierProcessor(ABC):
    """Base class for supplier-specific inventory processing."""
    
    def __init__(self, supplier_code: str, config: Dict[str, Any]):
        """
        Initialize supplier processor.
        
        Args:
            supplier_code: Supplier code (e.g., 'AL', 'VF')
            config: Supplier configuration dictionary
        """
        self.supplier_code = supplier_code
        self.config = config
        self.column_mapping = config.get('column_mapping', {})
        self.processing_rules = config.get('processing_rules', {})
        
    @abstractmethod
    def process_files(self, file_paths: List[str]) -> SupplierInventory:
        """
        Process supplier inventory files.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            SupplierInventory object with processed data
        """
        pass
    
    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize DataFrame columns to common format.
        
        Args:
            df: Input DataFrame with supplier-specific columns
            
        Returns:
            DataFrame with standardized columns
        """
        # Extract column mappings
        upc_col = self.column_mapping.get('upc_column')
        inv_col = self.column_mapping.get('inventory_column')
        desc_col = self.column_mapping.get('description_column')
        ext_desc_col = self.column_mapping.get('extended_description_column')
        
        if not all([upc_col, inv_col, desc_col, ext_desc_col]):
            raise ValueError(f"Missing column mappings for supplier {self.supplier_code}")
        
        # Select and rename columns
        try:
            standardized = df[[upc_col, inv_col, desc_col, ext_desc_col]].copy()
            standardized.insert(0, 'Company', self.supplier_code)
            standardized.columns = ['COMPAY', 'UPC', 'company Inventory', 'Description', 'Extended Description']
            
            return standardized
            
        except KeyError as e:
            raise ValueError(f"Column not found in {self.supplier_code} data: {e}")
    
    def _clean_inventory_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate inventory data.
        
        Args:
            df: DataFrame with standardized columns
            
        Returns:
            Cleaned DataFrame
        """
        # Remove rows with missing UPC or inventory
        df = df.dropna(subset=['UPC', 'company Inventory'])
        
        # Apply inventory mapping if specified
        inventory_mapping = self.processing_rules.get('inventory_mapping')
        if inventory_mapping:
            df['company Inventory'] = df['company Inventory'].replace(inventory_mapping)
        
        # Convert inventory to integer if specified
        if self.processing_rules.get('inventory_type') == 'int':
            df['company Inventory'] = df['company Inventory'].astype('int')
        
        return df
    
    def _dataframe_to_inventory_items(self, df: pd.DataFrame) -> List[InventoryItem]:
        """
        Convert DataFrame to list of InventoryItem objects.
        
        Args:
            df: Cleaned DataFrame with standardized columns
            
        Returns:
            List of InventoryItem objects
        """
        items = []
        current_time = datetime.now()
        
        for _, row in df.iterrows():
            try:
                item = InventoryItem(
                    upc=str(row['UPC']),
                    description=str(row['Description']),
                    extended_description=str(row['Extended Description']),
                    supplier_code=self.supplier_code,
                    quantity=int(row['company Inventory']),
                    last_updated=current_time
                )
                items.append(item)
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid item for {self.supplier_code}: {e}")
                continue
        
        return items


class ExcelSupplierProcessor(SupplierProcessor):
    """Processor for suppliers using Excel files."""
    
    def process_files(self, file_paths: List[str]) -> SupplierInventory:
        """Process Excel files for supplier inventory."""
        if not file_paths:
            raise ValueError(f"No files provided for {self.supplier_code}")
        
        dataframes = []
        processed_files = []
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue
            
            try:
                df = pd.read_excel(file_path)
                dataframes.append(df)
                processed_files.append(file_path)
                logger.info(f"Loaded {len(df)} rows from {file_path}")
                
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                continue
        
        if not dataframes:
            raise ValueError(f"No valid files processed for {self.supplier_code}")
        
        # Concatenate if multiple files
        if len(dataframes) > 1 and self.processing_rules.get('concat_files', False):
            combined_df = pd.concat(dataframes, ignore_index=True)
        else:
            combined_df = dataframes[0]
        
        # Standardize and clean data
        standardized_df = self._standardize_dataframe(combined_df)
        cleaned_df = self._clean_inventory_data(standardized_df)
        
        # Convert to inventory items
        items = self._dataframe_to_inventory_items(cleaned_df)
        
        return SupplierInventory(
            supplier_code=self.supplier_code,
            items=items,
            last_sync=datetime.now(),
            file_sources=processed_files
        )


class CSVSupplierProcessor(SupplierProcessor):
    """Processor for suppliers using CSV files."""
    
    def process_files(self, file_paths: List[str]) -> SupplierInventory:
        """Process CSV files for supplier inventory."""
        if not file_paths:
            raise ValueError(f"No files provided for {self.supplier_code}")
        
        file_path = file_paths[0]  # CSV suppliers typically use single files
        
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        try:
            # Get CSV-specific parameters
            separator = self.processing_rules.get('csv_separator', ',')
            encoding = self.config.get('encoding', 'utf-8')
            skiprows = self.processing_rules.get('skiprows', None)
            skipfooter = self.processing_rules.get('skipfooter', 0)
            
            df = pd.read_csv(
                file_path,
                sep=separator,
                encoding=encoding,
                skiprows=skiprows,
                skipfooter=skipfooter,
                engine='python',
                on_bad_lines='warn'
            )
            
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            
        except Exception as e:
            raise ValueError(f"Error reading CSV file {file_path}: {e}")
        
        # Standardize and clean data
        standardized_df = self._standardize_dataframe(df)
        cleaned_df = self._clean_inventory_data(standardized_df)
        
        # Convert to inventory items
        items = self._dataframe_to_inventory_items(cleaned_df)
        
        return SupplierInventory(
            supplier_code=self.supplier_code,
            items=items,
            last_sync=datetime.now(),
            file_sources=[file_path]
        )


class SupplierProcessorFactory:
    """Factory class for creating supplier processors."""
    
    @staticmethod
    def create_processor(supplier_code: str, config: Dict[str, Any]) -> SupplierProcessor:
        """
        Create appropriate processor for supplier.
        
        Args:
            supplier_code: Supplier code
            config: Supplier configuration
            
        Returns:
            SupplierProcessor instance
        """
        # Use specialized processors for specific suppliers
        specialized_processors = {
            'AL': AliciaProcessor,
            'VF': VivicaFoxProcessor,
            'BY': BoyangProcessor,
            'NBF': ChadeProcessor,
            'OUTRE': OutreProcessor,
            'HZ': HarlemProcessor,
            'SNG': SNGProcessor,
            'MANE': ManeProcessor
        }
        
        if supplier_code in specialized_processors:
            processor_class = specialized_processors[supplier_code]
            return processor_class(supplier_code, config)
        
        # Fallback to generic processors based on file format
        file_format = config.get('file_format', 'excel')
        
        if file_format == 'excel':
            return ExcelSupplierProcessor(supplier_code, config)
        elif file_format == 'csv':
            return CSVSupplierProcessor(supplier_code, config)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")


# Specific processor classes for suppliers with unique requirements

class AliciaProcessor(ExcelSupplierProcessor):
    """Specialized processor for Alicia International (AL) with dual file handling."""
    
    def process_files(self, file_paths: List[str]) -> SupplierInventory:
        """Process AL files - expects both 'brs' and 'inv' files."""
        # AL requires both files to be concatenated
        if len(file_paths) < 2:
            logger.warning(f"AL processor expects 2 files, got {len(file_paths)}")
        
        return super().process_files(file_paths)


class VivicaFoxProcessor(ExcelSupplierProcessor):
    """Specialized processor for Vivica Fox (VF) with barcode handling."""
    
    def process_files(self, file_paths: List[str]) -> SupplierInventory:
        """Process VF files with special barcode handling."""
        if not file_paths:
            raise ValueError(f"No files provided for {self.supplier_code}")
        
        file_path = file_paths[0]
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        try:
            # Load with specific dtype for Barcode column
            df = pd.read_excel(file_path, dtype={'Barcode': str})
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            
        except Exception as e:
            raise ValueError(f"Error reading Excel file {file_path}: {e}")
        
        # Standardize and clean data
        standardized_df = self._standardize_dataframe(df)
        
        # VF-specific cleaning: handle non-numeric barcodes
        standardized_df.loc[~standardized_df['UPC'].str.isnumeric(), 'UPC'] = pd.NA
        standardized_df['UPC'] = pd.to_numeric(standardized_df['UPC'], downcast='integer')
        
        cleaned_df = self._clean_inventory_data(standardized_df)
        
        # VF-specific rule: set inventory to 0 if less than 10
        cleaned_df.loc[cleaned_df['company Inventory'] < 10, 'company Inventory'] = 0
        
        # Convert to inventory items
        items = self._dataframe_to_inventory_items(cleaned_df)
        
        return SupplierInventory(
            supplier_code=self.supplier_code,
            items=items,
            last_sync=datetime.now(),
            file_sources=[file_path]
        )


class BoyangProcessor(ExcelSupplierProcessor):
    """Specialized processor for Boyang (BY) with skiprows handling."""
    
    def process_files(self, file_paths: List[str]) -> SupplierInventory:
        """Process BY files with skiprows."""
        if not file_paths:
            raise ValueError(f"No files provided for {self.supplier_code}")
        
        file_path = file_paths[0]
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        try:
            # Skip first 3 rows as per existing logic
            df = pd.read_excel(file_path, skiprows=3)
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            
        except Exception as e:
            raise ValueError(f"Error reading Excel file {file_path}: {e}")
        
        # Standardize and clean data
        standardized_df = self._standardize_dataframe(df)
        cleaned_df = self._clean_inventory_data(standardized_df)
        
        # BY-specific rule: set inventory to 0 if less than 10
        cleaned_df.loc[cleaned_df['company Inventory'] < 10, 'company Inventory'] = 0
        
        # Convert to inventory items
        items = self._dataframe_to_inventory_items(cleaned_df)
        
        return SupplierInventory(
            supplier_code=self.supplier_code,
            items=items,
            last_sync=datetime.now(),
            file_sources=[file_path]
        )


class ChadeProcessor(ExcelSupplierProcessor):
    """Specialized processor for Chade Fashions (NBF) with inventory mapping."""
    
    def _clean_inventory_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean NBF data with special inventory mapping."""
        # Remove rows with missing UPC or inventory
        df = df.dropna(subset=['UPC', 'company Inventory'])
        
        # NBF-specific inventory mapping
        inventory_mapping = {'A': 20, 'B': 5, 'C': 0, 'X': 0}
        df['company Inventory'] = df['company Inventory'].replace(inventory_mapping)
        
        return df


class OutreProcessor(CSVSupplierProcessor):
    """Specialized processor for Outre with tab-separated values."""
    
    def process_files(self, file_paths: List[str]) -> SupplierInventory:
        """Process Outre CSV files with special formatting."""
        return super().process_files(file_paths)


class HarlemProcessor(CSVSupplierProcessor):
    """Specialized processor for Harlem 125 (HZ) with tab-separated values."""
    
    def process_files(self, file_paths: List[str]) -> SupplierInventory:
        """Process HZ CSV files with special formatting."""
        return super().process_files(file_paths)


class SNGProcessor(ExcelSupplierProcessor):
    """Specialized processor for SNG Hair with filename filtering."""
    
    def process_files(self, file_paths: List[str]) -> SupplierInventory:
        """Process SNG files with filename length validation."""
        # SNG has specific filename length requirements
        filename_length = self.processing_rules.get('filename_length_filter')
        if filename_length:
            filtered_paths = []
            for path in file_paths:
                filename = os.path.basename(path)
                if len(filename) == filename_length:
                    filtered_paths.append(path)
            file_paths = filtered_paths
        
        return super().process_files(file_paths)


class ManeProcessor(ExcelSupplierProcessor):
    """Specialized processor for Mane Concept with barcode handling."""
    
    def process_files(self, file_paths: List[str]) -> SupplierInventory:
        """Process MANE files with special barcode handling."""
        if not file_paths:
            raise ValueError(f"No files provided for {self.supplier_code}")
        
        file_path = file_paths[0]
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        try:
            # Load with specific dtype for Barcode column
            df = pd.read_excel(file_path, dtype={'Barcode': str})
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            
        except Exception as e:
            raise ValueError(f"Error reading Excel file {file_path}: {e}")
        
        # Standardize and clean data
        standardized_df = self._standardize_dataframe(df)
        cleaned_df = self._clean_inventory_data(standardized_df)
        
        # MANE-specific rule: set inventory to 0 if less than 10
        cleaned_df.loc[cleaned_df['company Inventory'] < 10, 'company Inventory'] = 0
        
        # Convert to inventory items
        items = self._dataframe_to_inventory_items(cleaned_df)
        
        return SupplierInventory(
            supplier_code=self.supplier_code,
            items=items,
            last_sync=datetime.now(),
            file_sources=[file_path]
        )

# Usage example
if __name__ == "__main__":
    """
    Example usage of supplier configuration and processing.
    """
    from .config import ConfigManager
    
    # Initialize configuration manager
    config_manager = ConfigManager(root_path='')
    
    # Get configuration for a specific supplier
    al_config = config_manager.get_supplier_config('AL')
    print(f"AL Supplier: {al_config.name}")
    print(f"Email Subject: {al_config.email_subject}")
    print(f"File Format: {al_config.file_format}")
    
    # Create processor for the supplier
    processor = SupplierProcessorFactory.create_processor('AL', al_config.__dict__)
    print(f"Created processor: {type(processor).__name__}")
    
    # Example of processing files (would need actual files)
    # file_paths = ['inv_data/AL_brs inv.xls', 'inv_data/AL_inv.xls']
    # inventory = processor.process_files(file_paths)
    # print(f"Processed {inventory.item_count} items")