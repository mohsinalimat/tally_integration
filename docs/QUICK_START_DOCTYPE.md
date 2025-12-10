# Quick Start Guide - DocType Architecture

Get started with Tally Integration using the DocType-based architecture in 5 minutes!

## Step 1: Install and Configure (2 minutes)

```bash
# Install the app
cd frappe-bench
bench get-app tally_integration
bench install-app tally_integration
cd apps/tally_integration
pip install -e .
bench migrate
bench restart
```

**Configure Tally Settings**:
1. Open ERPNext → Search "Tally Settings"
2. Check "Enabled"
3. Host: `localhost`, Port: `9000`
4. Click "Test Connection"
5. Save

## Step 2: Initial Sync from Tally (1 minute)

Open **Console** (`bench console`) and run:

```python
from tally_integration.tally.doctype_sync import *

# Sync all ledgers from Tally
result = sync_ledgers_from_tally()
print(f"Ledgers: Created {result['created']}, Updated {result['updated']}")

# Sync all stock items from Tally
result = sync_stock_items_from_tally()
print(f"Items: Created {result['created']}, Updated {result['updated']}")

# Sync today's vouchers
from frappe.utils import today
result = sync_vouchers_from_tally(from_date=today(), to_date=today())
print(f"Vouchers: Created {result['created']}, Updated {result['updated']}")
```

**View synced data**:
- Tally Ledger list → See all Tally ledgers
- Tally Stock Item list → See all Tally items
- Tally Voucher list → See all Tally vouchers
- Tally Sync Log → See sync audit trail

## Step 3: Setup Auto-Sync with Server Scripts (2 minutes)

### Customer → Tally Ledger

1. Go to **Server Script** → New
2. Name: `Auto Create Tally Ledger for Customer`
3. DocType: `Customer`
4. Event: `After Insert`
5. Script:

```python
import frappe

settings = frappe.get_doc("Tally Settings", "Tally Settings")
if not settings.enabled:
    return

if frappe.db.exists("Tally Ledger", doc.customer_name):
    return

tally_ledger = frappe.get_doc({
    "doctype": "Tally Ledger",
    "ledger_name": doc.customer_name,
    "parent_group": "Sundry Debtors",
    "mobile": doc.mobile_no or "",
    "email": doc.email_id or "",
    "linked_doctype": "Customer",
    "linked_docname": doc.name,
    "auto_sync": 1,
    "sync_direction": "Bidirectional"
})
tally_ledger.insert(ignore_permissions=True)
frappe.msgprint(f"Tally Ledger created: {tally_ledger.name}", alert=True)
```

6. Enable and Save

### Sales Invoice → Tally Voucher

1. Go to **Server Script** → New
2. Name: `Create Tally Voucher for Sales Invoice`
3. DocType: `Sales Invoice`
4. Event: `On Submit`
5. Script:

```python
import frappe

settings = frappe.get_doc("Tally Settings", "Tally Settings")
if not settings.enabled:
    return

tally_voucher = frappe.get_doc({
    "doctype": "Tally Voucher",
    "voucher_type": "Sales",
    "date": doc.posting_date,
    "party_ledger_name": doc.customer_name,
    "narration": f"Sales Invoice {doc.name}",
    "linked_doctype": "Sales Invoice",
    "linked_docname": doc.name,
    "auto_sync": 1
})

# Customer (Debit)
tally_voucher.append("ledger_entries", {
    "ledger_name": doc.customer_name,
    "is_debit": 1,
    "amount": doc.grand_total
})

# Sales (Credit)
tally_voucher.append("ledger_entries", {
    "ledger_name": "Sales",
    "is_debit": 0,
    "amount": doc.total
})

# Taxes (Credit)
for tax in doc.taxes:
    if tax.tax_amount > 0:
        tally_voucher.append("ledger_entries", {
            "ledger_name": tax.account_head,
            "is_debit": 0,
            "amount": tax.tax_amount
        })

tally_voucher.insert(ignore_permissions=True)
tally_voucher.submit()
frappe.msgprint(f"Tally Voucher created: {tally_voucher.name}", alert=True)
```

6. Enable and Save

## Step 4: Test the Integration

### Test 1: Create a Customer

1. Create a new Customer in ERPNext
2. You should see: "Tally Ledger created: [Customer Name]"
3. Go to **Tally Ledger** list → See the new ledger
4. Check **Tally Sync Log** → See the sync operation
5. Open Tally → Verify ledger created under "Sundry Debtors"

### Test 2: Create a Sales Invoice

1. Create and submit a Sales Invoice
2. You should see: "Tally Voucher created: TVCH-XXXX"
3. Go to **Tally Voucher** list → See the new voucher
4. Check **Tally Sync Log** → See the sync operation
5. Open Tally → Verify sales voucher created

### Test 3: Sync from Tally

1. Create a new ledger in Tally (under Sundry Debtors)
2. In ERPNext Console:
   ```python
   from tally_integration.tally.doctype_sync import sync_ledgers_from_tally
   result = sync_ledgers_from_tally(parent_group="Sundry Debtors")
   print(result)
   ```
3. Go to **Tally Ledger** list → See the new ledger

## What's Happening?

### Data Flow (ERP → Tally)

```
Customer Created
    ↓
Server Script Triggers
    ↓
Tally Ledger Created (auto_sync=1)
    ↓
after_insert Hook
    ↓
frappe.enqueue(sync_ledger_to_tally)
    ↓
Background Job Runs
    ↓
TallyClient.create_ledger()
    ↓
Ledger Created in Tally
    ↓
Tally Sync Log Created
```

### Data Flow (Tally → ERP)

```
Scheduled Job Runs
    ↓
sync_ledgers_from_tally()
    ↓
TallyClient.get_ledgers()
    ↓
For each ledger:
  - Create/Update Tally Ledger
  - Tally Sync Log Created
    ↓
Server Script (if configured)
    ↓
Create/Update Customer
```

## Core DocTypes

### 1. Tally Ledger
- **What**: 1:1 copy of Tally ledgers
- **Link**: Can link to Customer/Supplier/Account
- **Auto Sync**: When enabled, changes push to Tally

### 2. Tally Stock Item
- **What**: 1:1 copy of Tally stock items
- **Link**: Can link to Item
- **Auto Sync**: When enabled, changes push to Tally

### 3. Tally Voucher
- **What**: 1:1 copy of Tally vouchers
- **Link**: Can link to Sales Invoice/Purchase Invoice/Payment Entry
- **Auto Sync**: When enabled, submitting pushes to Tally

### 4. Tally Sync Log
- **What**: Audit trail for all sync operations
- **Use**: Debug issues, compliance, reporting

## Common Functions

```python
# Import
from tally_integration.tally.doctype_sync import *

# Sync from Tally
sync_ledgers_from_tally()  # All ledgers
sync_ledgers_from_tally(parent_group="Sundry Debtors")  # Customers only
sync_stock_items_from_tally()  # All items
sync_vouchers_from_tally(voucher_type="Sales")  # Sales vouchers

# Sync to Tally
sync_ledger_to_tally("Customer Name")
sync_stock_item_to_tally("Item Name")
sync_voucher_to_tally("TVCH-0001")

# Create sync log
create_sync_log(
    sync_type="Master Data",
    operation="Create",
    status="Success",
    direction="ERP to Tally",
    entity_type="Ledger",
    entity_name="ABC Corp"
)
```

## API Endpoints

```javascript
// From frontend JavaScript
frappe.call({
    method: "tally_integration.tally.doctype_sync.sync_all_ledgers",
    callback: function(r) {
        console.log(r.message);
    }
});
```

## Scheduled Jobs (Optional)

Add to `hooks.py`:

```python
scheduler_events = {
    "daily": [
        "tally_integration.tally.scheduled_tasks.daily_sync_from_tally"
    ]
}
```

Create `tally_integration/tally/scheduled_tasks.py`:

```python
import frappe
from tally_integration.tally.doctype_sync import *

def daily_sync_from_tally():
    settings = frappe.get_doc("Tally Settings", "Tally Settings")
    if not settings.enabled:
        return
    sync_ledgers_from_tally()
    sync_stock_items_from_tally()
```

## Troubleshooting

### Issue: Tally Ledger not syncing to Tally

**Check**:
1. Tally Ledger → auto_sync = ✓
2. Tally Ledger → sync_direction = "ERP to Tally" or "Bidirectional"
3. Tally Settings → Enabled = ✓
4. Tally Settings → Test Connection = Success
5. Error Log → Any errors?
6. Tally Sync Log → Check sync status

### Issue: Background job not running

**Solution**:
```bash
# Check if workers are running
bench doctor

# Restart workers
bench restart
```

### Issue: Duplicate records

**Solution**: Use `frappe.db.exists()` in Server Scripts before creating

## Next Steps

1. ✅ Read [DOCTYPE_ARCHITECTURE.md](./DOCTYPE_ARCHITECTURE.md) for complete architecture
2. ✅ Check [server_scripts_examples.md](./examples/server_scripts_examples.md) for more scripts
3. ✅ Customize sync logic for your needs
4. ✅ Add more Server Scripts for other DocTypes
5. ✅ Setup scheduled jobs for automatic sync

## Support

- Check **Tally Sync Log** for all operations
- Check **Error Log** for errors
- Review documentation files
- Test in development first!

---

**You're all set!** 🎉

Your ERPNext and Tally are now connected with a robust, auditable, two-way sync system.
