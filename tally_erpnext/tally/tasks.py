"""
Scheduled Tasks for Tally Sync

This module contains background tasks that run on schedule to sync data
between Tally and ERPNext.
"""

import frappe
from frappe import _


def sync_all_from_tally():
	"""
	Main scheduled task to sync all data from Tally to ERPNext.
	Runs based on scheduler_events in hooks.py.

	Only runs if:
	- Tally Settings exists and is enabled
	- Auto sync is enabled in settings
	"""
	# Check if Tally Settings exists and is enabled
	if not frappe.db.exists("Tally Settings", "Tally Settings"):
		return

	settings = frappe.get_doc("Tally Settings", "Tally Settings")

	if not settings.enabled:
		return

	if not settings.get("auto_sync"):
		return

	# Import sync functions
	from tally_erpnext.tally.doctype_sync import (
		sync_ledgers_from_tally,
		sync_stock_items_from_tally,
		sync_vouchers_from_tally
	)

	company = settings.get("default_company")

	try:
		# Sync master data
		if settings.get("sync_ledgers", True):
			frappe.enqueue(
				sync_ledgers_from_tally,
				queue="long",
				timeout=600,
				company=company
			)

		if settings.get("sync_stock_items", True):
			frappe.enqueue(
				sync_stock_items_from_tally,
				queue="long",
				timeout=600,
				company=company
			)

		# Sync transactions (vouchers)
		if settings.get("sync_vouchers", True):
			frappe.enqueue(
				sync_vouchers_from_tally,
				queue="long",
				timeout=600
			)

	except Exception as e:
		frappe.log_error(
			message=str(e),
			title=_("Tally Scheduled Sync Failed")
		)
