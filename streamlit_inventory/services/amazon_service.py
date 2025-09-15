"""
Amazon API service for handling SP-API operations and report generation.
Extracted from invUpdateWindow.py Worker class and amazonOrderWindow.py.
"""

import json
import datetime
import logging
from typing import Dict, List, Optional, Any
from time import sleep
import pandas as pd
from sp_api.api import Reports, Orders
from sp_api.base.reportTypes import ReportType
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class AmazonService:
    """Service for managing Amazon SP-API operations."""
    
    def __init__(self, root_path: str = ''):
        self.root_path = root_path
        self._load_config()
        self._rate_limiter = RateLimiter()
    
    def _load_config(self):
        """Load Amazon API configuration from JSON file."""
        try:
            with open(f'{self.root_path}appdata/api_keys.json') as f:
                config = json.load(f)
                self.credentials = config['credentials']
                self.refresh_token = config['refresh_token']
        except FileNotFoundError:
            logger.error(f"Amazon API config file not found: {self.root_path}appdata/api_keys.json")
            raise
        except KeyError as e:
            logger.error(f"Missing Amazon API config key: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test Amazon SP-API connection."""
        try:
            reports_api = Reports(credentials=self.credentials, refresh_token=self.refresh_token)
            # Try to get a simple report to test connection
            response = reports_api.get_reports(reportTypes=[ReportType.GET_MERCHANT_LISTINGS_ALL_DATA])
            return True
        except Exception as e:
            logger.error(f"Amazon API connection test failed: {e}")
            return False
    
    def create_inventory_report(self) -> Optional[str]:
        """
        Create Amazon inventory report.
        Extracted from invUpdateWindow.py Worker.run() method.
        """
        try:
            with self._rate_limiter:
                reports_api = Reports(credentials=self.credentials, refresh_token=self.refresh_token)
                response = reports_api.create_report(reportType=ReportType.GET_MERCHANT_LISTINGS_ALL_DATA)
                
                if response and hasattr(response, 'payload') and 'reportId' in response.payload:
                    report_id = response.payload['reportId']
                    logger.info(f"Created Amazon inventory report: {report_id}")
                    return report_id
                else:
                    logger.error("Failed to create Amazon inventory report")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating Amazon inventory report: {e}")
            return None
    
    def get_report_status(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a report."""
        try:
            with self._rate_limiter:
                reports_api = Reports(credentials=self.credentials, refresh_token=self.refresh_token)
                response = reports_api.get_report(report_id)
                
                if response and hasattr(response, 'payload'):
                    return response.payload
                return None
                
        except Exception as e:
            logger.error(f"Error getting report status for {report_id}: {e}")
            return None
    
    def wait_for_report_completion(self, report_id: str, max_wait_time: int = 600, check_interval: int = 5) -> Optional[str]:
        """
        Wait for report to complete and return document ID.
        Extracted from invUpdateWindow.py Worker.run() method.
        """
        start_time = datetime.datetime.now()
        
        while (datetime.datetime.now() - start_time).seconds < max_wait_time:
            try:
                report_status = self.get_report_status(report_id)
                
                if report_status and 'reportDocumentId' in report_status:
                    document_id = report_status['reportDocumentId']
                    logger.info(f"Report {report_id} completed with document ID: {document_id}")
                    return document_id
                
                logger.info(f"Report {report_id} still processing, waiting {check_interval} seconds...")
                sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error checking report status: {e}")
                sleep(check_interval)
        
        logger.error(f"Report {report_id} did not complete within {max_wait_time} seconds")
        return None
    
    def download_report_document(self, document_id: str, file_path: str) -> bool:
        """Download report document to file."""
        try:
            with self._rate_limiter:
                reports_api = Reports(credentials=self.credentials, refresh_token=self.refresh_token)
                
                with open(file_path, "w", encoding='utf-8') as f:
                    reports_api.get_report_document(document_id, file=f)
                
                logger.info(f"Downloaded report document to: {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error downloading report document {document_id}: {e}")
            return False
    
    def generate_and_download_inventory_report(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        Complete workflow to generate and download inventory report.
        Combines the logic from invUpdateWindow.py Worker.run() method.
        """
        if output_path is None:
            output_path = f"{self.root_path}inv_data/Amazon_All+Listings+Report.txt"
        
        try:
            # Create report
            report_id = self.create_inventory_report()
            if not report_id:
                return None
            
            # Wait for completion
            document_id = self.wait_for_report_completion(report_id)
            if not document_id:
                return None
            
            # Download report
            if self.download_report_document(document_id, output_path):
                return output_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error in complete inventory report workflow: {e}")
            return None
    
    def get_orders(self, created_after: datetime.datetime, created_before: Optional[datetime.datetime] = None) -> Optional[List[Dict]]:
        """
        Get Amazon orders for specified date range.
        Based on amazonOrderWindow.py functionality.
        """
        try:
            with self._rate_limiter:
                orders_api = Orders(credentials=self.credentials, refresh_token=self.refresh_token)
                
                # Build parameters
                params = {
                    'CreatedAfter': created_after.isoformat(),
                    'MarketplaceIds': ['ATVPDKIKX0DER']  # US marketplace
                }
                
                if created_before:
                    params['CreatedBefore'] = created_before.isoformat()
                
                response = orders_api.get_orders(**params)
                
                if response and hasattr(response, 'payload') and 'Orders' in response.payload:
                    orders = response.payload['Orders']
                    logger.info(f"Retrieved {len(orders)} orders")
                    return orders
                
                return []
                
        except Exception as e:
            logger.error(f"Error getting Amazon orders: {e}")
            return None
    
    def get_order_items(self, order_id: str) -> Optional[List[Dict]]:
        """Get items for a specific order."""
        try:
            with self._rate_limiter:
                orders_api = Orders(credentials=self.credentials, refresh_token=self.refresh_token)
                response = orders_api.get_order_items(order_id)
                
                if response and hasattr(response, 'payload') and 'OrderItems' in response.payload:
                    return response.payload['OrderItems']
                
                return []
                
        except Exception as e:
            logger.error(f"Error getting order items for {order_id}: {e}")
            return None
    
    def get_unshipped_orders(self) -> Optional[pd.DataFrame]:
        """
        Get unshipped orders and create DataFrame.
        Based on amazonOrderWindow.py functionality.
        """
        try:
            # Get orders from last 30 days
            created_after = datetime.datetime.now() - datetime.timedelta(days=30)
            orders = self.get_orders(created_after)
            
            if not orders:
                return pd.DataFrame()
            
            # Filter for unshipped orders
            unshipped_orders = [
                order for order in orders 
                if order.get('OrderStatus') in ['Pending', 'Unshipped']
            ]
            
            # Convert to DataFrame format similar to existing code
            order_data = []
            for order in unshipped_orders:
                order_items = self.get_order_items(order['AmazonOrderId'])
                if order_items:
                    for item in order_items:
                        order_data.append({
                            'order-id': order['AmazonOrderId'],
                            'order-date': order.get('PurchaseDate', ''),
                            'sku': item.get('SellerSKU', ''),
                            'quantity': item.get('QuantityOrdered', 0),
                            'item-name': item.get('Title', ''),
                            'order-status': order.get('OrderStatus', ''),
                            'ship-service-level': order.get('ShipServiceLevel', ''),
                            'buyer-email': order.get('BuyerInfo', {}).get('BuyerEmail', ''),
                            'ship-address': self._format_shipping_address(order.get('ShippingAddress', {}))
                        })
            
            return pd.DataFrame(order_data)
            
        except Exception as e:
            logger.error(f"Error getting unshipped orders: {e}")
            return None
    
    def _format_shipping_address(self, address: Dict) -> str:
        """Format shipping address for display."""
        if not address:
            return ''
        
        parts = [
            address.get('Name', ''),
            address.get('AddressLine1', ''),
            address.get('AddressLine2', ''),
            f"{address.get('City', '')} {address.get('StateOrRegion', '')} {address.get('PostalCode', '')}",
            address.get('CountryCode', '')
        ]
        
        return ', '.join([part for part in parts if part])
    
    async def get_orders_async(self, created_after: datetime.datetime, created_before: Optional[datetime.datetime] = None) -> Optional[List[Dict]]:
        """Async version of get_orders for better performance."""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor, 
                self.get_orders, 
                created_after, 
                created_before
            )
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get Amazon API connection status information."""
        try:
            is_connected = self.test_connection()
            return {
                'connected': is_connected,
                'marketplace': 'US',
                'last_check': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'last_check': datetime.datetime.now().isoformat()
            }


class RateLimiter:
    """Simple rate limiter for Amazon API calls."""
    
    def __init__(self, calls_per_second: float = 0.5):
        self.calls_per_second = calls_per_second
        self.last_call_time = 0
    
    def __enter__(self):
        current_time = datetime.datetime.now().timestamp()
        time_since_last_call = current_time - self.last_call_time
        min_interval = 1.0 / self.calls_per_second
        
        if time_since_last_call < min_interval:
            sleep_time = min_interval - time_since_last_call
            sleep(sleep_time)
        
        self.last_call_time = datetime.datetime.now().timestamp()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass