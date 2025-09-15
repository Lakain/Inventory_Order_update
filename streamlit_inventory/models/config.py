"""
Configuration management models and utilities for the Streamlit inventory system.

This module provides centralized configuration management with structured data models
for suppliers, database connections, and Amazon API settings.

Supplier Configuration Mapping:
==============================

This module maps the existing keyword_mailadd.json configuration to structured 
SupplierConfig objects with detailed processing rules for each supplier:

- AL (Alicia International): Excel files, dual file processing (brs + inv)
- VF (Amekor/Vivica Fox): Excel files, barcode handling, inventory threshold
- BY (Bobbi Boss): Excel files, skip rows, inventory threshold  
- NBF (Chade Fashions): Excel files, inventory letter mapping (A/B/C/X)
- OUTRE (Outre): CSV files, tab-separated, Y/N inventory mapping
- HZ (Harlem 125): CSV files, tab-separated, Y/N inventory mapping
- SNG (SNG Hair): Excel files, filename filtering, Y/N inventory mapping
- MANE (Mane Concept): Excel files, barcode handling, inventory threshold

Each supplier configuration includes:
- Email search criteria (subject, from address, folder)
- File format and processing rules
- Column mappings for standardization
- Data type specifications
- Inventory value transformations
- File naming patterns and filters

The configuration system enables the creation of specialized processor classes
for each supplier while maintaining a consistent interface.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class SupplierConfig:
    """Configuration for a supplier including email and file processing settings."""
    code: str
    name: str
    email_subject: str
    email_from: Optional[str]
    file_format: str = 'excel'  # 'excel', 'csv', 'txt'
    file_patterns: List[str] = field(default_factory=list)
    column_mapping: Dict[str, str] = field(default_factory=dict)
    processing_rules: Dict[str, Any] = field(default_factory=dict)
    dtypes: Optional[Dict[str, type]] = None
    encoding: str = 'utf-8'
    
    def __post_init__(self):
        """Validate supplier configuration after initialization."""
        if not self.code:
            raise ValueError("Supplier code cannot be empty")
        if not self.email_subject:
            raise ValueError(f"Email subject required for supplier {self.code}")
        if self.file_format not in ['excel', 'csv', 'txt']:
            raise ValueError(f"Invalid file format '{self.file_format}' for supplier {self.code}")


@dataclass
class DatabaseConfig:
    """Configuration for database connection."""
    server: str
    database: str
    username: str
    password: str
    
    def __post_init__(self):
        """Validate database configuration after initialization."""
        if not all([self.server, self.database, self.username, self.password]):
            raise ValueError("All database configuration fields are required")
    
    @property
    def connection_string(self) -> str:
        """Generate SQL Server connection string."""
        return (f'DRIVER={{SQL Server}};SERVER={self.server};'
                f'DATABASE={self.database};UID={self.username};PWD={self.password}')


@dataclass
class AmazonConfig:
    """Configuration for Amazon SP-API."""
    credentials: Dict[str, str]
    refresh_token: str
    marketplace: str = 'US'
    
    def __post_init__(self):
        """Validate Amazon API configuration after initialization."""
        if not self.credentials:
            raise ValueError("Amazon credentials are required")
        if 'lwa_app_id' not in self.credentials or 'lwa_client_secret' not in self.credentials:
            raise ValueError("Amazon credentials must include lwa_app_id and lwa_client_secret")
        if not self.refresh_token:
            raise ValueError("Amazon refresh token is required")


@dataclass
class EmailConfig:
    """Configuration for email/Gmail access."""
    username: str
    password: str
    imap_server: str = 'imap.gmail.com'
    imap_port: int = 993
    
    def __post_init__(self):
        """Validate email configuration after initialization."""
        if not all([self.username, self.password]):
            raise ValueError("Email username and password are required")


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass


class ConfigManager:
    """Centralized configuration management for the inventory system."""
    
    def __init__(self, root_path: str = ''):
        """
        Initialize configuration manager.
        
        Args:
            root_path: Root path for configuration files (default: current directory)
        """
        self.root_path = Path(root_path) if root_path else Path.cwd()
        self.appdata_path = self.root_path / 'appdata'
        
        # Configuration caches
        self._supplier_configs: Optional[Dict[str, SupplierConfig]] = None
        self._database_config: Optional[DatabaseConfig] = None
        self._amazon_config: Optional[AmazonConfig] = None
        self._email_config: Optional[EmailConfig] = None
        
        # Validate configuration directory exists
        if not self.appdata_path.exists():
            raise ConfigurationError(f"Configuration directory not found: {self.appdata_path}")
    
    def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """
        Load and parse a JSON configuration file.
        
        Args:
            filename: Name of the JSON file to load
            
        Returns:
            Parsed JSON data as dictionary
            
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        file_path = self.appdata_path / filename
        
        try:
            if not file_path.exists():
                raise ConfigurationError(f"Configuration file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Successfully loaded configuration from {filename}")
            return data
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in {filename}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading {filename}: {e}")
    
    def get_supplier_configs(self) -> Dict[str, SupplierConfig]:
        """
        Get all supplier configurations.
        
        Returns:
            Dictionary mapping supplier codes to SupplierConfig objects
            
        Raises:
            ConfigurationError: If supplier configurations cannot be loaded
        """
        if self._supplier_configs is None:
            try:
                # Load keyword_mailadd.json
                supplier_data = self._load_json_file('keyword_mailadd.json')
                
                self._supplier_configs = {}
                for code, config in supplier_data.items():
                    # Create SupplierConfig with basic email settings
                    supplier_config = SupplierConfig(
                        code=code,
                        name=self._get_supplier_name(code),
                        email_subject=config.get('SUBJECT', ''),
                        email_from=config.get('FROM'),
                        file_format=self._get_supplier_file_format(code),
                        file_patterns=self._get_supplier_file_patterns(code),
                        column_mapping=self._get_supplier_column_mapping(code),
                        processing_rules=self._get_supplier_processing_rules(code),
                        dtypes=self._get_supplier_dtypes(code),
                        encoding=self._get_supplier_encoding(code)
                    )
                    
                    self._supplier_configs[code] = supplier_config
                
                logger.info(f"Loaded {len(self._supplier_configs)} supplier configurations")
                
            except Exception as e:
                raise ConfigurationError(f"Failed to load supplier configurations: {e}")
        
        return self._supplier_configs
    
    def get_supplier_config(self, supplier_code: str) -> SupplierConfig:
        """
        Get configuration for a specific supplier.
        
        Args:
            supplier_code: Supplier code (e.g., 'AL', 'VF')
            
        Returns:
            SupplierConfig object for the specified supplier
            
        Raises:
            ConfigurationError: If supplier configuration not found
        """
        configs = self.get_supplier_configs()
        
        if supplier_code not in configs:
            raise ConfigurationError(f"Supplier configuration not found: {supplier_code}")
        
        return configs[supplier_code]
    
    def get_supplier_codes(self) -> List[str]:
        """
        Get list of all available supplier codes.
        
        Returns:
            List of supplier codes
        """
        return list(self.get_supplier_configs().keys())
    
    def create_supplier_processor(self, supplier_code: str):
        """
        Create a processor instance for the specified supplier.
        
        Args:
            supplier_code: Supplier code (e.g., 'AL', 'VF')
            
        Returns:
            SupplierProcessor instance configured for the supplier
            
        Raises:
            ConfigurationError: If supplier configuration not found
        """
        from .supplier import SupplierProcessorFactory
        
        config = self.get_supplier_config(supplier_code)
        return SupplierProcessorFactory.create_processor(supplier_code, config.__dict__)
    
    def get_database_config(self) -> DatabaseConfig:
        """
        Get database configuration.
        
        Returns:
            DatabaseConfig object
            
        Raises:
            ConfigurationError: If database configuration cannot be loaded
        """
        if self._database_config is None:
            try:
                db_data = self._load_json_file('db_auth.json')
                self._database_config = DatabaseConfig(**db_data)
                logger.info("Successfully loaded database configuration")
                
            except Exception as e:
                raise ConfigurationError(f"Failed to load database configuration: {e}")
        
        return self._database_config
    
    def get_amazon_config(self) -> AmazonConfig:
        """
        Get Amazon API configuration.
        
        Returns:
            AmazonConfig object
            
        Raises:
            ConfigurationError: If Amazon configuration cannot be loaded
        """
        if self._amazon_config is None:
            try:
                amazon_data = self._load_json_file('api_keys.json')
                self._amazon_config = AmazonConfig(**amazon_data)
                logger.info("Successfully loaded Amazon API configuration")
                
            except Exception as e:
                raise ConfigurationError(f"Failed to load Amazon configuration: {e}")
        
        return self._amazon_config
    
    def get_email_config(self) -> EmailConfig:
        """
        Get email configuration.
        
        Returns:
            EmailConfig object
            
        Raises:
            ConfigurationError: If email configuration cannot be loaded
        """
        if self._email_config is None:
            try:
                # Load Gmail authentication from gmail_auth.json if it exists
                try:
                    email_data = self._load_json_file('gmail_auth.json')
                except ConfigurationError:
                    # Fallback to default configuration - will need to be set up
                    logger.warning("gmail_auth.json not found, using placeholder configuration")
                    email_data = {
                        'username': 'your-email@gmail.com',
                        'password': 'your-app-password'
                    }
                
                self._email_config = EmailConfig(**email_data)
                logger.info("Successfully loaded email configuration")
                
            except Exception as e:
                raise ConfigurationError(f"Failed to load email configuration: {e}")
        
        return self._email_config
    
    def reload_configurations(self):
        """Clear cached configurations to force reload on next access."""
        self._supplier_configs = None
        self._database_config = None
        self._amazon_config = None
        self._email_config = None
        logger.info("Configuration cache cleared")
    
    def validate_all_configurations(self) -> Dict[str, bool]:
        """
        Validate all configurations and return status.
        
        Returns:
            Dictionary with validation status for each configuration type
        """
        validation_results = {}
        
        # Validate supplier configurations
        try:
            self.get_supplier_configs()
            validation_results['suppliers'] = True
        except ConfigurationError as e:
            logger.error(f"Supplier configuration validation failed: {e}")
            validation_results['suppliers'] = False
        
        # Validate database configuration
        try:
            self.get_database_config()
            validation_results['database'] = True
        except ConfigurationError as e:
            logger.error(f"Database configuration validation failed: {e}")
            validation_results['database'] = False
        
        # Validate Amazon configuration
        try:
            self.get_amazon_config()
            validation_results['amazon'] = True
        except ConfigurationError as e:
            logger.error(f"Amazon configuration validation failed: {e}")
            validation_results['amazon'] = False
        
        # Validate email configuration
        try:
            self.get_email_config()
            validation_results['email'] = True
        except ConfigurationError as e:
            logger.error(f"Email configuration validation failed: {e}")
            validation_results['email'] = False
        
        return validation_results
    
    # Helper methods for supplier-specific configurations
    # Based on analysis of existing update methods
    
    def _get_supplier_name(self, code: str) -> str:
        """Get full supplier name from code."""
        name_mapping = {
            'AL': 'Alicia International',
            'VF': 'Amekor (Vivica Fox)',
            'BY': 'Bobbi Boss',
            'NBF': 'Chade Fashions (Naomi)',
            'OUTRE': 'Outre',
            'HZ': 'Harlem 125',
            'SNG': 'SNG Hair',
            'MANE': 'Mane Concept'
        }
        return name_mapping.get(code, code)
    
    def _get_supplier_file_format(self, code: str) -> str:
        """Get file format for supplier based on existing code patterns."""
        format_mapping = {
            'AL': 'excel',
            'VF': 'excel', 
            'BY': 'excel',
            'NBF': 'excel',
            'OUTRE': 'csv',
            'HZ': 'csv',
            'SNG': 'excel',
            'MANE': 'excel'
        }
        return format_mapping.get(code, 'excel')
    
    def _get_supplier_file_patterns(self, code: str) -> List[str]:
        """Get file patterns for supplier based on existing download logic."""
        pattern_mapping = {
            'AL': ['*brs*', '*inv*'],
            'VF': ['*inv*'],
            'BY': ['*inv*'],
            'NBF': ['*inv*'],
            'OUTRE': ['*.csv'],
            'HZ': ['*.csv'],
            'SNG': ['*.xlsx'],
            'MANE': ['*inv*']
        }
        return pattern_mapping.get(code, ['*'])
    
    def _get_supplier_column_mapping(self, code: str) -> Dict[str, str]:
        """Get column mapping for supplier based on existing processing logic."""
        # Standard output columns: ['COMPAY', 'UPC', 'company Inventory', 'Description', 'Extended Description']
        mapping_dict = {
            'AL': {
                'upc_column': 'AliasItemNo',
                'inventory_column': 'OnHand Customer',
                'description_column': 'ItemCode',
                'extended_description_column': 'ItemCodeDesc'
            },
            'VF': {
                'upc_column': 'Barcode',
                'inventory_column': 'On hand',
                'description_column': 'Product ID',
                'extended_description_column': 'SKU'
            },
            'BY': {
                'upc_column': 'Barcode',
                'inventory_column': 'O/H',
                'description_column': 'Item Name',
                'extended_description_column': 'Color'
            },
            'NBF': {
                'upc_column': 'UPC Code',
                'inventory_column': 'Unnamed: 6',
                'description_column': 'No.',
                'extended_description_column': 'Description'
            },
            'OUTRE': {
                'upc_column': 'BARCODE',
                'inventory_column': 'AVAIL',
                'description_column': 'ITEM',
                'extended_description_column': 'COLOR'
            },
            'HZ': {
                'upc_column': 'BARCODE',
                'inventory_column': 'AVAIL',
                'description_column': 'ITEM',
                'extended_description_column': 'COLOR'
            },
            'SNG': {
                'upc_column': 'Barcode',
                'inventory_column': 'Available',
                'description_column': 'Item',
                'extended_description_column': 'Descrip'
            },
            'MANE': {
                'upc_column': 'Barcode',
                'inventory_column': 'AQOH',
                'description_column': 'Item',
                'extended_description_column': 'Color'
            }
        }
        return mapping_dict.get(code, {})
    
    def _get_supplier_processing_rules(self, code: str) -> Dict[str, Any]:
        """Get processing rules for supplier based on existing logic."""
        rules_mapping = {
            'AL': {
                'multiple_files': True,
                'file_names': ['AL_brs inv.xls', 'AL_inv.xls'],
                'concat_files': True,
                'inventory_type': 'int',
                'email_folder': '"[Gmail]/All Mail"',
                'file_patterns': ['*brs*', '*inv*']
            },
            'VF': {
                'multiple_files': False,
                'file_names': ['VF_Inventory.xls'],
                'inventory_type': 'int',
                'email_folder': '"[Gmail]/All Mail"',
                'dtype_overrides': {'Barcode': str},
                'numeric_conversion': True,
                'min_inventory_threshold': 10
            },
            'BY': {
                'multiple_files': False,
                'file_names': ['BY_InventoryListAll.xls'],
                'inventory_type': 'int',
                'email_folder': '"[Gmail]/All Mail"',
                'skiprows': 3,
                'min_inventory_threshold': 10
            },
            'NBF': {
                'multiple_files': False,
                'file_names': ['NBF_Chade Fashions.xlsx'],
                'inventory_mapping': {'A': 20, 'B': 5, 'C': 0, 'X': 0},
                'email_folder': '"[Gmail]/All Mail"',
                'file_extension_filter': '.xlsx'
            },
            'OUTRE': {
                'multiple_files': False,
                'file_names': ['OUTRE_StockAvailability.csv'],
                'csv_separator': '\t',
                'skiprows': [1],
                'skipfooter': 1,
                'inventory_mapping': {'Y': 20, 'N': 0},
                'email_folder': 'Company/Outre'
            },
            'HZ': {
                'multiple_files': False,
                'file_names': ['HZ_StockAvailability.csv'],
                'csv_separator': '\t',
                'skiprows': [1],
                'skipfooter': 1,
                'inventory_mapping': {'Y': 20, 'N': 0},
                'email_folder': 'Company/Sensationnel'
            },
            'SNG': {
                'multiple_files': False,
                'file_names': ['SNG_inv.xlsx'],
                'inventory_mapping': {'Y': 20, 'N': 0},
                'filename_length_filter': 9,
                'email_folder': '"[Gmail]/All Mail"',
                'email_search_backwards': True
            },
            'MANE': {
                'multiple_files': False,
                'file_names': ['MANE_inv.xlsx'],
                'inventory_type': 'int',
                'email_folder': '"[Gmail]/All Mail"',
                'dtype_overrides': {'Barcode': str},
                'min_inventory_threshold': 10
            }
        }
        return rules_mapping.get(code, {})
    
    def _get_supplier_dtypes(self, code: str) -> Optional[Dict[str, type]]:
        """Get data types for supplier columns."""
        dtype_mapping = {
            'VF': {'Barcode': str},
            'MANE': {'Barcode': str}
        }
        return dtype_mapping.get(code, None)
    
    def _get_supplier_encoding(self, code: str) -> str:
        """Get file encoding for supplier."""
        encoding_mapping = {
            'OUTRE': 'utf_16',
            'HZ': 'utf_16',
            'AL': 'utf-8',
            'VF': 'utf-8',
            'BY': 'utf-8',
            'NBF': 'utf-8',
            'SNG': 'utf-8',
            'MANE': 'utf-8'
        }
        return encoding_mapping.get(code, 'utf-8')