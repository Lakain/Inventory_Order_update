# Streamlit Inventory Management System

A web-based inventory management system migrated from PySide6 desktop application to Streamlit.

## Project Structure

```
streamlit_inventory/
├── app.py                    # Main Streamlit application entry point
├── pages/                    # Streamlit page modules
│   ├── __init__.py
│   ├── dashboard.py          # System overview dashboard
│   ├── inventory_update.py   # Supplier inventory processing
│   ├── amazon_orders.py      # Amazon order analysis
│   └── sales_reports.py      # Sales reporting
├── services/                 # Business logic services (to be implemented)
│   └── __init__.py
├── models/                   # Data models and configurations (to be implemented)
│   └── __init__.py
├── utils/                    # Utility functions
│   ├── __init__.py
│   ├── logging.py           # Logging configuration
│   └── helpers.py           # Common helper functions
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure required configuration files exist in the parent directory:
   - `appdata/db_auth.json` - Database authentication
   - `appdata/api_keys.json` - Amazon API credentials
   - `appdata/keyword_mailadd.json` - Supplier email configurations

## Running the Application

### Development Mode
```bash
streamlit run app.py
```

### Production Mode (Network Access)
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

The application will be accessible at:
- Local: http://localhost:8501
- Network: http://[server-ip]:8501

## Features

- **Dashboard**: System status overview and quick actions
- **Inventory Update**: Automated supplier inventory processing via email
- **Amazon Order Analysis**: Order analysis and inventory planning
- **Sales Reports**: POS data analysis and reporting

## Configuration

The application uses existing configuration files from the desktop version:
- Database connections via `appdata/db_auth.json`
- Amazon API credentials via `appdata/api_keys.json`
- Supplier configurations via `appdata/keyword_mailadd.json`

## Logging

Application logs are stored in the `logs/` directory with daily rotation.
Log level can be configured in `.streamlit/config.toml`.

## Network Deployment

For multi-PC access on local network:
1. Run the application on a designated server PC
2. Configure firewall to allow port 8501
3. Access from client PCs using server IP address
4. No client-side installation required

## Development Status

This is the initial project structure. Individual features will be implemented in subsequent development phases according to the implementation plan.