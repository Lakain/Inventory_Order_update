#!/usr/bin/env python3
"""
Startup script for the Streamlit Inventory Management System.
Handles server initialization and configuration validation.
"""

import os
import sys
import subprocess
from pathlib import Path
from utils.helpers import validate_required_files, check_system_health

def check_dependencies():
    """Check if required Python packages are installed."""
    try:
        import streamlit
        import pandas
        import sqlalchemy
        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def validate_environment():
    """Validate the environment and configuration files."""
    print("🔍 Validating environment...")
    
    # Check required files
    file_status = validate_required_files()
    missing_files = [path for path, exists in file_status.items() if not exists]
    
    if missing_files:
        print("⚠️  Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all configuration files are in place.")
        return False
    
    print("✅ All required files found")
    
    # Check system health
    health = check_system_health()
    if health["status"] == "error":
        print(f"❌ System health check failed: {health['message']}")
        return False
    elif health["status"] == "warning":
        print(f"⚠️  System warning: {health['message']}")
    else:
        print("✅ System health check passed")
    
    return True

def start_server(network_mode=False):
    """Start the Streamlit server."""
    print("🚀 Starting Streamlit server...")
    
    # Build command
    cmd = ["streamlit", "run", "app.py"]
    
    if network_mode:
        cmd.extend(["--server.address", "0.0.0.0"])
        cmd.extend(["--server.port", "8501"])
        print("🌐 Server will be accessible on the network")
    else:
        print("🏠 Server will be accessible locally only")
    
    # Start server
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

def main():
    """Main startup function."""
    print("📦 Streamlit Inventory Management System")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Validate environment
    if not validate_environment():
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Ask for network mode
    print("\nServer Mode:")
    print("1. Local only (localhost)")
    print("2. Network accessible (all PCs)")
    
    while True:
        choice = input("Select mode (1 or 2): ").strip()
        if choice == "1":
            start_server(network_mode=False)
            break
        elif choice == "2":
            start_server(network_mode=True)
            break
        else:
            print("Please enter 1 or 2")

if __name__ == "__main__":
    main()