"""
Tally Client Wrapper for Frappe/ERPNext Integration

This module provides a Frappe-friendly wrapper around the TallyClient,
handling connection management, error handling, and data transformation.
"""

import frappe
from frappe import _
from tally_erpnext.tally.xmlFunctions import TallyClient as BaseTallyClient


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
		except Exception as e:
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

		Args:
			company: Company name (optional)

		Returns:
			list: List of stock item dictionaries
		"""
		try:
			xml_response = self.client.get_stock_items_list()
			parsed = self.client.parse_xml_response(xml_response)

			# Extract stock items from parsed response
			stock_items = []
			envelope = parsed.get("ENVELOPE", parsed)
			body = envelope.get("BODY", envelope)
			data = body.get("DATA", body)
			collection = data.get("COLLECTION", data)

			# Stock items might be under STOCKITEM key
			item_data = collection.get("STOCKITEM", [])
			if isinstance(item_data, dict):
				item_data = [item_data]

			for item in item_data:
				stock_items.append({
					"name": item.get("NAME", item.get("@NAME", "")),
					"guid": item.get("GUID", ""),
					"master_id": item.get("MASTERID", ""),
					"parent": item.get("PARENT", ""),
					"base_units": item.get("BASEUNITS", ""),
					"opening_balance": item.get("OPENINGBALANCE", 0),
					"opening_value": item.get("OPENINGVALUE", 0),
				})

			return stock_items
		except Exception as e:
			frappe.log_error(message=str(e), title=_("Failed to get stock items"))
			return []

	def create_stock_item(self, name, category, unit, **kwargs):
		"""
		Create a new stock item in Tally

		Args:
			name: Item name
			category: Item category (not used, kept for compatibility)
			unit: Unit of measurement
			**kwargs: Additional item properties (opening_balance, hsn_code, gst_rate)

		Returns:
			dict: Response from Tally
		"""
		try:
			opening_balance = kwargs.get('opening_balance', 0)
			hsn_code = kwargs.get('hsn_code')
			gst_rate = kwargs.get('gst_rate')

			xml_response = self.client.create_stock_item(
				name=name,
				base_unit=unit,
				opening_balance=opening_balance,
				hsn_code=hsn_code,
				gst_rate=gst_rate
			)
			return self.client.parse_xml_response(xml_response)
		except Exception as e:
			frappe.throw(_("Failed to create stock item: {0}").format(str(e)))

	def get_vouchers(self, voucher_type=None, from_date=None, to_date=None, company_name=None):
		"""
		Get vouchers from Tally

		Args:
			voucher_type: Type of voucher (Sales, Purchase, etc.)
			from_date: Start date (format: YYYYMMDD or DD-MMM-YYYY)
			to_date: End date (format: YYYYMMDD or DD-MMM-YYYY)
			company_name: Company name (optional)

		Returns:
			list: List of voucher dictionaries
		"""
		try:
			if not company_name:
				settings = self.get_tally_settings()
				company_name = settings.get("default_company", "")

			if not from_date or not to_date:
				from datetime import datetime, timedelta
				to_date = datetime.now().strftime("%Y%m%d")
				from_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

			if voucher_type and from_date and to_date and company_name:
				xml_response = self.client.get_vouchers_by_type(
					company_name=company_name,
					from_date=from_date,
					to_date=to_date,
					voucher_type=voucher_type
				)
			else:
				# Use sales report as fallback
				xml_response = self.client.get_sales_report()

			parsed = self.client.parse_xml_response(xml_response)
			return self._extract_vouchers(parsed)
		except Exception as e:
			frappe.log_error(message=str(e), title=_("Failed to get vouchers"))
			return []

	def _extract_vouchers(self, parsed_response):
		"""Extract vouchers from parsed XML response"""
		vouchers = []
		envelope = parsed_response.get("ENVELOPE", parsed_response)
		body = envelope.get("BODY", envelope)
		data = body.get("DATA", body)

		# Try different possible paths
		voucher_data = data.get("VOUCHER", data.get("TALLYMESSAGE", {}).get("VOUCHER", []))
		if isinstance(voucher_data, dict):
			voucher_data = [voucher_data]

		for voucher in voucher_data:
			vouchers.append({
				"voucher_number": voucher.get("VOUCHERNUMBER", ""),
				"voucher_type": voucher.get("VOUCHERTYPENAME", ""),
				"date": voucher.get("DATE", ""),
				"master_id": voucher.get("MASTERID", ""),
				"narration": voucher.get("NARRATION", ""),
				"party_name": voucher.get("PARTYLEDGERNAME", ""),
			})

		return vouchers

	def create_voucher(self, voucher_type, date, ledger_entries, narration=None, **kwargs):
		"""
		Create a voucher in Tally

		Args:
			voucher_type: Type of voucher (Sales, Purchase, Receipt, Payment, Journal)
			date: Voucher date (format: YYYYMMDD)
			ledger_entries: List of ledger entry dictionaries with keys:
							- ledger_name (str)
							- is_debit (bool)
							- amount (float)
			narration: Voucher narration (optional)
			**kwargs: Additional voucher properties (company_name, voucher_number)

		Returns:
			dict: Response from Tally
		"""
		try:
			company_name = kwargs.get('company_name')
			voucher_number = kwargs.get('voucher_number')

			if voucher_type.lower() == 'journal':
				xml_response = self.client.create_journal_voucher(
					company_name=company_name,
					entries=ledger_entries,
					date=date,
					voucher_number=voucher_number,
					narration=narration or ""
				)
			elif voucher_type.lower() == 'receipt':
				# For receipt vouchers, extract party and amount
				party_ledger = next((e['ledger_name'] for e in ledger_entries if not e.get('is_debit')), None)
				amount = next((e['amount'] for e in ledger_entries if not e.get('is_debit')), 0)

				xml_response = self.client.create_receipt_voucher(
					party_ledger_name=party_ledger,
					amount=amount,
					date=date,
					narration=narration or "",
					voucher_number=voucher_number
				)
			else:
				frappe.throw(_("Voucher type {0} not yet supported").format(voucher_type))

			return self.client.parse_xml_response(xml_response)
		except Exception as e:
			frappe.throw(_("Failed to create voucher: {0}").format(str(e)))

	def get_groups(self, group_type="Ledger", company_name=None):
		"""
		Get groups from Tally

		Args:
			group_type: Type of group (Ledger, Stock, etc.) - currently only Ledger is supported
			company_name: Company name (optional)

		Returns:
			list: List of group dictionaries
		"""
		try:
			xml_response = self.client.get_groups_list(company_name=company_name)
			parsed = self.client.parse_xml_response(xml_response)

			# Extract groups from parsed response
			groups = []
			envelope = parsed.get("ENVELOPE", parsed)
			body = envelope.get("BODY", envelope)
			data = body.get("DATA", body)
			collection = data.get("COLLECTION", data)

			# Groups might be under GROUP key
			group_data = collection.get("GROUP", [])
			if isinstance(group_data, dict):
				group_data = [group_data]

			for group in group_data:
				groups.append({
					"name": group.get("NAME", group.get("@NAME", "")),
					"parent": group.get("PARENT", ""),
					"master_id": group.get("MASTERID", ""),
				})

			return groups
		except Exception as e:
			frappe.log_error(message=str(e), title=_("Failed to get groups"))
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
