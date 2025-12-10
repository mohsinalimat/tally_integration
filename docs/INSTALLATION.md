# Installation Guide - Tally Integration for ERPNext

## Prerequisites

Before installing, ensure you have:

1. **Frappe/ERPNext v15.0+** installed and running
2. **Python 3.10+**
3. **TallyPrime or Tally.ERP 9** with XML API enabled
4. Network connectivity between ERPNext and Tally servers

## Step 1: Enable XML API in Tally

1. Open Tally
2. Navigate to: **Gateway of Tally → F12: Configure → Advanced Configuration**
3. Enable **"Allow XML Request"** option
4. Set Port: **9000** (default, or choose your preferred port)
5. **Restart Tally** for changes to take effect

### Verify XML API is Running

You can test if the XML API is accessible by running this command from your terminal:

```bash
curl -X POST http://localhost:9000 -d '<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Data</TYPE><ID>Voucher Types</ID></HEADER><BODY><DESC></DESC></BODY></ENVELOPE>'
```

If you see XML output, the API is working correctly.

## Step 2: Install the Tally Integration App

### Method 1: Install from Git Repository

```bash
cd /path/to/frappe-bench

# Get the app
bench get-app https://github.com/your-org/tally_integration --branch develop

# Install the app on your site
bench --site your-site-name install-app tally_integration

# Install dependencies
cd apps/tally_integration
pip install -e .

# Migrate database
bench --site your-site-name migrate

# Restart bench
bench restart
```

### Method 2: Install for Development

```bash
cd /path/to/frappe-bench/apps

# Clone the repository
git clone https://github.com/your-org/tally_integration
cd tally_integration

# Install in development mode
pip install -e .

# Install on site
cd ../..
bench --site your-site-name install-app tally_integration
bench --site your-site-name migrate
bench restart
```

## Step 3: Verify Installation

1. Open your ERPNext site
2. Search for **"Tally Settings"** in the Awesome Bar
3. If the page opens, installation is successful!

## Step 4: Configure Tally Integration

1. Open **Tally Settings** (search in Awesome Bar)
2. Configure the following:
   - **Enabled**: Check this box to enable integration
   - **Tally Server Host**:
     - `localhost` if Tally is on same machine
     - IP address if Tally is on another machine (e.g., `192.168.1.100`)
   - **Tally Server Port**: `9000` (or your configured port)
3. Click **Test Connection** button
4. You should see: ✓ "Successfully connected to Tally server"
5. **Save** the settings

### Connection Status

- **Green**: Connection successful
- **Red**: Connection failed - check:
  - Is Tally running?
  - Is XML API enabled?
  - Are host/port correct?
  - Firewall blocking connection?

## Step 5: Optional Configuration

### Enable Auto Sync

In Tally Settings, you can enable automatic synchronization:

- ☑ Auto Sync Customers
- ☑ Auto Sync Suppliers
- ☑ Auto Sync Items
- ☑ Auto Sync Sales Invoices
- ☑ Auto Sync Purchase Invoices

**Note**: Auto sync will trigger on document save/submit events.

### Add Custom Fields (Optional)

If you want to track Tally references in ERPNext documents:

```bash
bench --site your-site-name console
```

Then run:

```python
# Add custom field to Customer
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

custom_fields = {
    "Customer": [
        {
            "fieldname": "tally_ledger_name",
            "label": "Tally Ledger Name",
            "fieldtype": "Data",
            "insert_after": "customer_name",
            "read_only": 1
        }
    ],
    "Item": [
        {
            "fieldname": "tally_item_name",
            "label": "Tally Item Name",
            "fieldtype": "Data",
            "insert_after": "item_name",
            "read_only": 1
        }
    ],
    "Sales Invoice": [
        {
            "fieldname": "tally_voucher_number",
            "label": "Tally Voucher Number",
            "fieldtype": "Data",
            "insert_after": "naming_series",
            "read_only": 1
        }
    ]
}

create_custom_fields(custom_fields, update=True)
```

## Step 6: Test the Integration

### Test 1: Connection Test

```python
# Run from bench console
bench --site your-site-name console

from tally_integration.tally import TallyClient

client = TallyClient()
if client.test_connection():
    print("✓ Connection successful!")
else:
    print("✗ Connection failed")
```

### Test 2: Get Company Info

```python
from tally_integration.tally import TallyClient

client = TallyClient()
company = client.get_current_company()
print(f"Company: {company}")
```

### Test 3: Run Example Script

```bash
# From bench directory
bench --site your-site-name console
>>> exec(open('apps/tally_integration/examples/basic_usage.py').read())
```

## Troubleshooting

### Issue: "Failed to initialize Tally Client"

**Cause**: Cannot connect to Tally server

**Solutions**:
1. Verify Tally is running
2. Check XML API is enabled in Tally
3. Verify host/port settings in Tally Settings
4. Test connection: `curl -X POST http://localhost:9000`

### Issue: "Module 'tally_integration' not found"

**Cause**: Dependencies not installed

**Solution**:
```bash
cd apps/tally_integration
pip install -e .
bench restart
```

### Issue: "Tally Settings not found"

**Cause**: App not installed or migration not run

**Solution**:
```bash
bench --site your-site-name install-app tally_integration
bench --site your-site-name migrate
bench restart
```

### Issue: Connection works in console but not from UI

**Cause**: Bench not restarted after installation

**Solution**:
```bash
bench restart
# or for production
sudo supervisorctl restart all
```

### Issue: Firewall blocking connection

**For Windows Firewall**:
1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Add Tally.EXE
4. Allow on Private and Public networks

**For Linux Firewall (ufw)**:
```bash
sudo ufw allow 9000/tcp
```

## Remote Tally Connection

If Tally is on a different machine:

1. **On Tally Machine**:
   - Enable XML API in Tally (port 9000)
   - Note the IP address: `ipconfig` (Windows) or `ifconfig` (Linux)
   - Allow port 9000 through firewall

2. **On ERPNext Machine**:
   - In Tally Settings, set Host to Tally machine IP (e.g., `192.168.1.100`)
   - Test connection

3. **Test from Terminal**:
   ```bash
   curl -X POST http://192.168.1.100:9000 -d '<ENVELOPE>...</ENVELOPE>'
   ```

## Uninstallation

If you need to uninstall:

```bash
# Uninstall from site
bench --site your-site-name uninstall-app tally_integration

# Remove app files (optional)
rm -rf apps/tally_integration
```

## Next Steps

After successful installation:

1. Read [TALLY_INTEGRATION_GUIDE.md](./TALLY_INTEGRATION_GUIDE.md) for usage instructions
2. Try the examples in [examples/basic_usage.py](./examples/basic_usage.py)
3. Configure auto-sync settings as per your requirements
4. Set up scheduled tasks for regular synchronization

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the documentation in TALLY_INTEGRATION_GUIDE.md
- Check error logs: ERPNext → Error Log
- GitHub Issues: [Report an issue]

## Version Compatibility

| Component | Version |
|-----------|---------|
| Frappe/ERPNext | v15.0+ |
| Python | 3.10+ |
| TallyPrime | All versions |
| Tally.ERP 9 | Release 6.6+ |
| tally-integration (PyPI) | 1.0.0+ |
