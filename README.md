### Tally Integration for ERPNext

A comprehensive integration app that connects ERPNext with TallyPrime/Tally.ERP 9 using the [tally-integration](https://pypi.org/project/tally-integration/) Python package.

## Features

- **Bidirectional Data Sync**: Sync customers, suppliers, items, and transactions between ERPNext and Tally
- **Real-time Integration**: Push Sales Invoices, Purchase Invoices, and other vouchers to Tally
- **Master Data Management**: Create and manage ledgers, stock items, and groups in Tally from ERPNext
- **Transaction Processing**: Create vouchers (Sales, Purchase, Receipt, Payment, Journal) in Tally
- **Auto Sync**: Optional automatic synchronization on document events
- **REST API**: Whitelisted API endpoints for custom integrations
- **Connection Testing**: Built-in connection testing and validation

## Prerequisites

- Frappe/ERPNext v15.0+
- Python 3.10+
- TallyPrime or Tally.ERP 9 with XML API enabled
- Tally server accessible from ERPNext server

## Installation

### 1. Get and Install the App

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/svnix-solutions/tally_erpnext --branch develop
bench install-app tally_erpnext
```

### 2. Install Dependencies

The app uses the `tally-integration` PyPI package which will be automatically installed:

```bash
cd apps/tally_erpnext
pip install -e .
```

### 3. Configure Tally

1. Open Tally
2. Go to **Gateway of Tally → F12: Configure → Advanced Configuration**
3. Enable **"Allow XML Request"** option
4. Set the port (default: 9000)
5. Restart Tally

### 4. Configure ERPNext

1. In ERPNext, search for **Tally Settings** in the Awesome Bar
2. Enable the integration and configure:
   - **Host**: localhost (or Tally server IP)
   - **Port**: 9000 (or your configured port)
3. Click **Test Connection** to verify
4. Save settings

## Quick Start

### Test Connection

```python
from tally_erpnext.tally import TallyClient

client = TallyClient()
if client.test_connection():
    print("Connected successfully!")
```

### Sync Customers from Tally

```python
from tally_erpnext.tally.utils import sync_customers

result = sync_customers()
print(f"Synced {result['created']} customers")
```

### Push Sales Invoice to Tally

```python
from tally_erpnext.tally.utils import push_sales_invoice

result = push_sales_invoice("SINV-2025-00001")
print(f"Created voucher: {result['tally_response']['voucher_number']}")
```

## Architecture

This integration uses a **DocType-based architecture** with 1:1 mapping between Tally entities and ERPNext DocTypes:

- **Tally Ledger** ↔ Tally Ledgers (Customers, Suppliers, Accounts)
- **Tally Stock Item** ↔ Tally Stock Items
- **Tally Voucher** ↔ Tally Vouchers (Sales, Purchase, Payment, etc.)
- **Tally Sync Log** → Audit trail for all sync operations

### Two-Way Sync with Server Scripts

Use **Server Scripts** to manage automatic synchronization:
- Customer creation → Auto-creates Tally Ledger → Syncs to Tally
- Sales Invoice submission → Creates Tally Voucher → Syncs to Tally
- Scheduled jobs → Pull data from Tally → Creates/updates ERPNext records

## Documentation

📚 **[Documentation Index](./docs/README.md)** - Complete documentation hub

### Quick Links

- **[Quick Start Guide](./docs/QUICK_START_DOCTYPE.md)** - Get started in 5 minutes ⚡
- **[Installation Guide](./docs/INSTALLATION.md)** - Step-by-step installation instructions 📦
- **[Architecture Guide](./docs/DOCTYPE_ARCHITECTURE.md)** - Complete architecture with DocTypes 🏗️
- **[API Reference](./docs/TALLY_INTEGRATION_GUIDE.md)** - Detailed usage and API reference 📖
- **[Server Scripts Guide](./docs/SERVER_SCRIPTS_GUIDE.md)** - Ready-to-use Server Scripts 🔧
- **[Implementation Summary](./docs/IMPLEMENTATION_SUMMARY.md)** - Complete implementation overview 📋
- **[Project Structure](./docs/PROJECT_STRUCTURE.md)** - File structure and organization 📁

## Available Operations

### Master Data
- Get/Create Companies
- Get/Create Ledgers (Customers, Suppliers, Accounts)
- Get/Create Stock Items
- Get Groups

### Transactions
- Get/Create Vouchers (Sales, Purchase, Receipt, Payment, Journal)
- Get Voucher Reports

### Synchronization
- Sync Customers (Tally → ERPNext)
- Sync Suppliers (Tally → ERPNext)
- Sync Items (Tally → ERPNext)
- Push Sales Invoices (ERPNext → Tally)
- Push Purchase Invoices (ERPNext → Tally)

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/tally_erpnext
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

gpl-3.0
