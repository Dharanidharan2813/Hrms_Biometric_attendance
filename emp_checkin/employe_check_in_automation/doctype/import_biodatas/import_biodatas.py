# Copyright (c) 2025, dharanidharan s and contributors
# For license information, please see license.txt

from datetime import datetime

import frappe
import pandas as pd
from frappe.model.document import Document
from hrms.hr.doctype.employee_attendance_tool.employee_attendance_tool import mark_employee_attendance


class ImportBiodatas(Document):
	def validate(self):
		for row in self.employee_import_items:
			if not row.emp_id or not row.date:
				continue

			employee_email = frappe.db.get_value(
				"Employee", row.emp_id, "company_email"
			) or frappe.db.get_value("Employee", row.emp_id, "personal_email")
			if not row.status or str(row.status).strip() == "":
				if employee_email:
					frappe.sendmail(
						recipients=employee_email,
						subject="Attendance Status Missing",
						message=f"""
                            <p>Dear Employee,</p>
                            <p>Your attendance status is missing for:</p>
                            <ul>
                                <li><b>Employee ID:</b> {row.emp_id}</li>
                                <li><b>Employee ID:</b> {row.emp_name}</li>
                                <li><b>Date:</b> {row.date}</li>
                            </ul>
                            <p>Please contact your HR Administrator to update your attendance record.</p>
                            <p>Regards,<br>HR Department</p>
                        """,
					)
					frappe.msgprint(
						f"📧 Email sent to <b>{employee_email}</b> for missing attendance status ({row.emp_id})",
						alert=True,
					)
				else:
					frappe.msgprint(
						f"⚠️ No email found for Employee ID: <b>{row.emp_id}</b>. Unable to send notification.",
						alert=True,
					)

				continue

			employee = frappe.db.exists("Employee", {"name": row.emp_id, "status": "Active"})
			if not employee:
				frappe.msgprint(f"Employee <b>{row.emp_id}</b> not found. Skipping attendance.")
				continue

			mark_employee_attendance(
				employee_list=[row.emp_id],
				status=row.status,
				date=row.date,
			)


@frappe.whitelist()
def import_attendance(file_name):
	if not file_name:
		frappe.throw("Please upload a valid ODS file before loading data.")

	file_path = frappe.get_site_path(file_name.strip("/"))

	df = pd.read_excel(file_path, engine="odf")
	df.rename(
		columns={
			"First time zone": "On-duty",
			"Unnamed: 5": "Off-duty",
		},
		inplace=True,
	)
	expected_columns = ["ID", "Name", "Department", "Date", "On-duty", "Off-duty", "Status"]
	df = df[[col for col in expected_columns if col in df.columns]]
	records = []
	for _, row in df.iterrows():
		emp_id = row.get("ID")
		emp_name = row.get("Name")
		department = row.get("Department")
		date = row.get("Date")
		on_duty = row.get("On-duty")
		off_duty = row.get("Off-duty")

		if not emp_id or not emp_name:
			continue

		if not on_duty or not off_duty or pd.isna(on_duty) or pd.isna(off_duty):
			status = " "
			records.append(
				{
					"EmpID": emp_id,
					"EmpName": emp_name,
					"Department": department,
					"Date": date,
					"On-duty": on_duty if pd.notna(on_duty) else "",
					"Off-duty": off_duty if pd.notna(off_duty) else "",
					"Status": status,
				}
			)
			continue

		if str(on_duty).strip().lower() in ["on-duty", "off-duty"] or str(off_duty).strip().lower() in [
			"on-duty",
			"off-duty",
		]:
			continue

		on_duty_time = datetime.strptime(str(on_duty).strip(), "%H:%M").time()
		off_duty_time = datetime.strptime(str(off_duty).strip(), "%H:%M").time()

		work_hours = (
			datetime.combine(datetime.today(), off_duty_time)
			- datetime.combine(datetime.today(), on_duty_time)
		).total_seconds() / 3600

		if work_hours >= 8:
			status = "Present"
		elif 4 <= work_hours < 8:
			status = "Half Day"
		else:
			status = "Absent"

		records.append(
			{
				"EmpID": emp_id,
				"EmpName": emp_name,
				"Department": department,
				"Date": date,
				"On-duty": on_duty,
				"Off-duty": off_duty,
				"Status": status,
			}
		)

	return records
