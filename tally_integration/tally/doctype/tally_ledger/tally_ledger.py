# Copyright (c) 2025, SVNIX Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TallyLedger(Document):
	"""Tally Ledger - 1:1 representation of Tally Ledger in ERPNext"""

	def validate(self):
		"""Validate Tally Ledger"""
		if not self.ledger_name:
			frappe.throw(_("Ledger Name is required"))

	def on_update(self):
		"""Handle updates and sync to Tally if auto_sync is enabled"""
		if self.auto_sync and self.sync_direction in ["ERP to Tally", "Bidirectional"]:
			if self.has_value_changed("ledger_name") or self.has_value_changed("parent_group"):
				frappe.enqueue(
					"tally_integration.tally.doctype_sync.sync_ledger_to_tally",
					queue="short",
					timeout=300,
					ledger_name=self.name,
					operation="update"
				)

	def after_insert(self):
		"""Handle new ledger creation"""
		if self.auto_sync and self.sync_direction in ["ERP to Tally", "Bidirectional"]:
			frappe.enqueue(
				"tally_integration.tally.doctype_sync.sync_ledger_to_tally",
				queue="short",
				timeout=300,
				ledger_name=self.name,
				operation="create"
			)

	def on_trash(self):
		"""Handle ledger deletion"""
		# Note: Tally doesn't support deletion, so we just mark as inactive
		if self.auto_sync:
			frappe.msgprint(_("Tally ledgers cannot be deleted. They are marked as inactive instead."))
