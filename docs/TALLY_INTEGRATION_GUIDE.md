# Tally Integration for ERPNext - Usage Guide

This guide provides comprehensive instructions for using the Tally Integration app with ERPNext.

## Overview

The Tally Integration app connects ERPNext with TallyPrime/Tally.ERP 9 using the `tally-integration` Python package. It enables bidirectional data synchronization and transaction management between the two systems.

## Installation

### 1. Install the App

```bash
cd frappe-bench
bench get-app https://github.com/your-repo/tally_integration --branch develop
bench install-app tally_integration
```

### 2. Install Dependencies

```bash
cd apps/tally_integration
pip install -e .
```

This will install the `tally-integration` package (v1.0.0) and its dependencies.

### 3. Enable XML API in Tally

1. Open Tally
2. Go to Gateway of Tally → F12: Configure → Advanced Configuration
3. Enable "Allow XML Request" option
4. Set the port (default: 9000)
5. Restart Tally

## Configuration

### Tally Settings

1. In ERPNext, go to **Tally Settings** (Search in Awesome Bar)
2. Configure the following:
   - **Enabled**: Check to enable Tally integration
   - **Host**: Tally server host (default: localhost)
   - **Port**: Tally server port (default: 9000)
3. Click **Test Connection** to verify connectivity
4. Save the settings

### Auto Sync Settings (Optional)

Enable automatic synchronization for:
- Customers (Sundry Debtors from Tally)
- Suppliers (Sundry Creditors from Tally)
- Items (Stock Items from Tally)
- Sales Invoices
- Purchase Invoices

## Usage

### 1. Basic Connection Test

```python
import frappe
from tally_integration.tally import TallyClient

# Create client instance
client = TallyClient()

# Test connection
if client.test_connection():
    print("Connected to Tally successfully!")

# Get current company info
company = client.get_current_company()
print(f"Company: {company}")
```

### 2. Retrieve Data from Tally

#### Get Companies

```python
from tally_integration.tally import TallyClient

client = TallyClient()
companies = client.get_companies()
for company in companies:
    print(company)
```

#### Get Ledgers

```python
# Get all ledgers
ledgers = client.get_ledgers()

# Get ledgers for specific company
ledgers = client.get_ledgers(company="My Company")
```

#### Get Stock Items

```python
# Get all stock items
items = client.get_stock_items()

# Get items for specific company
items = client.get_stock_items(company="My Company")
```

#### Get Vouchers

```python
# Get all vouchers
vouchers = client.get_vouchers()

# Get specific voucher type
sales_vouchers = client.get_vouchers(voucher_type="Sales")

# Get vouchers within date range
vouchers = client.get_vouchers(
    voucher_type="Sales",
    from_date="2025-01-01",
    to_date="2025-12-31"
)
```

### 3. Create Master Data in Tally

#### Create Ledger (Customer/Supplier)

```python
# Create a customer ledger
response = client.create_ledger(
    name="ABC Corporation",
    parent="Sundry Debtors",
    address="123 Business Street, City, State",
    mobile="9876543210",
    email="contact@abc.com"
)
```

#### Create Stock Item

```python
# Create a stock item
response = client.create_stock_item(
    name="Product XYZ",
    category="Finished Goods",
    unit="Nos"
)
```

### 4. Create Vouchers in Tally

#### Create Sales Voucher

```python
# Prepare ledger entries
ledger_entries = [
    {
        "ledger_name": "ABC Corporation",
        "amount": 11800,
        "is_debit": True
    },
    {
        "ledger_name": "Sales",
        "amount": 10000,
        "is_debit": False
    },
    {
        "ledger_name": "CGST",
        "amount": 900,
        "is_debit": False
    },
    {
        "ledger_name": "SGST",
        "amount": 900,
        "is_debit": False
    }
]

# Create voucher
response = client.create_voucher(
    voucher_type="Sales",
    date="2025-12-10",
    ledger_entries=ledger_entries,
    narration="Sale of goods to ABC Corporation"
)
```

### 5. Synchronization Functions

#### Sync Customers from Tally to ERPNext

```python
from tally_integration.tally.utils import sync_customers

# Sync all customers
result = sync_customers()
print(f"Created: {result['created']}, Updated: {result['updated']}, Skipped: {result['skipped']}")
```

#### Sync Items from Tally to ERPNext

```python
from tally_integration.tally.utils import sync_items

# Sync all items
result = sync_items()
print(f"Created: {result['created']}, Updated: {result['updated']}, Skipped: {result['skipped']}")
```

#### Push Sales Invoice to Tally

```python
from tally_integration.tally.utils import push_sales_invoice

# Push a specific sales invoice
result = push_sales_invoice("SINV-2025-00001")
print(f"Tally Voucher Number: {result['tally_response']['voucher_number']}")
```

#### Create Customer in Tally from ERPNext

```python
from tally_integration.tally.utils import create_customer_in_tally

# Create customer in Tally
response = create_customer_in_tally("ABC Corporation")
```

#### Create Item in Tally from ERPNext

```python
from tally_integration.tally.utils import create_item_in_tally

# Create item in Tally
response = create_item_in_tally("ITEM-001")
```

### 6. API Endpoints

All API endpoints are whitelisted and can be called via HTTP or from frontend JavaScript:

```javascript
// Test connection
frappe.call({
    method: "tally_integration.tally.test_tally_connection",
    args: {
        host: "localhost",
        port: 9000
    },
    callback: function(r) {
        console.log(r.message);
    }
});

// Get companies
frappe.call({
    method: "tally_integration.tally.api.get_companies",
    callback: function(r) {
        if (r.message.success) {
            console.log(r.message.data);
        }
    }
});

// Sync customers
frappe.call({
    method: "tally_integration.tally.api.sync_customers_from_tally",
    freeze: true,
    freeze_message: "Syncing customers from Tally...",
    callback: function(r) {
        if (r.message.success) {
            frappe.msgprint(`Synced ${r.message.data.created + r.message.data.updated} customers`);
        }
    }
});
```

## Available API Methods

### Connection & Configuration
- `test_tally_connection(host, port)` - Test Tally connection

### Master Data Retrieval
- `get_companies()` - Get all companies
- `get_current_company()` - Get current company
- `get_ledgers(company)` - Get all ledgers
- `get_stock_items(company)` - Get all stock items
- `get_groups(group_type)` - Get groups
- `get_vouchers(voucher_type, from_date, to_date)` - Get vouchers

### Master Data Creation
- `create_ledger(name, parent, address, mobile, email)` - Create ledger
- `create_stock_item(name, category, unit)` - Create stock item
- `create_voucher(voucher_type, date, ledger_entries, narration)` - Create voucher

### Synchronization
- `sync_customers_from_tally()` - Sync customers from Tally
- `sync_items_from_tally()` - Sync items from Tally
- `push_sales_invoice_to_tally(sales_invoice_name)` - Push sales invoice to Tally

## Hooks & Automation

You can add hooks to automatically sync data on document events. Add to `hooks.py`:

```python
doc_events = {
    "Customer": {
        "after_insert": "tally_integration.tally.hooks.customer_after_insert",
        "on_update": "tally_integration.tally.hooks.customer_on_update"
    },
    "Sales Invoice": {
        "on_submit": "tally_integration.tally.hooks.sales_invoice_on_submit"
    }
}
```

## Troubleshooting

### Connection Issues

1. Ensure Tally is running and XML API is enabled
2. Check firewall settings if connecting to remote Tally
3. Verify host and port in Tally Settings
4. Test connection from Tally Settings page

### Data Sync Issues

1. Check Error Log in ERPNext for detailed error messages
2. Verify data format matches Tally requirements
3. Ensure required fields are populated
4. Check for duplicate records

### Common Errors

**TallyConnectionError**: Tally is not running or XML API is disabled
- Solution: Start Tally and enable XML API

**Ledger already exists**: Trying to create duplicate ledger
- Solution: Use update methods or check for existing records first

**Invalid voucher format**: Ledger entries don't balance
- Solution: Ensure debit and credit entries are equal

## Best Practices

1. **Test in Development First**: Always test synchronization in a development environment
2. **Backup Data**: Take backups of both ERPNext and Tally before bulk operations
3. **Incremental Sync**: Sync data in small batches rather than all at once
4. **Error Handling**: Monitor Error Logs regularly for sync issues
5. **Field Mapping**: Customize field mappings in utils.py as per your requirements
6. **Performance**: Use scheduled jobs for large data synchronization

## Advanced Usage

### Custom Field Mappings

Modify `tally_integration/tally/utils.py` to customize how ERPNext data maps to Tally:

```python
def map_erpnext_customer_to_tally_ledger(customer_name):
    customer = frappe.get_doc("Customer", customer_name)

    return {
        "name": customer.customer_name,
        "parent": "Sundry Debtors",
        "address": customer.primary_address or "",
        "mobile": customer.mobile_no or "",
        "email": customer.email_id or "",
        # Add custom fields here
        "custom_field": customer.custom_field
    }
```

### Scheduled Tasks

Add to `hooks.py` for automatic synchronization:

```python
scheduler_events = {
    "daily": [
        "tally_integration.tally.tasks.sync_daily_transactions"
    ],
    "hourly": [
        "tally_integration.tally.tasks.sync_new_customers"
    ]
}
```

## Support & Resources

- **PyPI Package**: https://pypi.org/project/tally-integration/
- **GitHub Repository**: https://github.com/aadil-sengupta/Tally.Py
- **ERPNext Documentation**: https://docs.erpnext.com
- **Tally Documentation**: https://help.tallysolutions.com

## License

GPL v3.0
