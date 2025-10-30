// Copyright (c) 2025, dharanidharan s and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Import Biodatas", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Import Biodatas", {
	refresh: function (frm) {
		// Disable add/delete actions in child table
		frm.events.toggle_add_delete_actions(frm);
	},

	upload_bio: function (frm) {
		if (!frm.doc.upload_bio) return;

		frappe.show_alert({ message: "Reading uploaded file...", indicator: "blue" });

		frappe.call({
			method: "emp_checkin.employe_check_in_automation.doctype.import_biodatas.import_biodatas.import_attendance",
			args: {
				file_name: frm.doc.upload_bio,
			},
			callback: function (r) {
				if (r.message && Array.isArray(r.message)) {
					frm.clear_table("employee_import_items");

					r.message.forEach((row) => {
						let child = frm.add_child("employee_import_items");
						child.emp_id = row["EmpID"] || "";
						child.emp_name = row["EmpName"] || "";
						child.department = row["Department"] || "";
						child.date = row["Date"] || "";
						child.on_duty = row["On-duty"] || "";
						child.off_duty = row["Off-duty"] || "";
						child.status = row["Status"] || "";
					});

					frm.refresh_field("employee_import_items");
					frappe.show_alert({
						message: "Employee data loaded successfully!",
						indicator: "green",
					});
				} else {
					frappe.msgprint("No data found or unable to read file.");
				}
			},
		});
	},

	toggle_add_delete_actions: function (frm) {
		frm.set_df_property("employee_import_items", "cannot_add_rows", true);
		frm.set_df_property("employee_import_items", "cannot_delete_rows", true);
	},
});
