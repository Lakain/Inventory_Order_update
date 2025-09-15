"""
Database service for handling POS database connections and operations.
Extracted from salesUpdateWindow.py Worker class.
"""

import json
import pandas as pd
import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.pool import QueuePool
from typing import Optional, Dict, Any, List
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing database connections and operations."""
    
    def __init__(self, root_path: str = ''):
        self.root_path = root_path
        self._engine = None
        self._load_config()
    
    def _load_config(self):
        """Load database configuration from JSON file."""
        try:
            with open(f'{self.root_path}appdata/db_auth.json') as f:
                config = json.load(f)
                self.server = config['server']
                self.database = config['database']
                self.username = config['username']
                self.password = config['password']
        except FileNotFoundError:
            logger.error(f"Database config file not found: {self.root_path}appdata/db_auth.json")
            raise
        except KeyError as e:
            logger.error(f"Missing database config key: {e}")
            raise
    
    def get_engine(self):
        """Get or create database engine with connection pooling."""
        if self._engine is None:
            connection_string = (
                f'DRIVER={{SQL Server}};SERVER={self.server};'
                f'DATABASE={self.database};UID={self.username};PWD={self.password}'
            )
            connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
            
            self._engine = create_engine(
                connection_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600
            )
        return self._engine
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        engine = self.get_engine()
        connection = engine.connect()
        try:
            yield connection
        finally:
            connection.close()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_connection() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_pos_inventory_data(self) -> pd.DataFrame:
        """
        Get POS inventory data.
        Extracted from salesUpdateWindow.py Worker.run() method.
        """
        query = """
        SELECT 
            Item.ItemLookupCode AS 'Item Lookup Code',
            Item.Price AS 'Price',
            Item.Quantity AS 'Qty On Hand',
            Item.SubDescription3 AS 'Display',
            Item.SubDescription2 AS 'Comp Inv {comp_inv_date}',
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
        """.format(comp_inv_date=datetime.date.today().strftime("%m%d"))
        
        try:
            with self.get_connection() as conn:
                df = pd.read_sql(query, conn, dtype={'Qty On Hand': 'int64'})
            
            # Process display column as in original code
            df['Display'] = df['Display'].str.strip()
            df.loc[df['Display'].str.startswith('0'), 'Display'] = '0'
            df.loc[df['Display'].str.startswith('1'), 'Display'] = '1'
            df.loc[df['Display'] == '', 'Display'] = '0'
            
            # Calculate item quantity
            df['ITEM QTY'] = df['Qty On Hand'] - df['Display'].astype('int64')
            df.loc[df['ITEM QTY'] < 0, 'ITEM QTY'] = 0
            
            # Group by reorder number
            temp = df[['Reorder Number', 'ITEM QTY']].groupby('Reorder Number').sum()
            temp.columns = ['FIN TOT QTY']
            
            # Merge back
            result = df.merge(temp, on='Reorder Number', how='left')
            result['FIN TOT QTY'] = result['FIN TOT QTY'].fillna(0).astype('int64')
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting POS inventory data: {e}")
            raise
    
    def get_sales_data(self, date_from: datetime.date, date_to: datetime.date) -> pd.DataFrame:
        """
        Get sales data for specified date range.
        Extracted from salesUpdateWindow.py Worker.run() method.
        """
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
            AND hs.DateTransferred BETWEEN '{date_from}' AND '{date_to} 23:59:59'
        ORDER BY
            hs.DateTransferred;
        """.format(
            date_from=f'{date_from.year}-{date_from.month}-{date_from.day}',
            date_to=f'{date_to.year}-{date_to.month}-{date_to.day}'
        )
        
        try:
            with self.get_connection() as conn:
                df = pd.read_sql(query, conn, dtype={'QTY SOLD': 'int64'})
            return df
        except Exception as e:
            logger.error(f"Error getting sales data: {e}")
            raise
    
    def update_pos_inventory(self, inventory_data: pd.DataFrame) -> bool:
        """
        Update POS inventory with new data.
        This would contain the logic for updating inventory in the POS system.
        """
        try:
            # This is a placeholder for the actual inventory update logic
            # The original code doesn't show the POS update mechanism clearly
            # This would need to be implemented based on the specific POS system requirements
            logger.info(f"Updating POS inventory with {len(inventory_data)} records")
            
            # Example implementation - would need actual update logic
            with self.get_connection() as conn:
                # Update logic would go here
                # This might involve updating Item.SubDescription2 or other fields
                pass
            
            return True
        except Exception as e:
            logger.error(f"Error updating POS inventory: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup."""
        try:
            backup_query = f"""
            BACKUP DATABASE [{self.database}] 
            TO DISK = '{backup_path}'
            WITH FORMAT, INIT;
            """
            
            with self.get_connection() as conn:
                conn.execute(text(backup_query))
            
            logger.info(f"Database backup created: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup."""
        try:
            restore_query = f"""
            RESTORE DATABASE [{self.database}] 
            FROM DISK = '{backup_path}'
            WITH REPLACE;
            """
            
            with self.get_connection() as conn:
                conn.execute(text(restore_query))
            
            logger.info(f"Database restored from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get database connection status information."""
        try:
            is_connected = self.test_connection()
            return {
                'connected': is_connected,
                'server': self.server,
                'database': self.database,
                'last_check': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'last_check': datetime.datetime.now().isoformat()
            }