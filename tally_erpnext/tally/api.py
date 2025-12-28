"""
Tally API Endpoints

This module provides whitelisted API endpoints for Tally integration operations
that can be called from the frontend or external systems.
"""

import frappe
from frappe import _
from tally_erpnext.tally.client import TallyClient


@frappe.whitelist()
def get_companies():
	"""
	Get list of all companies from Tally

	Returns:
		list: List of company dictionaries
	"""
	try:
		client = TallyClient()
		companies = client.get_companies()
		return {"success": True, "data": companies}
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Tally API Error - Get Companies"))
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_current_company():
	"""
	Get current company information from Tally

	Returns:
		dict: Company information
	"""
	try:
		client = TallyClient()
		company = client.get_current_company()
		return {"success": True, "data": company}
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Tally API Error - Get Current Company"))
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_ledgers(company=None):
	"""
	Get all ledgers from Tally

	Args:
		company: Company name (optional)

	Returns:
		dict: Response with ledgers list
	"""
	try:
		client = TallyClient()
		ledgers = client.get_ledgers(company=company)
		return {"success": True, "data": ledgers}
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Tally API Error - Get Ledgers"))
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def create_ledger(name, parent, address=None, mobile=None, email=None):
	"""
	Create a new ledger in Tally

	Args:
		name: Ledger name
		parent: Parent ledger group
		address: Address (optional)
		mobile: Mobile number (optional)
		email: Email (optional)

	Returns:
		dict: Response with creation status
	"""
	try:
		client = TallyClient()
		response = client.create_ledger(
			name=name,
			parent=parent,
			address=address,
			mobile=mobile,
			email=email
		)
		return {"success": True, "data": response}
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Tally API Error - Create Ledger"))
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_stock_items(company=None):
	"""
	Get all stock items from Tally

	Args:
		company: Company name (optional)

	Returns:
		dict: Response with stock items list
	"""
	try:
		client = TallyClient()
		items = client.get_stock_items(company=company)
		return {"success": True, "data": items}
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Tally API Error - Get Stock Items"))
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def create_stock_item(name, category, unit):
	"""
	Create a new stock item in Tally

	Args:
		name: Item name
		category: Item category
		unit: Unit of measurement

	Returns:
		dict: Response with creation status
	"""
	try:
		client = TallyClient()
		response = client.create_stock_item(name=name, category=category, unit=unit)
		return {"success": True, "data": response}
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Tally API Error - Create Stock Item"))
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_vouchers(voucher_type=None, from_date=None, to_date=None):
	"""
	Get vouchers from Tally

	Args:
		voucher_type: Type of voucher (Sales, Purchase, etc.)
		from_date: Start date (optional)
		to_date: End date (optional)

	Returns:
		dict: Response with vouchers list
	"""
	try:
		client = TallyClient()
		vouchers = client.get_vouchers(
			voucher_type=voucher_type,
			from_date=from_date,
			to_date=to_date
		)
		return {"success": True, "data": vouchers}
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Tally API Error - Get Vouchers"))
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def create_voucher(voucher_type, date, ledger_entries, narration=None):
	"""
	Create a voucher in Tally

	Args:
		voucher_type: Type of voucher (Sales, Purchase, Receipt, Payment, Journal)
		date: Voucher date
		ledger_entries: JSON string or list of ledger entry dictionaries
		narration: Voucher narration (optional)

	Returns:
		dict: Response with creation status
	"""
	try:
		import json

		# Parse ledger_entries if it's a JSON string
		if isinstance(ledger_entries, str):
			ledger_entries = json.loads(ledger_entries)

		client = TallyClient()
		response = client.create_voucher(
			voucher_type=voucher_type,
			date=date,
			ledger_entries=ledger_entries,
			narration=narration
		)
		return {"success": True, "data": response}
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Tally API Error - Create Voucher"))
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_groups(group_type="Ledger"):
	"""
	Get groups from Tally

	Args:
		group_type: Type of group (Ledger, Stock, etc.)

	Returns:
		dict: Response with groups list
	"""
	try:
		client = TallyClient()
		groups = client.get_groups(group_type=group_type)
		return {"success": True, "data": groups}
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Tally API Error - Get Groups"))
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def sync_customers_from_tally():
	"""
	Sync customers from Tally to ERPNext

	Returns:
		dict: Response with sync status
	"""
	try:
		from tally_erpnext.tally.utils import sync_customers
		result = sync_customers()
		return {"success": True, "data": result}
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Tally API Error - Sync Customers"))
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def sync_items_from_tally():
	"""
	Sync items from Tally to ERPNext

	Returns:
		dict: Response with sync status
	"""
	try:
		from tally_erpnext.tally.utils import sync_items
		result = sync_items()
		return {"success": True, "data": result}
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Tally API Error - Sync Items"))
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def push_sales_invoice_to_tally(sales_invoice_name):
	"""
	Push a Sales Invoice from ERPNext to Tally

	Args:
		sales_invoice_name: Name of the Sales Invoice document

	Returns:
		dict: Response with push status
	"""
	try:
		from tally_erpnext.tally.utils import push_sales_invoice
		result = push_sales_invoice(sales_invoice_name)
		return {"success": True, "data": result}
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Tally API Error - Push Sales Invoice"))
		return {"success": False, "message": str(e)}
