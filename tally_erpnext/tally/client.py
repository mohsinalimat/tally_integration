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

	def __init__(self, host=None, port=None, timeout=30):
		"""
		Initialize Tally Client with settings from Frappe

		Args:
			host: Tally server host (defaults to settings or localhost)
			port: Tally server port (defaults to settings or 9000)
			timeout: Request timeout in seconds (defaults to 30)
		"""
		# Get settings from Tally Settings doctype if not provided
		if not host or not port:
			settings = self.get_tally_settings()
			host = host or settings.get("host", "localhost")
			port = port or settings.get("port", 9000)

		# Format host as URL if not already
		if not host.startswith("http"):
			tally_url = f"http://{host}"
		else:
			tally_url = host

		try:
			self.client = BaseTallyClient(tally_url=tally_url, tally_port=int(port), timeout=timeout)
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
			xml_response = self.client.get_current_company()
			return self.client.parse_xml_response(xml_response)
		except Exception as e:
			frappe.throw(_("Failed to get company info: {0}").format(str(e)))

	def get_companies(self):
		"""
		Get list of all companies in Tally

		Returns:
			list: List of company dictionaries
		"""
		try:
			xml_response = self.client.get_companies_list()
			parsed = self.client.parse_xml_response(xml_response)
			# Extract companies from parsed response
			companies = parsed.get("ENVELOPE", {}).get("BODY", {}).get("DATA", {}).get("COLLECTION", {}).get("COMPANY", [])
			if isinstance(companies, dict):
				companies = [companies]
			return companies
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
			xml_response = self.client.get_ledgers_list(company_name=company)
			parsed = self.client.parse_xml_response(xml_response)

			# Extract ledgers from parsed response - structure may vary
			# Try different possible paths in the XML structure
			ledgers = []

			envelope = parsed.get("ENVELOPE", parsed)
			body = envelope.get("BODY", envelope)
			data = body.get("DATA", body)
			collection = data.get("COLLECTION", data)

			# Ledgers might be under LEDGER key
			ledger_data = collection.get("LEDGER", [])
			if isinstance(ledger_data, dict):
				ledger_data = [ledger_data]

			for ledger in ledger_data:
				ledgers.append({
					"name": ledger.get("NAME", ledger.get("@NAME", "")),
					"parent": ledger.get("PARENT", ""),
					"guid": ledger.get("GUID", ""),
					"opening_balance": ledger.get("OPENINGBALANCE", 0),
					"closing_balance": ledger.get("CLOSINGBALANCE", 0),
					"address": ledger.get("ADDRESS", ""),
					"mobile": ledger.get("LEDGERPHONE", ledger.get("MOBILE", "")),
					"email": ledger.get("EMAIL", ""),
					"gstin": ledger.get("PARTYGSTIN", ledger.get("GSTIN", "")),
					"pan": ledger.get("INCOMETAXNUMBER", ledger.get("PAN", "")),
				})

			return ledgers
		except Exception as e:
			frappe.throw(_("Failed to get ledgers: {0}").format(str(e)))

	def create_ledger(self, name, parent, address=None, mobile=None, gstin=None, **kwargs):
		"""
		Create a new ledger in Tally

		Args:
			name: Ledger name
			parent: Parent ledger group
			address: Address (optional)
			mobile: Mobile number (optional)
			gstin: GSTIN (optional)
			**kwargs: Additional ledger properties

		Returns:
			dict: Response from Tally
		"""
		try:
			xml_response = self.client.create_ledger(
				name=name,
				parent=parent,
				address=address,
				mobile=mobile,
				gstin=gstin
			)
			return self.client.parse_xml_response(xml_response)
		except Exception as e:
			frappe.throw(_("Failed to create ledger: {0}").format(str(e)))

	def get_stock_items(self, company=None):
		"""
		Get all stock items from Tally

		NOTE: The tally-integration package (v1.0.0) does not support stock items.
		This method returns an empty list. For stock item support, you need to:
		1. Extend the package with custom XML requests, or
		2. Wait for package updates with stock item support

		Args:
			company: Company name (optional)

		Returns:
			list: Empty list (not supported in current package version)
		"""
		frappe.logger("tally_sync").warning(
			"get_stock_items: Not supported in tally-integration v1.0.0. Returning empty list."
		)
		# Stock items not supported in tally-integration v1.0.0
		return []

	def create_stock_item(self, name, category, unit, **kwargs):
		"""
		Create a new stock item in Tally

		NOTE: Not supported in tally-integration v1.0.0

		Args:
			name: Item name
			category: Item category
			unit: Unit of measurement
			**kwargs: Additional item properties

		Returns:
			dict: Error response (not supported)
		"""
		frappe.throw(_("Stock item creation not supported in tally-integration v1.0.0"))

	def get_vouchers(self, voucher_type=None, from_date=None, to_date=None):
		"""
		Get vouchers from Tally

		NOTE: The tally-integration package (v1.0.0) does not support vouchers.
		This method returns an empty list. For voucher support, you need to:
		1. Extend the package with custom XML requests, or
		2. Wait for package updates with voucher support

		Args:
			voucher_type: Type of voucher (Sales, Purchase, etc.)
			from_date: Start date (optional)
			to_date: End date (optional)

		Returns:
			list: Empty list (not supported in current package version)
		"""
		frappe.logger("tally_sync").warning(
			"get_vouchers: Not supported in tally-integration v1.0.0. Returning empty list."
		)
		# Vouchers not supported in tally-integration v1.0.0
		return []

	def create_voucher(self, voucher_type, date, ledger_entries, narration=None, **kwargs):
		"""
		Create a voucher in Tally

		NOTE: Not supported in tally-integration v1.0.0

		Args:
			voucher_type: Type of voucher (Sales, Purchase, Receipt, Payment, Journal)
			date: Voucher date
			ledger_entries: List of ledger entry dictionaries
			narration: Voucher narration (optional)
			**kwargs: Additional voucher properties

		Returns:
			dict: Error response (not supported)
		"""
		frappe.throw(_("Voucher creation not supported in tally-integration v1.0.0"))

	def get_groups(self, group_type="Ledger"):
		"""
		Get groups from Tally

		NOTE: Not supported in tally-integration v1.0.0

		Args:
			group_type: Type of group (Ledger, Stock, etc.)

		Returns:
			list: Empty list (not supported)
		"""
		frappe.logger("tally_sync").warning(
			"get_groups: Not supported in tally-integration v1.0.0. Returning empty list."
		)
		return []


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
