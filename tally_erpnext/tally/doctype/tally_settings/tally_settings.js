// Copyright (c) 2025, SVNIX Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tally Settings", {
	refresh(frm) {
		// Add Test Connection button handler
		frm.add_custom_button(__("Test Connection"), function() {
			frm.trigger("test_connection");
		});
	},

	test_connection(frm) {
		// Test connection to Tally server
		frappe.call({
			method: "tally_erpnext.tally.test_tally_connection",
			args: {
				host: frm.doc.host,
				port: frm.doc.port
			},
			freeze: true,
			freeze_message: __("Testing connection to Tally server..."),
			callback: function(r) {
				if (r.message) {
					if (r.message.success) {
						frm.set_value("connection_status", r.message.message);
						frappe.show_alert({
							message: r.message.message,
							indicator: "green"
						}, 5);
					} else {
						frm.set_value("connection_status", "Error: " + r.message.message);
						frappe.show_alert({
							message: r.message.message,
							indicator: "red"
						}, 5);
					}
				}
			}
		});
	}
});
