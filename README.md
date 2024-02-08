# Inventory Manager

## Description
Inventory Manager is designed to streamline the process of managing suppliers' inventory statuses and handling Amazon orders efficiently. It automates the retrieval of inventory report files from Google Mail, updates inventory status in a Microsoft SQL POS database, manages Amazon Marketplace item listings, and generates comprehensive sales reports for in-store inventory checks and ordering processes. This tool is essential for businesses looking to optimize their inventory management and sales reporting with minimal manual intervention.

## Features
- **Email Integration**: Automatically retrieves suppliers' inventory report files from Google Mail using SMTP.
- **Database Updates**: Updates the Microsoft SQL POS database with the latest inventory statuses from suppliers.
- **Amazon Marketplace Integration**: Manages Amazon Marketplace item listings and updates store inventory data on Amazon.
- **Order Management**: Retrieves Amazon order lists and generates item order forms for efficient order processing.
- **Sales Reporting**: Generates detailed sales reports for in-store inventory checks and ordering, facilitating better inventory management.

## Technology Stack
- **Amazon Seller Partner API (SP-API)**: For integrating with Amazon Marketplace to manage listings and orders.
- **Square API**: Utilized for payment processing and sales data (assumed based on mention, specifics not provided).
- **Microsoft SQL**: Serves as the backend database for storing inventory and order data.
- **Python**: The primary programming language used for developing Inventory Manager, handling data processing, API communication, and automation tasks.

## Installation
- No installation needed. Packed as an exe file through Nuitka.
