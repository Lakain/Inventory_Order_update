"""
Helper utilities and common functions for the Streamlit application.
"""

import streamlit as st
import json
import os
from pathlib import Path
from typing import Dict, Any
from utils.logging import get_logger

logger = get_logger(__name__)

def check_system_health() -> Dict[str, Any]:
    """
    Check system health and connectivity status.
    
    Returns:
        Dictionary with status and message
    """
    try:
        # Check if required configuration files exist
        config_files = [
            "appdata/db_auth.json",
            "appdata/api_keys.json", 
            "appdata/keyword_mailadd.json"
        ]
        
        missing_files = []
        for config_file in config_files:
            if not os.path.exists(config_file):
                missing_files.append(config_file)
        
        if missing_files:
            return {
                "status": "warning",
                "message": f"Missing configuration files: {', '.join(missing_files)}"
            }
        
        # Basic health check passed
        return {
            "status": "healthy",
            "message": "All systems operational"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}"
        }

def handle_error(error: Exception, context: str = ""):
    """
    Centralized error handling for Streamlit UI.
    
    Args:
        error: The exception that occurred
        context: Context where the error occurred
    """
    error_message = str(error)
    logger.error(f"Error in {context}: {error_message}")
    
    # Display user-friendly error messages
    if "database" in error_message.lower() or "connection" in error_message.lower():
        st.error("❌ Database connection failed. Please check network connectivity.")
        st.info("💡 Try refreshing the page or contact IT support.")
    elif "email" in error_message.lower() or "authentication" in error_message.lower():
        st.error("❌ Email authentication failed.")
        st.info("💡 You can upload files manually using the file uploader below.")
    elif "amazon" in error_message.lower() or "api" in error_message.lower():
        st.error(f"❌ Amazon API error: {error_message}")
        st.info("💡 This may be temporary. Try again in a few minutes.")
    else:
        st.error(f"❌ Unexpected error in {context}: {error_message}")
        st.info("💡 Please contact support if this persists.")

def load_json_config(file_path: str) -> Dict[str, Any]:
    """
    Load JSON configuration file with error handling.
    
    Args:
        file_path: Path to JSON configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If configuration file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {file_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file {file_path}: {str(e)}")
        raise

def create_progress_callback(progress_bar, status_container):
    """
    Create a progress callback function for long-running operations.
    
    Args:
        progress_bar: Streamlit progress bar component
        status_container: Streamlit container for status messages
        
    Returns:
        Callback function that updates progress and status
    """
    def callback(step: str, progress: float):
        """
        Update progress bar and status message.
        
        Args:
            step: Description of current step
            progress: Progress value between 0.0 and 1.0
        """
        if status_container:
            status_container.info(f"🔄 {step}")
        if progress_bar:
            progress_bar.progress(progress)
        logger.info(f"Progress: {progress:.1%} - {step}")
    
    return callback

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def validate_required_files() -> Dict[str, bool]:
    """
    Validate that all required files and directories exist.
    
    Returns:
        Dictionary mapping file paths to existence status
    """
    required_paths = [
        "appdata/",
        "appdata/db_auth.json",
        "appdata/api_keys.json",
        "appdata/keyword_mailadd.json"
    ]
    
    validation_results = {}
    for path in required_paths:
        validation_results[path] = os.path.exists(path)
    
    return validation_results