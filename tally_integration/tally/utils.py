"""
Tally Integration Utilities

This module provides utility functions for data mapping and synchronization
between ERPNext and Tally.
"""

import frappe
from frappe import _
from tally_integration.tally.client import TallyClient


def get_tally_client():
	"""
	Get a configured TallyClient instance

	Returns:
		TallyClient: Configured Tally client
	"""
	return TallyClient()


def sync_customers():
	"""
	Sync customers from Tally to ERPNext

	This function fetches ledgers from Tally under "Sundry Debtors" group
	and creates/updates corresponding Customer records in ERPNext.

	Returns:
		dict: Sync results with counts
	"""
	client = get_tally_client()
	ledgers = client.get_ledgers()

	created = 0
	updated = 0
	skipped = 0

	# Filter ledgers that are customers (Sundry Debtors)
	customer_ledgers = [
		ledger for ledger in ledgers
		if ledger.get("parent") == "Sundry Debtors"
	]

	for ledger in customer_ledgers:
		try:
			customer_name = ledger.get("name")
			if not customer_name:
				skipped += 1
				continue

			# Check if customer already exists
			if frappe.db.exists("Customer", {"customer_name": customer_name}):
				# Update existing customer
				customer = frappe.get_doc("Customer", {"customer_name": customer_name})
				customer.tally_ledger_name = customer_name
				if ledger.get("mobile"):
					customer.mobile_no = ledger.get("mobile")
				if ledger.get("email"):
					customer.email_id = ledger.get("email")
				customer.save(ignore_permissions=True)
				updated += 1
			else:
				# Create new customer
				customer = frappe.get_doc({
					"doctype": "Customer",
					"customer_name": customer_name,
					"customer_type": "Company",
					"customer_group": "Commercial",
					"territory": "All Territories",
					"tally_ledger_name": customer_name,
					"mobile_no": ledger.get("mobile"),
					"email_id": ledger.get("email")
				})
				customer.insert(ignore_permissions=True)
				created += 1

			frappe.db.commit()

		except Exception as e:
			frappe.log_error(
				message=f"Error syncing customer {ledger.get('name')}: {str(e)}",
				title=_("Customer Sync Error")
			)
			skipped += 1
			continue

	return {
		"created": created,
		"updated": updated,
		"skipped": skipped,
		"total": len(customer_ledgers)
	}


def sync_items():
	"""
	Sync stock items from Tally to ERPNext

	This function fetches stock items from Tally and creates/updates
	corresponding Item records in ERPNext.

	Returns:
		dict: Sync results with counts
	"""
	client = get_tally_client()
	stock_items = client.get_stock_items()

	created = 0
	updated = 0
	skipped = 0

	for tally_item in stock_items:
		try:
			item_name = tally_item.get("name")
			if not item_name:
				skipped += 1
				continue

			# Check if item already exists
			if frappe.db.exists("Item", {"item_name": item_name}):
				# Update existing item
				item = frappe.get_doc("Item", {"item_name": item_name})
				item.tally_item_name = item_name
				if tally_item.get("unit"):
					item.stock_uom = tally_item.get("unit")
				item.save(ignore_permissions=True)
				updated += 1
			else:
				# Create new item
				item = frappe.get_doc({
					"doctype": "Item",
					"item_code": item_name,
					"item_name": item_name,
					"item_group": tally_item.get("category", "Products"),
					"stock_uom": tally_item.get("unit", "Nos"),
					"tally_item_name": item_name,
					"is_stock_item": 1
				})
				item.insert(ignore_permissions=True)
				created += 1

			frappe.db.commit()

		except Exception as e:
			frappe.log_error(
				message=f"Error syncing item {tally_item.get('name')}: {str(e)}",
				title=_("Item Sync Error")
			)
			skipped += 1
			continue

	return {
		"created": created,
		"updated": updated,
		"skipped": skipped,
		"total": len(stock_items)
	}


def push_sales_invoice(sales_invoice_name):
	"""
	Push a Sales Invoice from ERPNext to Tally as a Sales Voucher

	Args:
		sales_invoice_name: Name of the Sales Invoice document

	Returns:
		dict: Push result
	"""
	client = get_tally_client()

	# Get Sales Invoice document
	si = frappe.get_doc("Sales Invoice", sales_invoice_name)

	# Prepare ledger entries for Tally
	ledger_entries = []

	# Customer ledger entry (Debit)
	ledger_entries.append({
		"ledger_name": si.customer_name,
		"amount": si.grand_total,
		"is_debit": True
	})

	# Sales ledger entry (Credit)
	ledger_entries.append({
		"ledger_name": "Sales",
		"amount": si.total,
		"is_debit": False
	})

	# Tax ledger entries (if any)
	for tax in si.taxes:
		ledger_entries.append({
			"ledger_name": tax.account_head,
			"amount": tax.tax_amount,
			"is_debit": False
		})

	# Create voucher in Tally
	response = client.create_voucher(
		voucher_type="Sales",
		date=si.posting_date,
		ledger_entries=ledger_entries,
		narration=f"Sales Invoice {si.name} - {si.customer_name}"
	)

	# Update Sales Invoice with Tally reference
	si.db_set("tally_voucher_number", response.get("voucher_number"), update_modified=False)
	frappe.db.commit()

	return {
		"sales_invoice": si.name,
		"tally_response": response
	}


def map_erpnext_customer_to_tally_ledger(customer_name):
	"""
	Map ERPNext Customer to Tally Ledger format

	Args:
		customer_name: Name of the Customer document

	Returns:
		dict: Tally ledger data
	"""
	customer = frappe.get_doc("Customer", customer_name)

	return {
		"name": customer.customer_name,
		"parent": "Sundry Debtors",
		"address": customer.primary_address or "",
		"mobile": customer.mobile_no or "",
		"email": customer.email_id or ""
	}


def map_erpnext_item_to_tally_stock_item(item_code):
	"""
	Map ERPNext Item to Tally Stock Item format

	Args:
		item_code: Item code in ERPNext

	Returns:
		dict: Tally stock item data
	"""
	item = frappe.get_doc("Item", item_code)

	return {
		"name": item.item_name,
		"category": item.item_group,
		"unit": item.stock_uom
	}


def create_customer_in_tally(customer_name):
	"""
	Create a customer in Tally from ERPNext Customer

	Args:
		customer_name: Name of the Customer document

	Returns:
		dict: Creation response
	"""
	client = get_tally_client()
	ledger_data = map_erpnext_customer_to_tally_ledger(customer_name)

	response = client.create_ledger(**ledger_data)

	# Update customer with Tally reference
	frappe.db.set_value("Customer", customer_name, "tally_ledger_name", ledger_data["name"])
	frappe.db.commit()

	return response


def create_item_in_tally(item_code):
	"""
	Create an item in Tally from ERPNext Item

	Args:
		item_code: Item code in ERPNext

	Returns:
		dict: Creation response
	"""
	client = get_tally_client()
	item_data = map_erpnext_item_to_tally_stock_item(item_code)

	response = client.create_stock_item(**item_data)

	# Update item with Tally reference
	frappe.db.set_value("Item", item_code, "tally_item_name", item_data["name"])
	frappe.db.commit()

	return response


def is_tally_enabled():
	"""
	Check if Tally integration is enabled

	Returns:
		bool: True if enabled, False otherwise
	"""
	settings = TallyClient.get_tally_settings()
	return settings.get("enabled", False)


def validate_tally_connection():
	"""
	Validate connection to Tally server

	Returns:
		tuple: (is_valid, message)
	"""
	try:
		client = get_tally_client()
		if client.test_connection():
			return True, _("Connection successful")
		else:
			return False, _("Connection failed")
	except Exception as e:
		return False, str(e)
