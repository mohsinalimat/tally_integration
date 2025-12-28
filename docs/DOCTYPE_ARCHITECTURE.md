# Tally Integration - DocType Architecture Guide

## Overview

This guide explains the **DocType-based architecture** for Tally integration. This approach provides:

1. **1:1 Mapping**: Each Tally entity has a corresponding ERPNext DocType
2. **Two-Way Sync**: Data flows both ways with full audit trail
3. **Server Scripts**: Use Server Scripts for custom sync logic
4. **Audit Trail**: Every sync operation is logged
5. **Flexibility**: Easily extend and customize sync behavior

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Tally Software                       │
│     (Ledgers, Stock Items, Vouchers, Companies, etc.)       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ XML API (Port 9000)
                   │
         ┌─────────▼─────────────────────────────┐
         │   tally-integration (PyPI Package)     │
         │         TallyClient Wrapper            │
         └─────────┬─────────────────────────────┘
                   │
                   │
         ┌─────────▼─────────────────────────────┐
         │        Tally DocTypes (ERPNext)        │
         │  ┌──────────────────────────────────┐ │
         │  │   Tally Ledger                    │ │
         │  │   Tally Stock Item                │ │
         │  │   Tally Voucher                   │ │
         │  │   Tally Sync Log                  │ │
         │  └──────────────────────────────────┘ │
         └─────────┬─────────────────────────────┘
                   │
                   │ Server Scripts / Hooks
                   │
         ┌─────────▼─────────────────────────────┐
         │      Standard ERPNext DocTypes         │
         │  ┌──────────────────────────────────┐ │
         │  │   Customer                        │ │
         │  │   Supplier                        │ │
         │  │   Item                            │ │
         │  │   Sales Invoice                   │ │
         │  │   Purchase Invoice                │ │
         │  │   Payment Entry                   │ │
         │  └──────────────────────────────────┘ │
         └───────────────────────────────────────┘
```

---

## Core DocTypes

### 1. Tally Sync Log

**Purpose**: Audit trail for all sync operations

**Key Fields**:
- Sync Type (Master Data/Transaction/Report)
- Operation (Create/Update/Delete/Read)
- Status (Pending/In Progress/Success/Failed)
- Direction (Tally to ERP/ERP to Tally/Bidirectional)
- Entity Type (Ledger/Stock Item/Voucher)
- Tally Data (JSON)
- ERP Data (JSON)
- Error Message & Traceback

**Use Cases**:
- Track all sync operations
- Debug sync failures
- Generate sync reports
- Compliance and audit

**Example**:
```python
from tally_erpnext.tally.doctype_sync import create_sync_log

create_sync_log(
    sync_type="Master Data",
    operation="Create",
    status="Success",
    direction="Tally to ERP",
    entity_type="Ledger",
    entity_name="ABC Customer",
    reference_doctype="Tally Ledger",
    reference_name="ABC Customer",
    tally_data={"name": "ABC Customer", "parent": "Sundry Debtors"}
)
```

---

### 2. Tally Ledger

**Purpose**: 1:1 representation of Tally Ledgers in ERPNext

**Key Fields**:
- Ledger Name (unique)
- Parent Group (Sundry Debtors, Sundry Creditors, etc.)
- GUID (Tally's unique identifier)
- Balance Details (Opening, Current)
- Contact Details (Address, Mobile, Email, GSTIN, PAN)
- ERP Linking (linked_doctype, linked_docname)
- Sync Settings (auto_sync, sync_direction)

**Sync Direction Options**:
- **Tally to ERP**: Only pull from Tally
- **ERP to Tally**: Only push to Tally
- **Bidirectional**: Two-way sync
- **No Sync**: Manual only

**Use Cases**:
- Store Tally ledger data in ERPNext
- Link to Customer/Supplier/Account
- Manage two-way sync with auto_sync flag

**Example**:
```python
# Create Tally Ledger
ledger = frappe.get_doc({
    "doctype": "Tally Ledger",
    "ledger_name": "XYZ Corporation",
    "parent_group": "Sundry Debtors",
    "address": "123 Business St",
    "mobile": "9876543210",
    "email": "contact@xyz.com",
    "linked_doctype": "Customer",
    "linked_docname": "XYZ Corporation",
    "auto_sync": 1,
    "sync_direction": "Bidirectional"
})
ledger.insert()
```

---

### 3. Tally Stock Item

**Purpose**: 1:1 representation of Tally Stock Items in ERPNext

**Key Fields**:
- Item Name (unique)
- Parent Group/Category
- Base Units
- GST Details (HSN Code, GST Rate)
- Stock Details (Opening Balance, Current Balance, Rates)
- ERP Linking (linked to Item)
- Sync Settings

**Use Cases**:
- Store Tally item data
- Link to ERPNext Item
- Sync stock information

**Example**:
```python
# Create Tally Stock Item
item = frappe.get_doc({
    "doctype": "Tally Stock Item",
    "item_name": "Product ABC",
    "category": "Finished Goods",
    "base_units": "Nos",
    "hsn_code": "1234",
    "linked_doctype": "Item",
    "linked_docname": "ITEM-001",
    "auto_sync": 1
})
item.insert()
```

---

### 4. Tally Voucher

**Purpose**: 1:1 representation of Tally Vouchers in ERPNext

**Key Fields**:
- Voucher Type (Sales/Purchase/Receipt/Payment/Journal)
- Voucher Number
- Date
- Ledger Entries (child table)
- Totals (Debit/Credit)
- ERP Linking (linked to Sales Invoice, etc.)
- Sync Settings

**Child Table**: Tally Voucher Ledger Entry
- Ledger Name
- Is Debit (checkbox)
- Amount
- Cost Center
- Remarks

**Use Cases**:
- Store Tally vouchers
- Link to Sales/Purchase Invoice
- Create vouchers in Tally from ERP

**Example**:
```python
# Create Tally Voucher
voucher = frappe.get_doc({
    "doctype": "Tally Voucher",
    "voucher_type": "Sales",
    "date": "2025-12-10",
    "party_ledger_name": "ABC Customer",
    "narration": "Sale of goods",
    "linked_doctype": "Sales Invoice",
    "linked_docname": "SINV-001",
    "ledger_entries": [
        {
            "ledger_name": "ABC Customer",
            "is_debit": 1,
            "amount": 11800
        },
        {
            "ledger_name": "Sales",
            "is_debit": 0,
            "amount": 10000
        },
        {
            "ledger_name": "CGST",
            "is_debit": 0,
            "amount": 900
        },
        {
            "ledger_name": "SGST",
            "is_debit": 0,
            "amount": 900
        }
    ]
})
voucher.insert()
voucher.submit()
```

---

## Synchronization Functions

### From `doctype_sync.py`

#### 1. Sync from Tally to ERP

```python
from tally_erpnext.tally.doctype_sync import (
    sync_ledgers_from_tally,
    sync_stock_items_from_tally,
    sync_vouchers_from_tally
)

# Sync all ledgers from Tally
result = sync_ledgers_from_tally()
# Returns: {"created": 10, "updated": 5, "failed": 0, "total": 15}

# Sync specific parent group
result = sync_ledgers_from_tally(parent_group="Sundry Debtors")

# Sync stock items
result = sync_stock_items_from_tally()

# Sync vouchers with filters
result = sync_vouchers_from_tally(
    voucher_type="Sales",
    from_date="2025-12-01",
    to_date="2025-12-31"
)
```

#### 2. Sync from ERP to Tally

```python
from tally_erpnext.tally.doctype_sync import (
    sync_ledger_to_tally,
    sync_stock_item_to_tally,
    sync_voucher_to_tally
)

# Push ledger to Tally
result = sync_ledger_to_tally("ABC Customer", operation="create")
# Returns: {"success": True, "response": {...}}

# Push stock item to Tally
result = sync_stock_item_to_tally("Product ABC", operation="create")

# Push voucher to Tally
result = sync_voucher_to_tally("TVCH-0001", operation="create")
```

---

## Two-Way Sync with Server Scripts

### Workflow

1. **User creates Customer in ERPNext**
2. **Server Script** (After Insert) → Creates Tally Ledger
3. **Tally Ledger** (auto_sync=True) → Pushes to Tally via `sync_ledger_to_tally()`
4. **Sync Log** created with status

### Reverse Flow

1. **New ledger created in Tally**
2. **Scheduled Job** runs `sync_ledgers_from_tally()`
3. **Tally Ledger** created in ERPNext
4. **Server Script** (After Insert) → Creates Customer
5. **Sync Log** created

---

## Server Script Examples

See [server_scripts_examples.md](./examples/server_scripts_examples.md) for complete examples:

1. Customer → Tally Ledger
2. Supplier → Tally Ledger
3. Item → Tally Stock Item
4. Sales Invoice → Tally Voucher
5. Purchase Invoice → Tally Voucher
6. Payment Entry → Tally Voucher
7. Reverse sync from Tally

---

## API Endpoints

All sync functions are exposed as API endpoints:

```javascript
// Sync all ledgers from Tally
frappe.call({
    method: "tally_erpnext.tally.doctype_sync.sync_all_ledgers",
    args: {
        company: "My Company",
        parent_group: "Sundry Debtors"
    },
    callback: function(r) {
        console.log(r.message);
    }
});

// Sync all stock items
frappe.call({
    method: "tally_erpnext.tally.doctype_sync.sync_all_stock_items",
    callback: function(r) {
        console.log(r.message);
    }
});

// Sync vouchers
frappe.call({
    method: "tally_erpnext.tally.doctype_sync.sync_all_vouchers",
    args: {
        voucher_type: "Sales",
        from_date: "2025-12-01",
        to_date: "2025-12-31"
    },
    callback: function(r) {
        console.log(r.message);
    }
});
```

---

## Scheduled Tasks

Add to `hooks.py` for automatic sync:

```python
scheduler_events = {
    "daily": [
        "tally_erpnext.tally.scheduled_tasks.daily_sync_from_tally"
    ],
    "hourly": [
        "tally_erpnext.tally.scheduled_tasks.hourly_sync_from_tally"
    ]
}
```

---

## Data Flow Examples

### Example 1: Customer Creation Flow

1. User creates **Customer** "ABC Corp" in ERPNext
2. **Server Script** (After Insert) triggers
3. Creates **Tally Ledger** "ABC Corp" with:
   - parent_group = "Sundry Debtors"
   - linked_doctype = "Customer"
   - auto_sync = 1
4. **Tally Ledger** (after_insert) triggers
5. Enqueues `sync_ledger_to_tally("ABC Corp")`
6. TallyClient creates ledger in Tally
7. **Tally Sync Log** created with:
   - status = "Success"
   - direction = "ERP to Tally"
   - entity_type = "Ledger"

### Example 2: Sales Invoice Flow

1. User submits **Sales Invoice** SINV-001
2. **Server Script** (On Submit) triggers
3. Creates **Tally Voucher** with:
   - voucher_type = "Sales"
   - linked_doctype = "Sales Invoice"
   - ledger_entries from invoice
4. User submits **Tally Voucher**
5. **Tally Voucher** (on_submit) triggers
6. Enqueues `sync_voucher_to_tally("TVCH-0001")`
7. TallyClient creates voucher in Tally
8. **Tally Sync Log** created

### Example 3: Scheduled Sync from Tally

1. **Cron job** runs daily at midnight
2. Calls `sync_ledgers_from_tally()`
3. TallyClient fetches all ledgers
4. For each ledger:
   - Check if **Tally Ledger** exists
   - Create or update
   - **Sync Log** created
5. **Server Script** on Tally Ledger (After Insert)
6. Creates/updates **Customer** if parent_group = "Sundry Debtors"

---

## Benefits of DocType Architecture

1. **Audit Trail**: Every sync operation logged
2. **Data Integrity**: Validation at DocType level
3. **Flexibility**: Use Server Scripts for custom logic
4. **Transparency**: Users can see Tally data in ERPNext
5. **Conflict Resolution**: Handle conflicts via status field
6. **Reporting**: Query Tally data using ERPNext reports
7. **Permissions**: Standard ERPNext permission system
8. **Workflow**: Can add approval workflow if needed
9. **History**: Track changes with version control
10. **Testing**: Easy to test with test records

---

## Best Practices

1. **Always use Sync Log**: Track all operations
2. **Handle errors gracefully**: Log errors, don't break
3. **Use background jobs**: For heavy operations
4. **Test in dev first**: Never test in production
5. **Monitor sync status**: Check failed syncs regularly
6. **Keep Tally data**: Store raw JSON in additional_data
7. **Link properly**: Always link to ERP doctypes
8. **Use auto_sync wisely**: Enable only when needed
9. **Conflict resolution**: Define clear rules
10. **Documentation**: Document custom sync logic

---

## Troubleshooting

### Issue: Tally Ledger not syncing to Tally

**Check**:
1. auto_sync = 1?
2. sync_direction = "ERP to Tally" or "Bidirectional"?
3. Tally connection working?
4. Check Error Log for failures
5. Check Tally Sync Log for details

### Issue: Duplicate records

**Solution**:
- Use GUID field to identify unique records
- Check before creating new records
- Use `frappe.db.exists()` before insert

### Issue: Data mismatch

**Solution**:
- Compare data in additional_data field
- Check field mappings in sync functions
- Review Server Scripts for custom logic

---

## Extending the Architecture

### Add Custom Fields

```python
# Add custom field to Tally Ledger
frappe.get_doc({
    "doctype": "Custom Field",
    "dt": "Tally Ledger",
    "fieldname": "custom_tax_id",
    "label": "Tax ID",
    "fieldtype": "Data"
}).insert()
```

### Add Custom Sync Logic

```python
# Override sync function
def custom_sync_ledger_to_tally(ledger_name):
    # Custom logic here
    result = sync_ledger_to_tally(ledger_name)
    # Additional processing
    return result
```

### Add Custom DocTypes

Create your own doctypes like:
- Tally Company
- Tally Group
- Tally Unit
- Tally Godown
- Tally Cost Center

---

## Migration from Old Architecture

If you were using the direct sync functions (without DocTypes):

1. Run `sync_ledgers_from_tally()` to create Tally Ledger records
2. Run `sync_stock_items_from_tally()` to create Tally Stock Item records
3. Add Server Scripts for ongoing sync
4. Update custom code to use new functions

---

## Conclusion

The DocType-based architecture provides:
- ✅ Full audit trail
- ✅ Two-way synchronization
- ✅ Flexible Server Scripts
- ✅ Standard ERPNext features
- ✅ Easy customization
- ✅ Better data integrity

For detailed code examples, see:
- [server_scripts_examples.md](./examples/server_scripts_examples.md)
- [TALLY_INTEGRATION_GUIDE.md](./TALLY_INTEGRATION_GUIDE.md)
- [doctype_sync.py](./tally_erpnext/tally/doctype_sync.py)
