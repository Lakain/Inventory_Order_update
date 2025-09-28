"""
Inventory Update page - Supplier inventory processing interface.
Provides supplier selection, progress tracking, and manual file upload options.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import traceback
from pathlib import Path
import os
import shutil

from models.config import ConfigManager, ConfigurationError
from services.inventory_service import InventoryService
from services.email_service import EmailService
from services.database_service import DatabaseService
from utils.helpers import handle_error, format_file_size, create_progress_callback

logger = logging.getLogger(__name__)


def show_inventory_update():
    """Display the inventory update interface with supplier selection and progress tracking."""
    st.title("📦 Inventory Update")
    st.markdown("Update inventory from supplier emails and files")
    
    # Initialize session state for inventory update
    if 'inventory_update_state' not in st.session_state:
        st.session_state.inventory_update_state = {
            'selected_suppliers': {},
            'update_in_progress': False,
            'last_update_results': None,
            'uploaded_files': {},
            'supplier_status': {}
        }
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        supplier_configs = config_manager.get_supplier_configs()
        
        # Display supplier selection interface
        _display_supplier_selection(supplier_configs)
        
        # Display system status
        _display_system_status()
        
        # Display manual file upload section
        _display_manual_upload_section(supplier_configs)
        
        # Display update controls and execution
        _display_update_controls(supplier_configs)
        
        # Display last update results if available
        _display_update_results()
        
    except ConfigurationError as e:
        st.error(f"❌ Configuration Error: {str(e)}")
        st.info("💡 Please check your configuration files in the appdata directory.")
    except Exception as e:
        handle_error(e, "inventory update page")


def _display_supplier_selection(supplier_configs: Dict[str, Any]):
    """Display supplier selection interface with status indicators."""
    st.subheader("📋 Supplier Selection")
    
    # Get current supplier status
    supplier_status = _get_supplier_status(supplier_configs)
    
    # Create columns for supplier checkboxes
    cols = st.columns(3)
    
    for i, (code, config) in enumerate(supplier_configs.items()):
        col = cols[i % 3]
        
        with col:
            # Display supplier status indicator
            status = supplier_status.get(code, {})
            status_icon = _get_status_icon(status)
            
            # Checkbox for supplier selection
            selected = st.checkbox(
                f"{status_icon} **{config.name}** ({code})",
                value=st.session_state.inventory_update_state['selected_suppliers'].get(code, True),
                key=f"supplier_checkbox_{code}",
                help=f"Email: {config.email_subject[:50]}..." if config.email_subject else "No email configured"
            )
            
            # Update session state
            st.session_state.inventory_update_state['selected_suppliers'][code] = selected
            
            # Display last update info if available
            last_update = status.get('last_update')
            if last_update:
                st.caption(f"Last updated: {last_update}")
            else:
                st.caption("Never updated")


def _get_supplier_status(supplier_configs: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Get status information for all suppliers."""
    status_dict = {}
    
    try:
        # Load update history to get last update dates
        update_history_path = "appdata/update_history.xlsx"
        if os.path.exists(update_history_path):
            update_history = pd.read_excel(update_history_path)
            
            for code in supplier_configs.keys():
                # Find supplier in update history
                supplier_row = update_history[update_history['Initial'] == code]
                
                if not supplier_row.empty and supplier_row.iloc[0]['Date']:
                    last_update = supplier_row.iloc[0]['Date']
                    # Calculate days since last update
                    try:
                        if isinstance(last_update, str):
                            last_update_date = datetime.strptime(last_update, "%m/%d/%Y").date()
                        else:
                            last_update_date = last_update.date() if hasattr(last_update, 'date') else last_update
                        
                        days_since = (datetime.now().date() - last_update_date).days
                        
                        status_dict[code] = {
                            'last_update': last_update,
                            'days_since_update': days_since,
                            'status': 'recent' if days_since <= 7 else 'stale' if days_since <= 30 else 'old'
                        }
                    except (ValueError, TypeError):
                        status_dict[code] = {
                            'last_update': str(last_update),
                            'days_since_update': None,
                            'status': 'unknown'
                        }
                else:
                    status_dict[code] = {
                        'last_update': None,
                        'days_since_update': None,
                        'status': 'never_updated'
                    }
        else:
            # No update history available
            for code in supplier_configs.keys():
                status_dict[code] = {
                    'last_update': None,
                    'days_since_update': None,
                    'status': 'no_history'
                }
                
    except Exception as e:
        logger.warning(f"Error loading supplier status: {e}")
        # Fallback to basic status
        for code in supplier_configs.keys():
            status_dict[code] = {
                'last_update': None,
                'days_since_update': None,
                'status': 'error'
            }
    
    return status_dict


def _get_status_icon(status: Dict[str, Any]) -> str:
    """Get status icon based on supplier status."""
    status_type = status.get('status', 'unknown')
    
    if status_type == 'recent':
        return "🟢"  # Green - recently updated
    elif status_type == 'stale':
        return "🟡"  # Yellow - somewhat old
    elif status_type == 'old':
        return "🔴"  # Red - very old
    elif status_type == 'never_updated':
        return "⚪"  # White - never updated
    elif status_type == 'no_history':
        return "🔵"  # Blue - no history file
    else:
        return "❓"  # Question mark - unknown status


def _display_system_status():
    """Display system status indicators."""
    st.subheader("🔧 System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Database status
        try:
            config_manager = ConfigManager()
            db_config = config_manager.get_database_config()
            st.success("✅ Database Config")
        except Exception:
            st.error("❌ Database Config")
    
    with col2:
        # Email status
        try:
            config_manager = ConfigManager()
            email_config = config_manager.get_email_config()
            st.success("✅ Email Config")
        except Exception:
            st.error("❌ Email Config")
    
    with col3:
        # Amazon API status
        try:
            config_manager = ConfigManager()
            amazon_config = config_manager.get_amazon_config()
            st.success("✅ Amazon API")
        except Exception:
            st.error("❌ Amazon API")
    
    with col4:
        # File system status
        required_dirs = ["appdata", "inv_data"]
        all_dirs_exist = all(os.path.exists(dir_path) for dir_path in required_dirs)
        if all_dirs_exist:
            st.success("✅ File System")
        else:
            st.error("❌ File System")


def _display_manual_upload_section(supplier_configs: Dict[str, Any]):
    """Display manual file upload section as fallback option."""
    st.subheader("📁 Manual File Upload")
    st.markdown("Upload supplier files manually if email download fails")
    
    # Create expandable section for manual uploads
    with st.expander("Upload Files Manually", expanded=False):
        st.info("💡 Use this section to upload supplier files manually if email download fails or for testing purposes.")
        
        # Create tabs for each supplier
        supplier_codes = list(supplier_configs.keys())
        if supplier_codes:
            tabs = st.tabs([f"{code} - {supplier_configs[code].name}" for code in supplier_codes])
            
            for i, (code, config) in enumerate(supplier_configs.items()):
                with tabs[i]:
                    st.markdown(f"**{config.name} ({code})**")
                    
                    # File format information
                    file_format = config.file_format
                    if file_format == 'excel':
                        accepted_types = ['xlsx', 'xls']
                        help_text = "Upload Excel files (.xlsx or .xls)"
                    elif file_format == 'csv':
                        accepted_types = ['csv', 'txt']
                        help_text = "Upload CSV or text files"
                    else:
                        accepted_types = None
                        help_text = "Upload supplier inventory file"
                    
                    # File uploader
                    uploaded_file = st.file_uploader(
                        f"Choose file for {code}",
                        type=accepted_types,
                        key=f"manual_upload_{code}",
                        help=help_text
                    )
                    
                    if uploaded_file is not None:
                        # Display file info
                        file_size = format_file_size(uploaded_file.size)
                        st.success(f"✅ File uploaded: {uploaded_file.name} ({file_size})")
                        
                        # Store in session state
                        if 'uploaded_files' not in st.session_state.inventory_update_state:
                            st.session_state.inventory_update_state['uploaded_files'] = {}
                        
                        # Save file temporarily
                        temp_dir = Path("temp_uploads")
                        temp_dir.mkdir(exist_ok=True)
                        temp_file_path = temp_dir / f"{code}_{uploaded_file.name}"
                        
                        with open(temp_file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        st.session_state.inventory_update_state['uploaded_files'][code] = str(temp_file_path)
                        
                        # Show preview option
                        if st.button(f"Preview {code} Data", key=f"preview_{code}"):
                            _preview_uploaded_file(code, str(temp_file_path), config)


def _preview_uploaded_file(supplier_code: str, file_path: str, config: Any):
    """Preview uploaded file data."""
    try:
        st.subheader(f"Preview: {supplier_code} Data")
        
        # Load file based on format
        if config.file_format == 'excel':
            df = pd.read_excel(file_path, nrows=10)
        elif config.file_format == 'csv':
            df = pd.read_csv(file_path, nrows=10, encoding=config.encoding)
        else:
            df = pd.read_csv(file_path, nrows=10)
        
        st.dataframe(df)
        st.info(f"Showing first 10 rows of {len(df)} total rows")
        
    except Exception as e:
        st.error(f"Error previewing file: {str(e)}")


def _display_update_controls(supplier_configs: Dict[str, Any]):
    """Display update controls and execution interface."""
    st.subheader("🚀 Update Controls")
    
    # Check if any suppliers are selected
    selected_suppliers = st.session_state.inventory_update_state['selected_suppliers']
    active_suppliers = [code for code, selected in selected_suppliers.items() if selected]
    
    if not active_suppliers:
        st.warning("⚠️ No suppliers selected. Please select at least one supplier to update.")
        return
    
    # Display selected suppliers
    st.info(f"📋 Selected suppliers: {', '.join(active_suppliers)}")
    
    # Update options
    col1, col2 = st.columns(2)
    
    with col1:
        update_mode = st.radio(
            "Update Mode",
            ["Email Download + Process", "Process Uploaded Files Only", "Email Download Only"],
            help="Choose how to handle supplier data"
        )
    
    with col2:
        backup_before_update = st.checkbox(
            "Backup before update",
            value=True,
            help="Create backup of current inventory before updating"
        )
    
    # Update button
    update_disabled = st.session_state.inventory_update_state.get('update_in_progress', False)
    
    if st.button(
        "🔄 Start Inventory Update",
        type="primary",
        disabled=update_disabled,
        help="Begin inventory update process for selected suppliers"
    ):
        _execute_inventory_update(
            active_suppliers,
            supplier_configs,
            update_mode,
            backup_before_update
        )


def _execute_inventory_update(supplier_codes: List[str], supplier_configs: Dict[str, Any], 
                            update_mode: str, backup_before_update: bool):
    """Execute the inventory update process with enhanced progress tracking and error handling."""
    
    # Show confirmation dialog before starting
    if not _show_update_confirmation(supplier_codes, update_mode, backup_before_update):
        return
    
    # Set update in progress
    st.session_state.inventory_update_state['update_in_progress'] = True
    
    # Create main containers for update process
    main_container = st.container()
    
    with main_container:
        st.subheader("🔄 Inventory Update in Progress")
        
        # Create progress tracking components
        progress_bar = st.progress(0)
        status_container = st.empty()
        details_container = st.empty()
        
        # Initialize logging for this update session
        update_start_time = datetime.now()
        update_log = []
        
        try:
            # Log update start
            start_msg = f"Starting inventory update at {update_start_time.strftime('%Y-%m-%d %H:%M:%S')}"
            update_log.append(start_msg)
            logger.info(start_msg)
            
            # Create enhanced progress callback with detailed logging
            def enhanced_progress_callback(step: str, progress: float, details: Optional[Dict[str, Any]] = None):
                """Enhanced progress callback with detailed status updates."""
                # Update progress bar and status
                progress_bar.progress(progress)
                status_container.info(f"🔄 {step}")
                
                # Log progress
                log_msg = f"Progress {progress:.1%}: {step}"
                update_log.append(log_msg)
                logger.info(log_msg)
                
                # Display additional details if provided
                if details:
                    detail_text = []
                    for key, value in details.items():
                        detail_text.append(f"**{key}:** {value}")
                    
                    if detail_text:
                        details_container.markdown("  \n".join(detail_text))
                
                # Force Streamlit to update display (removed to avoid issues during update)
                pass
            
            # Perform backup if requested
            if backup_before_update:
                enhanced_progress_callback("Creating backup of current inventory", 0.05)
                backup_result = _create_inventory_backup()
                if backup_result['success']:
                    update_log.append(f"Backup created: {backup_result['backup_path']}")
                    logger.info(f"Backup created successfully: {backup_result['backup_path']}")
                else:
                    warning_msg = f"Backup failed: {backup_result['error']}"
                    update_log.append(warning_msg)
                    logger.warning(warning_msg)
                    st.warning(f"⚠️ {warning_msg}")
            
            # Initialize inventory service
            enhanced_progress_callback("Initializing inventory service", 0.10)
            inventory_service = InventoryService()
            
            # Prepare supplier selections
            supplier_selections = {code: code in supplier_codes for code in supplier_configs.keys()}
            
            # Validate configuration before starting
            enhanced_progress_callback("Validating system configuration", 0.15)
            config_validation = _validate_system_configuration()
            if not config_validation['valid']:
                error_msg = f"Configuration validation failed: {config_validation['errors']}"
                update_log.append(error_msg)
                logger.error(error_msg)
                st.error(f"❌ {error_msg}")
                return
            
            # Get uploaded files if using manual upload mode
            uploaded_files = None
            if update_mode == "Process Uploaded Files Only":
                uploaded_files = st.session_state.inventory_update_state.get('uploaded_files', {})
                if not uploaded_files:
                    error_msg = "No uploaded files found for manual processing mode"
                    update_log.append(error_msg)
                    logger.error(error_msg)
                    st.error(f"❌ {error_msg}")
                    return
                
                # Validate uploaded files
                enhanced_progress_callback("Validating uploaded files", 0.20)
                file_validation = _validate_uploaded_files(uploaded_files, supplier_codes)
                if not file_validation['valid']:
                    error_msg = f"File validation failed: {file_validation['errors']}"
                    update_log.append(error_msg)
                    logger.error(error_msg)
                    st.error(f"❌ {error_msg}")
                    return
            
            # Execute update based on mode
            enhanced_progress_callback("Starting inventory update process", 0.25)
            
            if update_mode == "Email Download + Process":
                # Full update with email download and processing
                update_log.append("Executing full inventory update (email + processing)")
                results = inventory_service.update_inventory(
                    supplier_selections,
                    progress_callback=enhanced_progress_callback
                )
            elif update_mode == "Process Uploaded Files Only":
                # Process only uploaded files
                update_log.append("Processing uploaded files only")
                results = inventory_service.process_multiple_suppliers(
                    supplier_selections,
                    uploaded_files=uploaded_files,
                    progress_callback=enhanced_progress_callback
                )
            else:  # Email Download Only
                # Download files but don't process
                update_log.append("Downloading supplier files only")
                enhanced_progress_callback("Downloading supplier files", 0.30)
                results = _download_supplier_files_only(supplier_codes, enhanced_progress_callback)
            
            # Final progress update
            enhanced_progress_callback("Update process completed", 1.0)
            
            # Calculate update duration
            update_end_time = datetime.now()
            update_duration = update_end_time - update_start_time
            
            # Add completion info to results
            results['update_duration'] = str(update_duration)
            results['update_start_time'] = update_start_time.isoformat()
            results['update_end_time'] = update_end_time.isoformat()
            results['update_log'] = update_log
            
            # Store results in session state
            st.session_state.inventory_update_state['last_update_results'] = results
            
            # Log completion
            completion_msg = f"Update completed in {update_duration}"
            update_log.append(completion_msg)
            logger.info(completion_msg)
            
            # Clear progress indicators
            progress_bar.empty()
            status_container.empty()
            details_container.empty()
            
            # Display completion results with enhanced notifications
            _display_enhanced_completion_results(results, update_log)
            
        except Exception as e:
            # Enhanced error handling with detailed logging
            error_msg = f"Critical error during inventory update: {str(e)}"
            update_log.append(error_msg)
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Display detailed error information
            st.error(f"❌ Update Failed: {error_msg}")
            
            # Show error details in expandable section
            with st.expander("Error Details", expanded=True):
                st.code(traceback.format_exc())
                
                # Show update log up to failure point
                if update_log:
                    st.subheader("Update Log")
                    for log_entry in update_log:
                        st.text(log_entry)
            
            # Store error results
            error_results = {
                'success': False,
                'error': error_msg,
                'update_log': update_log,
                'traceback': traceback.format_exc(),
                'update_start_time': update_start_time.isoformat(),
                'update_end_time': datetime.now().isoformat()
            }
            st.session_state.inventory_update_state['last_update_results'] = error_results
        
        finally:
            # Clear update in progress flag
            st.session_state.inventory_update_state['update_in_progress'] = False
            
            # Clean up temporary files
            _cleanup_temp_files()
            
            # Final log entry
            final_msg = f"Update session ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            logger.info(final_msg)


def _download_supplier_files_only(supplier_codes: List[str], progress_callback) -> Dict[str, Any]:
    """Download supplier files without processing."""
    try:
        email_service = EmailService()
        results = {'success': True, 'supplier_results': {}}
        
        for i, supplier_code in enumerate(supplier_codes):
            progress = i / len(supplier_codes)
            progress_callback(f"Downloading {supplier_code} files", progress)
            
            try:
                downloaded_files = email_service.download_supplier_files(
                    supplier_code, 
                    None,  # No update history needed for download only
                    streamlit_mode=True
                )
                
                results['supplier_results'][supplier_code] = {
                    'success': True,
                    'files_downloaded': len(downloaded_files),
                    'downloaded_files': downloaded_files
                }
                
            except Exception as e:
                results['supplier_results'][supplier_code] = {
                    'success': False,
                    'error': str(e)
                }
        
        progress_callback("Download complete", 1.0)
        return results
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _display_update_completion(results: Dict[str, Any]):
    """Display update completion results."""
    if results.get('success', False):
        st.success("✅ Inventory update completed successfully!")
        
        # Display summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            suppliers_processed = results.get('suppliers_processed', 0)
            total_suppliers = results.get('total_suppliers', 0)
            st.metric("Suppliers Processed", f"{suppliers_processed}/{total_suppliers}")
        
        with col2:
            total_records = results.get('total_records', 0)
            st.metric("Total Records", total_records)
        
        with col3:
            completion_time = results.get('completion_time', '')
            if completion_time:
                try:
                    completion_dt = datetime.fromisoformat(completion_time.replace('Z', '+00:00'))
                    st.metric("Completed At", completion_dt.strftime("%H:%M:%S"))
                except:
                    st.metric("Completed", "✅")
        
        # Display detailed results
        if 'supplier_results' in results:
            st.subheader("📊 Detailed Results")
            
            for supplier_code, supplier_result in results['supplier_results'].items():
                with st.expander(f"{supplier_code} Results", expanded=False):
                    if supplier_result.get('success', False):
                        st.success(f"✅ {supplier_code} processed successfully")
                        
                        # Display metrics
                        metrics_col1, metrics_col2 = st.columns(2)
                        
                        with metrics_col1:
                            records = supplier_result.get('records_processed', 0)
                            st.metric("Records Processed", records)
                        
                        with metrics_col2:
                            files = supplier_result.get('files_downloaded', 0)
                            st.metric("Files Downloaded", files)
                        
                        # Display downloaded files
                        downloaded_files = supplier_result.get('downloaded_files', [])
                        if downloaded_files:
                            st.write("**Downloaded Files:**")
                            for file_path in downloaded_files:
                                st.write(f"- {Path(file_path).name}")
                    else:
                        st.error(f"❌ {supplier_code} failed: {supplier_result.get('error', 'Unknown error')}")
        
        # Display warnings if any
        warnings = results.get('warnings', [])
        if warnings:
            st.warning("⚠️ Warnings occurred during update:")
            for warning in warnings:
                st.write(f"- {warning}")
    
    else:
        st.error("❌ Inventory update failed")
        error_msg = results.get('error', 'Unknown error occurred')
        st.error(f"Error: {error_msg}")
        
        # Display any partial results
        if 'supplier_results' in results:
            st.subheader("Partial Results")
            for supplier_code, supplier_result in results['supplier_results'].items():
                if supplier_result.get('success', False):
                    st.success(f"✅ {supplier_code}: Success")
                else:
                    st.error(f"❌ {supplier_code}: {supplier_result.get('error', 'Failed')}")


def _display_update_results():
    """Display last update results if available."""
    last_results = st.session_state.inventory_update_state.get('last_update_results')
    
    if last_results:
        st.subheader("📈 Last Update Results")
        
        with st.expander("View Last Update Details", expanded=False):
            if last_results.get('success', False):
                st.success("✅ Last update completed successfully")
                
                # Display summary
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Suppliers Processed", 
                             f"{last_results.get('suppliers_processed', 0)}/{last_results.get('total_suppliers', 0)}")
                with col2:
                    st.metric("Total Records", last_results.get('total_records', 0))
                
                # Display completion time
                completion_time = last_results.get('completion_time', '')
                if completion_time:
                    st.write(f"**Completed:** {completion_time}")
                
                # Show supplier breakdown
                supplier_results = last_results.get('supplier_results', {})
                if supplier_results:
                    st.write("**Supplier Results:**")
                    for code, result in supplier_results.items():
                        status = "✅" if result.get('success', False) else "❌"
                        records = result.get('records_processed', result.get('records', 0))
                        st.write(f"- {status} {code}: {records} records")
            else:
                st.error("❌ Last update failed")
                st.error(f"Error: {last_results.get('error', 'Unknown error')}")


def _show_update_confirmation(supplier_codes: List[str], update_mode: str, backup_before_update: bool) -> bool:
    """Show confirmation dialog before starting update."""
    st.subheader("⚠️ Confirm Inventory Update")
    
    # Display update summary
    st.info(f"""
    **Update Summary:**
    - **Suppliers:** {', '.join(supplier_codes)}
    - **Mode:** {update_mode}
    - **Backup:** {'Yes' if backup_before_update else 'No'}
    - **Estimated Time:** 5-15 minutes depending on data size
    """)
    
    # Warning about potential impacts
    st.warning("""
    **Important Notes:**
    - This will update inventory data in the POS system
    - The process may take several minutes to complete
    - Do not close the browser during the update
    - Ensure stable network connection for email downloads
    """)
    
    # Confirmation checkbox
    confirm_update = st.checkbox(
        "I understand the impact and want to proceed with the inventory update",
        key="confirm_inventory_update"
    )
    
    # Confirmation buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Proceed with Update", type="primary", disabled=not confirm_update):
            return True
    
    with col2:
        if st.button("❌ Cancel Update"):
            st.info("Update cancelled by user")
            return False
    
    return False


def _create_inventory_backup() -> Dict[str, Any]:
    """Create backup of current inventory data."""
    try:
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Backup main inventory file
        source_file = Path("appdata/all_upc_inv.xlsx")
        if source_file.exists():
            backup_file = backup_dir / f"all_upc_inv_backup_{backup_timestamp}.xlsx"
            
            # Copy file
            import shutil
            shutil.copy2(source_file, backup_file)
            
            return {
                'success': True,
                'backup_path': str(backup_file),
                'timestamp': backup_timestamp
            }
        else:
            return {
                'success': False,
                'error': 'Source inventory file not found'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def _validate_system_configuration() -> Dict[str, Any]:
    """Validate system configuration before update."""
    try:
        config_manager = ConfigManager()
        validation_results = config_manager.validate_all_configurations()
        
        errors = []
        for config_type, is_valid in validation_results.items():
            if not is_valid:
                errors.append(f"{config_type} configuration is invalid")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'details': validation_results
        }
        
    except Exception as e:
        return {
            'valid': False,
            'errors': [f"Configuration validation failed: {str(e)}"],
            'details': {}
        }


def _validate_uploaded_files(uploaded_files: Dict[str, str], supplier_codes: List[str]) -> Dict[str, Any]:
    """Validate uploaded files before processing."""
    try:
        errors = []
        
        # Check that all selected suppliers have uploaded files
        for supplier_code in supplier_codes:
            if supplier_code not in uploaded_files:
                errors.append(f"No uploaded file found for supplier {supplier_code}")
            else:
                file_path = uploaded_files[supplier_code]
                if not os.path.exists(file_path):
                    errors.append(f"Uploaded file not found: {file_path}")
                elif os.path.getsize(file_path) == 0:
                    errors.append(f"Uploaded file is empty: {file_path}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
        
    except Exception as e:
        return {
            'valid': False,
            'errors': [f"File validation failed: {str(e)}"]
        }


def _display_enhanced_completion_results(results: Dict[str, Any], update_log: List[str]):
    """Display enhanced completion results with detailed information and notifications."""
    
    if results.get('success', False):
        # Success notification with celebration
        st.balloons()
        st.success("🎉 Inventory Update Completed Successfully!")
        
        # Display comprehensive summary
        st.subheader("📊 Update Summary")
        
        # Main metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            suppliers_processed = results.get('suppliers_processed', 0)
            total_suppliers = results.get('total_suppliers', 0)
            st.metric(
                "Suppliers Processed", 
                f"{suppliers_processed}/{total_suppliers}",
                delta=f"{suppliers_processed} successful" if suppliers_processed > 0 else None
            )
        
        with col2:
            total_records = results.get('total_records', 0)
            st.metric("Total Records", f"{total_records:,}")
        
        with col3:
            update_duration = results.get('update_duration', 'Unknown')
            st.metric("Duration", update_duration)
        
        with col4:
            completion_time = results.get('update_end_time', '')
            if completion_time:
                try:
                    completion_dt = datetime.fromisoformat(completion_time.replace('Z', '+00:00'))
                    st.metric("Completed At", completion_dt.strftime("%H:%M:%S"))
                except:
                    st.metric("Status", "✅ Complete")
            else:
                st.metric("Status", "✅ Complete")
        
        # Detailed supplier results
        if 'supplier_results' in results:
            st.subheader("🏢 Supplier Details")
            
            # Create tabs for each supplier
            supplier_results = results['supplier_results']
            if supplier_results:
                supplier_tabs = st.tabs(list(supplier_results.keys()))
                
                for i, (supplier_code, supplier_result) in enumerate(supplier_results.items()):
                    with supplier_tabs[i]:
                        if supplier_result.get('success', False):
                            st.success(f"✅ {supplier_code} processed successfully")
                            
                            # Supplier metrics
                            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                            
                            with metrics_col1:
                                records = supplier_result.get('records_processed', supplier_result.get('records', 0))
                                st.metric("Records Processed", f"{records:,}")
                            
                            with metrics_col2:
                                files = supplier_result.get('files_downloaded', 0)
                                st.metric("Files Downloaded", files)
                            
                            with metrics_col3:
                                source = supplier_result.get('processing_source', 'unknown')
                                st.metric("Data Source", source.replace('_', ' ').title())
                            
                            # Downloaded files list
                            downloaded_files = supplier_result.get('downloaded_files', [])
                            if downloaded_files:
                                st.write("**Downloaded Files:**")
                                for file_path in downloaded_files:
                                    file_name = Path(file_path).name
                                    file_size = format_file_size(os.path.getsize(file_path)) if os.path.exists(file_path) else "Unknown"
                                    st.write(f"📄 {file_name} ({file_size})")
                            
                            # Data quality information
                            data_quality = supplier_result.get('data_quality', {})
                            if data_quality:
                                st.write("**Data Quality:**")
                                for metric, value in data_quality.items():
                                    st.write(f"- {metric.replace('_', ' ').title()}: {value}")
                            
                            # Validation warnings
                            validation_warnings = supplier_result.get('validation_warnings', [])
                            if validation_warnings:
                                st.warning("⚠️ Data validation warnings:")
                                for warning in validation_warnings:
                                    st.write(f"- {warning}")
                        
                        else:
                            st.error(f"❌ {supplier_code} failed")
                            error_msg = supplier_result.get('error', 'Unknown error')
                            st.error(f"Error: {error_msg}")
        
        # Display warnings if any
        warnings = results.get('warnings', [])
        if warnings:
            st.subheader("⚠️ Warnings")
            for warning in warnings:
                st.warning(f"⚠️ {warning}")
        
        # Success actions
        st.subheader("🎯 Next Steps")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 View Updated Inventory", type="secondary"):
                st.info("Navigate to Dashboard to view updated inventory data")
        
        with col2:
            if st.button("📈 Generate Reports", type="secondary"):
                st.info("Navigate to Sales Reports to generate updated reports")
        
        with col3:
            if st.button("🔄 Run Another Update", type="secondary"):
                # Clear results to allow another update
                st.session_state.inventory_update_state['last_update_results'] = None
                st.success("✅ Ready for another update! Please refresh the page or scroll up to start again.")
    
    else:
        # Failure notification
        st.error("❌ Inventory Update Failed")
        
        error_msg = results.get('error', 'Unknown error occurred')
        st.error(f"**Error:** {error_msg}")
        
        # Display any partial results
        if 'supplier_results' in results:
            st.subheader("📊 Partial Results")
            
            success_count = 0
            total_count = len(results['supplier_results'])
            
            for supplier_code, supplier_result in results['supplier_results'].items():
                if supplier_result.get('success', False):
                    success_count += 1
                    st.success(f"✅ {supplier_code}: {supplier_result.get('records_processed', 0)} records processed")
                else:
                    st.error(f"❌ {supplier_code}: {supplier_result.get('error', 'Failed')}")
            
            if success_count > 0:
                st.info(f"💡 {success_count}/{total_count} suppliers were processed successfully before the error occurred")
        
        # Error recovery actions
        st.subheader("🔧 Recovery Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Retry Update", type="primary"):
                # Clear error results and allow retry
                st.session_state.inventory_update_state['last_update_results'] = None
                st.info("✅ Ready to retry! Please refresh the page or scroll up to start again.")
        
        with col2:
            if st.button("📞 Contact Support", type="secondary"):
                st.info("Please contact IT support with the error details above")
    
    # Update log section
    if update_log:
        with st.expander("📋 Detailed Update Log", expanded=False):
            st.subheader("Update Log")
            log_text = "\n".join([f"{i+1:02d}. {entry}" for i, entry in enumerate(update_log)])
            st.text_area("Log Entries", log_text, height=300, disabled=True)
            
            # Download log button
            log_content = f"Inventory Update Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            log_content += "=" * 60 + "\n\n"
            log_content += log_text
            
            st.download_button(
                "📥 Download Log File",
                log_content,
                file_name=f"inventory_update_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )


def _cleanup_temp_files():
    """Clean up temporary uploaded files."""
    try:
        temp_dir = Path("temp_uploads")
        if temp_dir.exists():
            for file_path in temp_dir.glob("*"):
                try:
                    file_path.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete temp file {file_path}: {e}")
            
            # Try to remove directory if empty
            try:
                temp_dir.rmdir()
            except OSError:
                pass  # Directory not empty or other issue
                
        # Clear uploaded files from session state
        if 'uploaded_files' in st.session_state.inventory_update_state:
            st.session_state.inventory_update_state['uploaded_files'] = {}
            
    except Exception as e:
        logger.warning(f"Error cleaning up temp files: {e}")