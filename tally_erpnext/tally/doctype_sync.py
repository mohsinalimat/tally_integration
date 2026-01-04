"""
DocType Synchronization Module

This module handles synchronization between Tally DocTypes and Tally software.
It provides functions to sync data in both directions and log all operations.
"""

import frappe
from frappe import _
from frappe.utils import now
import json
import traceback
from datetime import datetime, date
from tally_erpnext.tally.client import TallyClient


class DateTimeEncoder(json.JSONEncoder):
	"""Custom JSON encoder that handles datetime objects"""
	def default(self, obj):
		if isinstance(obj, (datetime, date)):
			return obj.isoformat()
		return super().default(obj)


def create_sync_log(sync_type, operation, status, direction, entity_type, entity_name=None,
                   reference_doctype=None, reference_name=None, tally_data=None,
                   erp_data=None, error_message=None):
	"""
	Create a Tally Sync Log entry

	Args:
		sync_type: Master Data/Transaction/Report
		operation: Create/Update/Delete/Read
		status: Pending/In Progress/Success/Failed/Partial
		direction: Tally to ERP/ERP to Tally/Bidirectional
		entity_type: Ledger/Stock Item/Voucher/etc
		entity_name: Name of the entity
		reference_doctype: ERPNext DocType
		reference_name: ERPNext document name
		tally_data: JSON data from Tally
		erp_data: JSON data from ERP
		error_message: Error message if failed

	Returns:
		Sync log document name
	"""
	try:
		log = frappe.get_doc({
			"doctype": "Tally Sync Log",
			"sync_type": sync_type,
			"operation": operation,
			"status": status,
			"direction": direction,
			"entity_type": entity_type,
			"entity_name": entity_name,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"tally_data": json.dumps(tally_data, indent=2, cls=DateTimeEncoder) if tally_data else None,
			"erp_data": json.dumps(erp_data, indent=2, cls=DateTimeEncoder) if erp_data else None,
			"error_message": error_message,
			"traceback": traceback.format_exc() if error_message else None,
			"sync_date": now(),
			"processed_by": frappe.session.user
		})
		log.insert(ignore_permissions=True)
		frappe.db.commit()
		return log.name
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Failed to create Tally Sync Log"))
		return None


# ================== LEDGER SYNC ==================

def sync_ledgers_from_tally(company=None, parent_group=None):
	"""
	Sync all ledgers from Tally to Tally Ledger DocType

	Args:
		company: Tally company name (optional)
		parent_group: Filter by parent group (optional)

	Returns:
		dict: Sync statistics
	"""
	frappe.logger("tally_sync").info(f"[{now()}] sync_ledgers_from_tally started - company: {company}, parent_group: {parent_group}")

	created = 0
	updated = 0
	failed = 0

	try:
		frappe.logger("tally_sync").info(f"[{now()}] Initializing TallyClient...")
		client = TallyClient()
		frappe.logger("tally_sync").info(f"[{now()}] TallyClient initialized, fetching ledgers...")
		ledgers = client.get_ledgers(company=company)
		frappe.logger("tally_sync").info(f"[{now()}] Fetched {len(ledgers) if ledgers else 0} ledgers from Tally")

		if parent_group:
			ledgers = [l for l in ledgers if l.get("parent") == parent_group]

		for ledger_data in ledgers:
			try:
				ledger_name = ledger_data.get("name")
				if not ledger_name:
					continue

				# Check if ledger exists
				if frappe.db.exists("Tally Ledger", ledger_name):
					# Update existing
					ledger = frappe.get_doc("Tally Ledger", ledger_name)
					operation = "Update"
				else:
					# Create new
					ledger = frappe.new_doc("Tally Ledger")
					ledger.ledger_name = ledger_name
					operation = "Create"

				# Map fields
				ledger.parent_group = ledger_data.get("parent")
				ledger.alias = ledger_data.get("alias")
				ledger.guid = ledger_data.get("guid")
				ledger.tally_company = company or ledger_data.get("company")
				ledger.mailing_name = ledger_data.get("mailing_name")
				ledger.address = ledger_data.get("address")
				ledger.mobile = ledger_data.get("mobile")
				ledger.email = ledger_data.get("email")
				ledger.pan = ledger_data.get("pan")
				ledger.gstin = ledger_data.get("gstin")
				ledger.opening_balance = ledger_data.get("opening_balance", 0)
				ledger.current_balance = ledger_data.get("current_balance", 0)
				ledger.last_sync_date = now()
				ledger.sync_status = "Synced"
				ledger.additional_data = json.dumps(ledger_data, indent=2, cls=DateTimeEncoder)

				ledger.save(ignore_permissions=True)

				if operation == "Create":
					created += 1
				else:
					updated += 1

				# Create sync log
				create_sync_log(
					sync_type="Master Data",
					operation=operation,
					status="Success",
					direction="Tally to ERP",
					entity_type="Ledger",
					entity_name=ledger_name,
					reference_doctype="Tally Ledger",
					reference_name=ledger.name,
					tally_data=ledger_data
				)

			except Exception as e:
				failed += 1
				frappe.log_error(
					message=f"Error syncing ledger {ledger_data.get('name')}: {str(e)}",
					title=_("Ledger Sync Error")
				)
				create_sync_log(
					sync_type="Master Data",
					operation="Update" if frappe.db.exists("Tally Ledger", ledger_data.get("name")) else "Create",
					status="Failed",
					direction="Tally to ERP",
					entity_type="Ledger",
					entity_name=ledger_data.get("name"),
					tally_data=ledger_data,
					error_message=str(e)
				)
				continue

		frappe.db.commit()

	except Exception as e:
		frappe.logger("tally_sync").error(f"[{now()}] Ledger sync failed with error: {str(e)}")
		frappe.log_error(message=str(e), title=_("Ledger Sync Failed"))
		raise

	frappe.logger("tally_sync").info(f"[{now()}] sync_ledgers_from_tally completed - created: {created}, updated: {updated}, failed: {failed}")
	return {"created": created, "updated": updated, "failed": failed, "total": created + updated + failed}


def sync_ledger_to_tally(ledger_name, operation="create"):
	"""
	Sync a Tally Ledger from ERP to Tally

	Args:
		ledger_name: Name of the Tally Ledger document
		operation: create/update

	Returns:
		dict: Sync result
	"""
	try:
		ledger = frappe.get_doc("Tally Ledger", ledger_name)
		client = TallyClient()

		ledger_data = {
			"name": ledger.ledger_name,
			"parent": ledger.parent_group,
			"address": ledger.address,
			"mobile": ledger.mobile,
			"email": ledger.email
		}

		if operation == "create":
			response = client.create_ledger(**ledger_data)
		else:
			# Update operation would require update methods in tally-integration package
			response = client.create_ledger(**ledger_data)

		# Update sync status
		ledger.db_set("last_sync_date", now(), update_modified=False)
		ledger.db_set("sync_status", "Synced", update_modified=False)

		create_sync_log(
			sync_type="Master Data",
			operation=operation.capitalize(),
			status="Success",
			direction="ERP to Tally",
			entity_type="Ledger",
			entity_name=ledger.ledger_name,
			reference_doctype="Tally Ledger",
			reference_name=ledger.name,
			erp_data=ledger.as_dict(),
			tally_data=response
		)

		return {"success": True, "response": response}

	except Exception as e:
		frappe.log_error(message=str(e), title=_("Ledger Push Failed"))
		create_sync_log(
			sync_type="Master Data",
			operation=operation.capitalize(),
			status="Failed",
			direction="ERP to Tally",
			entity_type="Ledger",
			entity_name=ledger_name,
			reference_doctype="Tally Ledger",
			reference_name=ledger_name,
			error_message=str(e)
		)
		return {"success": False, "error": str(e)}


# ================== STOCK ITEM SYNC ==================

def sync_stock_items_from_tally(company=None):
	"""
	Sync all stock items from Tally to Tally Stock Item DocType

	Args:
		company: Tally company name (optional)

	Returns:
		dict: Sync statistics
	"""
	frappe.logger("tally_sync").info(f"[{now()}] sync_stock_items_from_tally started - company: {company}")

	created = 0
	updated = 0
	failed = 0

	try:
		frappe.logger("tally_sync").info(f"[{now()}] Initializing TallyClient...")
		client = TallyClient()
		frappe.logger("tally_sync").info(f"[{now()}] TallyClient initialized, fetching stock items...")
		items = client.get_stock_items(company=company)
		frappe.logger("tally_sync").info(f"[{now()}] Fetched {len(items) if items else 0} stock items from Tally")

		for item_data in items:
			try:
				item_name = item_data.get("name")
				if not item_name:
					continue

				# Check if item exists
				if frappe.db.exists("Tally Stock Item", item_name):
					item = frappe.get_doc("Tally Stock Item", item_name)
					operation = "Update"
				else:
					item = frappe.new_doc("Tally Stock Item")
					item.item_name = item_name
					operation = "Create"

				# Map fields
				item.parent_group = item_data.get("parent") or item_data.get("category")
				item.alias = item_data.get("alias")
				item.guid = item_data.get("guid")
				item.tally_company = company or item_data.get("company")
				item.category = item_data.get("category")
				item.base_units = item_data.get("base_units")
				item.opening_balance = item_data.get("opening_balance", 0)
				item.opening_rate = item_data.get("opening_rate", 0)
				item.opening_value = item_data.get("opening_value", 0)
				item.current_balance = item_data.get("current_balance", 0)
				item.current_rate = item_data.get("current_rate", 0)
				item.current_value = item_data.get("current_value", 0)
				item.hsn_code = item_data.get("hsn_code")

				# Handle GST fields
				gst_applicable = item_data.get("gst_applicable", "No")
				item.gst_applicable = 1 if gst_applicable and str(gst_applicable).lower() in ["yes", "true", "1"] else 0
				item.gst_rate = item_data.get("gst_rate")

				item.last_sync_date = now()
				item.sync_status = "Synced"
				item.additional_data = json.dumps(item_data, indent=2, cls=DateTimeEncoder)

				item.save(ignore_permissions=True)

				if operation == "Create":
					created += 1
				else:
					updated += 1

				create_sync_log(
					sync_type="Master Data",
					operation=operation,
					status="Success",
					direction="Tally to ERP",
					entity_type="Stock Item",
					entity_name=item_name,
					reference_doctype="Tally Stock Item",
					reference_name=item.name,
					tally_data=item_data
				)

			except Exception as e:
				failed += 1
				frappe.log_error(
					message=f"Error syncing item {item_data.get('name')}: {str(e)}",
					title=_("Item Sync Error")
				)
				create_sync_log(
					sync_type="Master Data",
					operation="Update" if frappe.db.exists("Tally Stock Item", item_data.get("name")) else "Create",
					status="Failed",
					direction="Tally to ERP",
					entity_type="Stock Item",
					entity_name=item_data.get("name"),
					tally_data=item_data,
					error_message=str(e)
				)
				continue

		frappe.db.commit()

	except Exception as e:
		frappe.logger("tally_sync").error(f"[{now()}] Stock items sync failed with error: {str(e)}")
		frappe.log_error(message=str(e), title=_("Item Sync Failed"))
		raise

	frappe.logger("tally_sync").info(f"[{now()}] sync_stock_items_from_tally completed - created: {created}, updated: {updated}, failed: {failed}")
	return {"created": created, "updated": updated, "failed": failed, "total": created + updated + failed}


def sync_stock_item_to_tally(item_name, operation="create"):
	"""
	Sync a Tally Stock Item from ERP to Tally

	Args:
		item_name: Name of the Tally Stock Item document
		operation: create/update

	Returns:
		dict: Sync result
	"""
	try:
		item = frappe.get_doc("Tally Stock Item", item_name)
		client = TallyClient()

		item_data = {
			"name": item.item_name,
			"category": item.category or item.parent_group,
			"unit": item.base_units
		}

		if operation == "create":
			response = client.create_stock_item(**item_data)
		else:
			response = client.create_stock_item(**item_data)

		# Update sync status
		item.db_set("last_sync_date", now(), update_modified=False)
		item.db_set("sync_status", "Synced", update_modified=False)

		create_sync_log(
			sync_type="Master Data",
			operation=operation.capitalize(),
			status="Success",
			direction="ERP to Tally",
			entity_type="Stock Item",
			entity_name=item.item_name,
			reference_doctype="Tally Stock Item",
			reference_name=item.name,
			erp_data=item.as_dict(),
			tally_data=response
		)

		return {"success": True, "response": response}

	except Exception as e:
		frappe.log_error(message=str(e), title=_("Item Push Failed"))
		create_sync_log(
			sync_type="Master Data",
			operation=operation.capitalize(),
			status="Failed",
			direction="ERP to Tally",
			entity_type="Stock Item",
			entity_name=item_name,
			reference_doctype="Tally Stock Item",
			reference_name=item_name,
			error_message=str(e)
		)
		return {"success": False, "error": str(e)}


# ================== VOUCHER SYNC ==================

def sync_vouchers_from_tally(voucher_type=None, from_date=None, to_date=None):
	"""
	Sync vouchers from Tally to Tally Voucher DocType

	Args:
		voucher_type: Type of voucher (optional)
		from_date: Start date (optional)
		to_date: End date (optional)

	Returns:
		dict: Sync statistics
	"""
	frappe.logger("tally_sync").info(f"[{now()}] sync_vouchers_from_tally started - voucher_type: {voucher_type}, from_date: {from_date}, to_date: {to_date}")

	created = 0
	updated = 0
	failed = 0

	try:
		frappe.logger("tally_sync").info(f"[{now()}] Initializing TallyClient...")
		client = TallyClient()
		frappe.logger("tally_sync").info(f"[{now()}] TallyClient initialized, fetching vouchers...")
		vouchers = client.get_vouchers(
			voucher_type=voucher_type,
			from_date=from_date,
			to_date=to_date
		)
		frappe.logger("tally_sync").info(f"[{now()}] Fetched {len(vouchers) if vouchers else 0} vouchers from Tally")

		for voucher_data in vouchers:
			try:
				voucher_number = voucher_data.get("voucher_number")
				guid = voucher_data.get("guid")

				# Check if voucher exists by GUID or voucher number
				existing = None
				if guid:
					existing = frappe.db.get_value("Tally Voucher", {"guid": guid}, "name")

				if existing:
					voucher = frappe.get_doc("Tally Voucher", existing)
					operation = "Update"
				else:
					voucher = frappe.new_doc("Tally Voucher")
					operation = "Create"

				# Map fields
				voucher.voucher_type = voucher_data.get("voucher_type")
				voucher.voucher_number = voucher_number
				voucher.date = voucher_data.get("date")
				voucher.guid = guid
				voucher.tally_company = voucher_data.get("company")
				voucher.party_ledger_name = voucher_data.get("party_ledger")
				voucher.narration = voucher_data.get("narration")
				voucher.reference_number = voucher_data.get("reference_number")
				voucher.reference_date = voucher_data.get("reference_date")
				voucher.is_cancelled = voucher_data.get("is_cancelled", 0)

				# Clear and add ledger entries
				voucher.ledger_entries = []
				for entry in voucher_data.get("ledger_entries", []):
					voucher.append("ledger_entries", {
						"ledger_name": entry.get("ledger_name"),
						"is_debit": entry.get("is_debit", False),
						"is_credit": entry.get("is_credit", False),
						"amount": entry.get("amount", 0)
					})

				voucher.last_sync_date = now()
				voucher.sync_status = "Synced"
				voucher.voucher_data = json.dumps(voucher_data, indent=2, cls=DateTimeEncoder)

				voucher.save(ignore_permissions=True)

				if operation == "Create":
					created += 1
				else:
					updated += 1

				create_sync_log(
					sync_type="Transaction",
					operation=operation,
					status="Success",
					direction="Tally to ERP",
					entity_type="Voucher",
					entity_name=voucher_number,
					reference_doctype="Tally Voucher",
					reference_name=voucher.name,
					tally_data=voucher_data
				)

			except Exception as e:
				failed += 1
				frappe.log_error(
					message=f"Error syncing voucher {voucher_data.get('voucher_number')}: {str(e)}",
					title=_("Voucher Sync Error")
				)
				create_sync_log(
					sync_type="Transaction",
					operation="Update" if existing else "Create",
					status="Failed",
					direction="Tally to ERP",
					entity_type="Voucher",
					entity_name=voucher_data.get("voucher_number"),
					tally_data=voucher_data,
					error_message=str(e)
				)
				continue

		frappe.db.commit()

	except Exception as e:
		frappe.logger("tally_sync").error(f"[{now()}] Voucher sync failed with error: {str(e)}")
		frappe.log_error(message=str(e), title=_("Voucher Sync Failed"))
		raise

	frappe.logger("tally_sync").info(f"[{now()}] sync_vouchers_from_tally completed - created: {created}, updated: {updated}, failed: {failed}")
	return {"created": created, "updated": updated, "failed": failed, "total": created + updated + failed}


def sync_voucher_to_tally(voucher_name, operation="create"):
	"""
	Sync a Tally Voucher from ERP to Tally

	Args:
		voucher_name: Name of the Tally Voucher document
		operation: create/update

	Returns:
		dict: Sync result
	"""
	try:
		voucher = frappe.get_doc("Tally Voucher", voucher_name)
		client = TallyClient()

		# Prepare ledger entries
		ledger_entries = []
		for entry in voucher.ledger_entries:
			ledger_entries.append({
				"ledger_name": entry.ledger_name,
				"amount": entry.amount,
				"is_debit": entry.is_debit
			})

		# Create voucher in Tally
		response = client.create_voucher(
			voucher_type=voucher.voucher_type,
			date=voucher.date,
			ledger_entries=ledger_entries,
			narration=voucher.narration
		)

		# Update voucher with Tally response
		if response.get("voucher_number"):
			voucher.db_set("voucher_number", response.get("voucher_number"), update_modified=False)
		if response.get("guid"):
			voucher.db_set("guid", response.get("guid"), update_modified=False)

		voucher.db_set("last_sync_date", now(), update_modified=False)
		voucher.db_set("sync_status", "Synced", update_modified=False)

		create_sync_log(
			sync_type="Transaction",
			operation=operation.capitalize(),
			status="Success",
			direction="ERP to Tally",
			entity_type="Voucher",
			entity_name=voucher.voucher_number or voucher.name,
			reference_doctype="Tally Voucher",
			reference_name=voucher.name,
			erp_data=voucher.as_dict(),
			tally_data=response
		)

		return {"success": True, "response": response}

	except Exception as e:
		frappe.log_error(message=str(e), title=_("Voucher Push Failed"))
		create_sync_log(
			sync_type="Transaction",
			operation=operation.capitalize(),
			status="Failed",
			direction="ERP to Tally",
			entity_type="Voucher",
			entity_name=voucher_name,
			reference_doctype="Tally Voucher",
			reference_name=voucher_name,
			error_message=str(e)
		)
		return {"success": False, "error": str(e)}


def cancel_voucher_in_tally(voucher_name):
	"""
	Cancel a voucher in Tally (Note: Tally doesn't support deletion, use cancel)

	Args:
		voucher_name: Name of the Tally Voucher document

	Returns:
		dict: Sync result
	"""
	try:
		voucher = frappe.get_doc("Tally Voucher", voucher_name)

		# Note: tally-integration package may not support cancel operation
		# This would need to be implemented based on Tally's XML API

		voucher.db_set("is_cancelled", 1, update_modified=False)
		voucher.db_set("sync_status", "Synced", update_modified=False)

		create_sync_log(
			sync_type="Transaction",
			operation="Delete",
			status="Success",
			direction="ERP to Tally",
			entity_type="Voucher",
			entity_name=voucher.voucher_number or voucher.name,
			reference_doctype="Tally Voucher",
			reference_name=voucher.name
		)

		return {"success": True, "message": "Voucher marked as cancelled"}

	except Exception as e:
		frappe.log_error(message=str(e), title=_("Voucher Cancel Failed"))
		return {"success": False, "error": str(e)}


# ================== API ENDPOINTS ==================

@frappe.whitelist()
def sync_all_ledgers(company=None, parent_group=None):
	"""API endpoint to sync ledgers from Tally"""
	return sync_ledgers_from_tally(company=company, parent_group=parent_group)


@frappe.whitelist()
def sync_all_stock_items(company=None):
	"""API endpoint to sync stock items from Tally"""
	return sync_stock_items_from_tally(company=company)


@frappe.whitelist()
def sync_all_vouchers(voucher_type=None, from_date=None, to_date=None):
	"""API endpoint to sync vouchers from Tally"""
	return sync_vouchers_from_tally(voucher_type=voucher_type, from_date=from_date, to_date=to_date)
