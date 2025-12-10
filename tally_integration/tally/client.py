"""
Tally Client Wrapper for Frappe/ERPNext Integration

This module provides a Frappe-friendly wrapper around the tally-integration package,
handling connection management, error handling, and data transformation.
"""

import frappe
from frappe import _
from tally_integration import TallyClient as BaseTallyClient, TallyConnectionError


class TallyClient:
	"""
	Wrapper class for TallyClient that integrates with Frappe's settings and error handling.
	"""

	def __init__(self, host=None, port=None):
		"""
		Initialize Tally Client with settings from Frappe

		Args:
			host: Tally server host (defaults to settings or localhost)
			port: Tally server port (defaults to settings or 9000)
		"""
		# Get settings from Tally Settings doctype if not provided
		if not host or not port:
			settings = self.get_tally_settings()
			host = host or settings.get("host", "localhost")
			port = port or settings.get("port", 9000)

		try:
			self.client = BaseTallyClient(host=host, port=port)
		except Exception as e:
			frappe.throw(_("Failed to initialize Tally Client: {0}").format(str(e)))

	@staticmethod
	def get_tally_settings():
		"""
		Get Tally integration settings from Frappe

		Returns:
			dict: Tally settings
		"""
		try:
			if frappe.db.exists("Tally Settings", "Tally Settings"):
				settings = frappe.get_doc("Tally Settings", "Tally Settings")
				return {
					"host": settings.host or "localhost",
					"port": settings.port or 9000,
					"enabled": settings.enabled,
				}
		except Exception:
			pass

		return {"host": "localhost", "port": 9000, "enabled": False}

	def test_connection(self):
		"""
		Test connection to Tally server

		Returns:
			bool: True if connection successful, False otherwise
		"""
		try:
			return self.client.test_connection()
		except TallyConnectionError as e:
			frappe.log_error(
				message=str(e), title=_("Tally Connection Error")
			)
			return False

	def get_current_company(self):
		"""
		Get current company information from Tally

		Returns:
			dict: Company information
		"""
		try:
			return self.client.get_current_company()
		except Exception as e:
			frappe.throw(_("Failed to get company info: {0}").format(str(e)))

	def get_companies(self):
		"""
		Get list of all companies in Tally

		Returns:
			list: List of company dictionaries
		"""
		try:
			return self.client.get_companies()
		except Exception as e:
			frappe.throw(_("Failed to get companies: {0}").format(str(e)))

	def get_ledgers(self, company=None):
		"""
		Get all ledgers from Tally

		Args:
			company: Company name (optional)

		Returns:
			list: List of ledger dictionaries
		"""
		try:
			return self.client.get_ledgers(company=company)
		except Exception as e:
			frappe.throw(_("Failed to get ledgers: {0}").format(str(e)))

	def create_ledger(self, name, parent, address=None, mobile=None, email=None, **kwargs):
		"""
		Create a new ledger in Tally

		Args:
			name: Ledger name
			parent: Parent ledger group
			address: Address (optional)
			mobile: Mobile number (optional)
			email: Email (optional)
			**kwargs: Additional ledger properties

		Returns:
			dict: Response from Tally
		"""
		try:
			return self.client.create_ledger(
				name=name,
				parent=parent,
				address=address,
				mobile=mobile,
				email=email,
				**kwargs
			)
		except Exception as e:
			frappe.throw(_("Failed to create ledger: {0}").format(str(e)))

	def get_stock_items(self, company=None):
		"""
		Get all stock items from Tally

		Args:
			company: Company name (optional)

		Returns:
			list: List of stock item dictionaries
		"""
		try:
			return self.client.get_stock_items(company=company)
		except Exception as e:
			frappe.throw(_("Failed to get stock items: {0}").format(str(e)))

	def create_stock_item(self, name, category, unit, **kwargs):
		"""
		Create a new stock item in Tally

		Args:
			name: Item name
			category: Item category
			unit: Unit of measurement
			**kwargs: Additional item properties

		Returns:
			dict: Response from Tally
		"""
		try:
			return self.client.create_stock_item(
				name=name,
				category=category,
				unit=unit,
				**kwargs
			)
		except Exception as e:
			frappe.throw(_("Failed to create stock item: {0}").format(str(e)))

	def get_vouchers(self, voucher_type=None, from_date=None, to_date=None):
		"""
		Get vouchers from Tally

		Args:
			voucher_type: Type of voucher (Sales, Purchase, etc.)
			from_date: Start date (optional)
			to_date: End date (optional)

		Returns:
			list: List of voucher dictionaries
		"""
		try:
			return self.client.get_vouchers(
				voucher_type=voucher_type,
				from_date=from_date,
				to_date=to_date
			)
		except Exception as e:
			frappe.throw(_("Failed to get vouchers: {0}").format(str(e)))

	def create_voucher(self, voucher_type, date, ledger_entries, narration=None, **kwargs):
		"""
		Create a voucher in Tally

		Args:
			voucher_type: Type of voucher (Sales, Purchase, Receipt, Payment, Journal)
			date: Voucher date
			ledger_entries: List of ledger entry dictionaries
			narration: Voucher narration (optional)
			**kwargs: Additional voucher properties

		Returns:
			dict: Response from Tally
		"""
		try:
			return self.client.create_voucher(
				voucher_type=voucher_type,
				date=date,
				ledger_entries=ledger_entries,
				narration=narration,
				**kwargs
			)
		except Exception as e:
			frappe.throw(_("Failed to create voucher: {0}").format(str(e)))

	def get_groups(self, group_type="Ledger"):
		"""
		Get groups from Tally

		Args:
			group_type: Type of group (Ledger, Stock, etc.)

		Returns:
			list: List of group dictionaries
		"""
		try:
			return self.client.get_groups(group_type=group_type)
		except Exception as e:
			frappe.throw(_("Failed to get groups: {0}").format(str(e)))


@frappe.whitelist()
def test_tally_connection(host=None, port=None):
	"""
	Test connection to Tally server (whitelisted for API access)

	Args:
		host: Tally server host
		port: Tally server port

	Returns:
		dict: Connection status
	"""
	try:
		client = TallyClient(host=host, port=port)
		if client.test_connection():
			return {
				"success": True,
				"message": _("Successfully connected to Tally server")
			}
		else:
			return {
				"success": False,
				"message": _("Failed to connect to Tally server")
			}
	except Exception as e:
		return {
			"success": False,
			"message": str(e)
		}
