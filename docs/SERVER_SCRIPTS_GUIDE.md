# Server Scripts Examples for Tally Integration

This document provides ready-to-use Server Scripts for two-way synchronization between ERPNext and Tally using the Tally DocTypes.

## How to Add Server Scripts

1. Go to **Server Script** list in ERPNext
2. Click **New**
3. Copy and paste the script code
4. Set the appropriate DocType and Event Type
5. Enable the script
6. Save

---

## 1. Customer to Tally Ledger Sync

### Auto-create Tally Ledger when Customer is created

**DocType:** Customer
**Event Type:** After Insert

```python
import frappe
from frappe import _

def execute(doc, method=None):
    """
    Create Tally Ledger when Customer is created
    """
    # Check if Tally integration is enabled
    settings = frappe.get_doc("Tally Settings", "Tally Settings")
    if not settings.enabled:
        return

    # Check if Tally Ledger already exists
    if frappe.db.exists("Tally Ledger", doc.customer_name):
        return

    # Create Tally Ledger
    try:
        tally_ledger = frappe.get_doc({
            "doctype": "Tally Ledger",
            "ledger_name": doc.customer_name,
            "parent_group": "Sundry Debtors",
            "mailing_name": doc.customer_name,
            "address": doc.primary_address or "",
            "mobile": doc.mobile_no or "",
            "email": doc.email_id or "",
            "gstin": doc.gstin or "",
            "pan": doc.pan or "",
            "linked_doctype": "Customer",
            "linked_docname": doc.name,
            "auto_sync": 1,
            "sync_direction": "ERP to Tally"
        })
        tally_ledger.insert(ignore_permissions=True)
        frappe.msgprint(_("Tally Ledger {0} created for Customer {1}").format(
            tally_ledger.name, doc.customer_name
        ), alert=True, indicator="green")
    except Exception as e:
        frappe.log_error(message=str(e), title=_("Tally Ledger Creation Failed"))
```

---

### Update Tally Ledger when Customer is updated

**DocType:** Customer
**Event Type:** On Update

```python
import frappe
from frappe import _

def execute(doc, method=None):
    """
    Update Tally Ledger when Customer is updated
    """
    # Check if Tally Ledger exists
    if not frappe.db.exists("Tally Ledger", doc.customer_name):
        return

    try:
        tally_ledger = frappe.get_doc("Tally Ledger", doc.customer_name)

        # Update fields
        tally_ledger.mailing_name = doc.customer_name
        tally_ledger.address = doc.primary_address or tally_ledger.address
        tally_ledger.mobile = doc.mobile_no or tally_ledger.mobile
        tally_ledger.email = doc.email_id or tally_ledger.email
        tally_ledger.gstin = doc.gstin or tally_ledger.gstin
        tally_ledger.pan = doc.pan or tally_ledger.pan

        tally_ledger.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(message=str(e), title=_("Tally Ledger Update Failed"))
```

---

## 2. Supplier to Tally Ledger Sync

### Auto-create Tally Ledger when Supplier is created

**DocType:** Supplier
**Event Type:** After Insert

```python
import frappe
from frappe import _

def execute(doc, method=None):
    """
    Create Tally Ledger when Supplier is created
    """
    settings = frappe.get_doc("Tally Settings", "Tally Settings")
    if not settings.enabled:
        return

    if frappe.db.exists("Tally Ledger", doc.supplier_name):
        return

    try:
        tally_ledger = frappe.get_doc({
            "doctype": "Tally Ledger",
            "ledger_name": doc.supplier_name,
            "parent_group": "Sundry Creditors",
            "mailing_name": doc.supplier_name,
            "address": doc.primary_address or "",
            "mobile": doc.mobile_no or "",
            "email": doc.email_id or "",
            "gstin": doc.gstin or "",
            "pan": doc.pan or "",
            "linked_doctype": "Supplier",
            "linked_docname": doc.name,
            "auto_sync": 1,
            "sync_direction": "ERP to Tally"
        })
        tally_ledger.insert(ignore_permissions=True)
        frappe.msgprint(_("Tally Ledger {0} created for Supplier {1}").format(
            tally_ledger.name, doc.supplier_name
        ), alert=True, indicator="green")
    except Exception as e:
        frappe.log_error(message=str(e), title=_("Tally Ledger Creation Failed"))
```

---

## 3. Item to Tally Stock Item Sync

### Auto-create Tally Stock Item when Item is created

**DocType:** Item
**Event Type:** After Insert

```python
import frappe
from frappe import _

def execute(doc, method=None):
    """
    Create Tally Stock Item when Item is created
    """
    settings = frappe.get_doc("Tally Settings", "Tally Settings")
    if not settings.enabled:
        return

    # Only sync stock items
    if not doc.is_stock_item:
        return

    if frappe.db.exists("Tally Stock Item", doc.item_name):
        return

    try:
        tally_item = frappe.get_doc({
            "doctype": "Tally Stock Item",
            "item_name": doc.item_name,
            "parent_group": doc.item_group,
            "category": doc.item_group,
            "base_units": doc.stock_uom,
            "hsn_code": doc.gst_hsn_code or "",
            "linked_doctype": "Item",
            "linked_docname": doc.name,
            "auto_sync": 1,
            "sync_direction": "ERP to Tally"
        })
        tally_item.insert(ignore_permissions=True)
        frappe.msgprint(_("Tally Stock Item {0} created for Item {1}").format(
            tally_item.name, doc.item_name
        ), alert=True, indicator="green")
    except Exception as e:
        frappe.log_error(message=str(e), title=_("Tally Stock Item Creation Failed"))
```

---

## 4. Sales Invoice to Tally Voucher Sync

### Create Tally Voucher when Sales Invoice is submitted

**DocType:** Sales Invoice
**Event Type:** On Submit

```python
import frappe
from frappe import _

def execute(doc, method=None):
    """
    Create Tally Voucher when Sales Invoice is submitted
    """
    settings = frappe.get_doc("Tally Settings", "Tally Settings")
    if not settings.enabled or not settings.auto_sync_sales_invoices:
        return

    try:
        # Create Tally Voucher
        tally_voucher = frappe.get_doc({
            "doctype": "Tally Voucher",
            "voucher_type": "Sales",
            "date": doc.posting_date,
            "party_ledger_name": doc.customer_name,
            "narration": f"Sales Invoice {doc.name} - {doc.customer_name}",
            "reference_number": doc.name,
            "reference_date": doc.posting_date,
            "linked_doctype": "Sales Invoice",
            "linked_docname": doc.name,
            "auto_sync": 1,
            "sync_direction": "ERP to Tally"
        })

        # Add ledger entries
        # Customer ledger (Debit)
        tally_voucher.append("ledger_entries", {
            "ledger_name": doc.customer_name,
            "is_debit": 1,
            "amount": doc.grand_total
        })

        # Sales ledger (Credit)
        tally_voucher.append("ledger_entries", {
            "ledger_name": "Sales",
            "is_debit": 0,
            "amount": doc.total
        })

        # Tax ledgers (Credit)
        for tax in doc.taxes:
            if tax.tax_amount > 0:
                tally_voucher.append("ledger_entries", {
                    "ledger_name": tax.account_head,
                    "is_debit": 0,
                    "amount": tax.tax_amount
                })

        tally_voucher.insert(ignore_permissions=True)
        tally_voucher.submit()

        # Link back to Sales Invoice
        doc.db_set("tally_voucher_number", tally_voucher.name, update_modified=False)

        frappe.msgprint(_("Tally Voucher {0} created for Sales Invoice {1}").format(
            tally_voucher.name, doc.name
        ), alert=True, indicator="green")

    except Exception as e:
        frappe.log_error(message=str(e), title=_("Tally Voucher Creation Failed"))
```

---

## 5. Purchase Invoice to Tally Voucher Sync

### Create Tally Voucher when Purchase Invoice is submitted

**DocType:** Purchase Invoice
**Event Type:** On Submit

```python
import frappe
from frappe import _

def execute(doc, method=None):
    """
    Create Tally Voucher when Purchase Invoice is submitted
    """
    settings = frappe.get_doc("Tally Settings", "Tally Settings")
    if not settings.enabled or not settings.auto_sync_purchase_invoices:
        return

    try:
        tally_voucher = frappe.get_doc({
            "doctype": "Tally Voucher",
            "voucher_type": "Purchase",
            "date": doc.posting_date,
            "party_ledger_name": doc.supplier_name,
            "narration": f"Purchase Invoice {doc.name} - {doc.supplier_name}",
            "reference_number": doc.name,
            "reference_date": doc.posting_date,
            "linked_doctype": "Purchase Invoice",
            "linked_docname": doc.name,
            "auto_sync": 1,
            "sync_direction": "ERP to Tally"
        })

        # Add ledger entries
        # Purchase ledger (Debit)
        tally_voucher.append("ledger_entries", {
            "ledger_name": "Purchases",
            "is_debit": 1,
            "amount": doc.total
        })

        # Tax ledgers (Debit)
        for tax in doc.taxes:
            if tax.tax_amount > 0:
                tally_voucher.append("ledger_entries", {
                    "ledger_name": tax.account_head,
                    "is_debit": 1,
                    "amount": tax.tax_amount
                })

        # Supplier ledger (Credit)
        tally_voucher.append("ledger_entries", {
            "ledger_name": doc.supplier_name,
            "is_debit": 0,
            "amount": doc.grand_total
        })

        tally_voucher.insert(ignore_permissions=True)
        tally_voucher.submit()

        doc.db_set("tally_voucher_number", tally_voucher.name, update_modified=False)

        frappe.msgprint(_("Tally Voucher {0} created for Purchase Invoice {1}").format(
            tally_voucher.name, doc.name
        ), alert=True, indicator="green")

    except Exception as e:
        frappe.log_error(message=str(e), title=_("Tally Voucher Creation Failed"))
```

---

## 6. Payment Entry to Tally Voucher Sync

### Create Tally Voucher when Payment Entry is submitted

**DocType:** Payment Entry
**Event Type:** On Submit

```python
import frappe
from frappe import _

def execute(doc, method=None):
    """
    Create Tally Voucher when Payment Entry is submitted
    """
    settings = frappe.get_doc("Tally Settings", "Tally Settings")
    if not settings.enabled:
        return

    try:
        # Determine voucher type based on payment type
        voucher_type = "Receipt" if doc.payment_type == "Receive" else "Payment"

        # Determine party ledger name
        party_ledger = doc.party_name if doc.party else "Cash"

        tally_voucher = frappe.get_doc({
            "doctype": "Tally Voucher",
            "voucher_type": voucher_type,
            "date": doc.posting_date,
            "party_ledger_name": party_ledger,
            "narration": doc.remarks or f"{voucher_type} - {party_ledger}",
            "reference_number": doc.name,
            "reference_date": doc.posting_date,
            "linked_doctype": "Payment Entry",
            "linked_docname": doc.name,
            "auto_sync": 1,
            "sync_direction": "ERP to Tally"
        })

        if doc.payment_type == "Receive":
            # Receipt: Debit bank/cash, Credit party
            tally_voucher.append("ledger_entries", {
                "ledger_name": doc.paid_to or "Cash",
                "is_debit": 1,
                "amount": doc.paid_amount
            })
            tally_voucher.append("ledger_entries", {
                "ledger_name": party_ledger,
                "is_debit": 0,
                "amount": doc.paid_amount
            })
        else:
            # Payment: Debit party, Credit bank/cash
            tally_voucher.append("ledger_entries", {
                "ledger_name": party_ledger,
                "is_debit": 1,
                "amount": doc.paid_amount
            })
            tally_voucher.append("ledger_entries", {
                "ledger_name": doc.paid_from or "Cash",
                "is_debit": 0,
                "amount": doc.paid_amount
            })

        tally_voucher.insert(ignore_permissions=True)
        tally_voucher.submit()

        doc.db_set("tally_voucher_number", tally_voucher.name, update_modified=False)

        frappe.msgprint(_("Tally Voucher {0} created for Payment Entry {1}").format(
            tally_voucher.name, doc.name
        ), alert=True, indicator="green")

    except Exception as e:
        frappe.log_error(message=str(e), title=_("Tally Voucher Creation Failed"))
```

---

## 7. Reverse Sync - Update Customer from Tally Ledger

### Update Customer when Tally Ledger is synced from Tally

**DocType:** Tally Ledger
**Event Type:** After Insert

```python
import frappe
from frappe import _

def execute(doc, method=None):
    """
    Create or update Customer when Tally Ledger is synced from Tally
    """
    # Only process if it's a Sundry Debtor (customer)
    if doc.parent_group != "Sundry Debtors":
        return

    # Skip if already linked
    if doc.linked_doctype == "Customer" and doc.linked_docname:
        return

    try:
        # Check if customer exists
        if frappe.db.exists("Customer", {"customer_name": doc.ledger_name}):
            customer = frappe.get_doc("Customer", {"customer_name": doc.ledger_name})
        else:
            # Create new customer
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": doc.ledger_name,
                "customer_type": "Company",
                "customer_group": "Commercial",
                "territory": "All Territories"
            })

        # Update fields
        if doc.mobile:
            customer.mobile_no = doc.mobile
        if doc.email:
            customer.email_id = doc.email
        if doc.gstin:
            customer.gstin = doc.gstin
        if doc.pan:
            customer.pan = doc.pan

        if customer.is_new():
            customer.insert(ignore_permissions=True)
        else:
            customer.save(ignore_permissions=True)

        # Link back to Tally Ledger
        doc.db_set("linked_doctype", "Customer", update_modified=False)
        doc.db_set("linked_docname", customer.name, update_modified=False)

    except Exception as e:
        frappe.log_error(message=str(e), title=_("Customer Sync from Tally Failed"))
```

---

## 8. Scheduled Sync Jobs

### Daily sync from Tally (to be added in hooks.py)

Add this to your `hooks.py`:

```python
scheduler_events = {
    "daily": [
        "tally_integration.tally.scheduled_tasks.daily_sync_from_tally"
    ],
    "hourly": [
        "tally_integration.tally.scheduled_tasks.hourly_sync_from_tally"
    ]
}
```

Then create `tally_integration/tally/scheduled_tasks.py`:

```python
import frappe
from tally_integration.tally.doctype_sync import (
    sync_ledgers_from_tally,
    sync_stock_items_from_tally,
    sync_vouchers_from_tally
)

def daily_sync_from_tally():
    """Daily sync all master data from Tally"""
    settings = frappe.get_doc("Tally Settings", "Tally Settings")
    if not settings.enabled:
        return

    # Sync ledgers
    if settings.auto_sync_customers or settings.auto_sync_suppliers:
        sync_ledgers_from_tally()

    # Sync stock items
    if settings.auto_sync_items:
        sync_stock_items_from_tally()

def hourly_sync_from_tally():
    """Hourly sync transactions from Tally"""
    settings = frappe.get_doc("Tally Settings", "Tally Settings")
    if not settings.enabled:
        return

    # Sync today's vouchers
    from frappe.utils import today
    sync_vouchers_from_tally(from_date=today(), to_date=today())
```

---

## Testing Server Scripts

1. Create a test Customer/Supplier/Item
2. Check if Tally Ledger/Stock Item is created
3. Submit a Sales/Purchase Invoice
4. Check if Tally Voucher is created
5. View Tally Sync Log for audit trail

---

## Customization Tips

1. **Conditional Sync**: Add checks based on custom fields
2. **Field Mapping**: Customize field mapping as per your needs
3. **Error Handling**: Add specific error handling for your use cases
4. **Filters**: Add filters to sync only specific records
5. **Batch Processing**: For bulk operations, use queue

---

## Important Notes

- Server Scripts run synchronously by default
- For heavy operations, use `frappe.enqueue()` for background processing
- Always test in a development environment first
- Monitor Tally Sync Log for any sync errors
- Use `ignore_permissions=True` carefully, only in server scripts
