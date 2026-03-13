# Copyright (c) 2026, MI_Cloud and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, date_diff, add_days, getdate


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	return [
		{
			"label": "Purchase Receipt Date",
			"fieldname": "grn_date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": "Date",
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": "Ref No",
			"fieldname": "invoice_no",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 150
		},
		{
			"label": "Party Name",
			"fieldname": "supplier",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": "MSME Number",
			"fieldname": "custom_msme_no",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": "MSME Category",
			"fieldname": "custom_msme_category",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": "PAN No",
			"fieldname": "pan_no",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": "Pending Amount",
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"label": "MSME Due Date",
			"fieldname": "msme_due_date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": "Overdue Days",
			"fieldname": "overdue_days",
			"fieldtype": "Int",
			"width": 120
		}
	]

def get_data(filters):
	today_date = getdate(today())
	conditions = ""

	if filters.get("supplier"):
		conditions += " AND pi.supplier IN %(supplier)s"
		filters["supplier"] = tuple(filters["supplier"])

	query = f"""
		SELECT
			pi.custom_purchase_receipt_date as grn_date,
			pi.posting_date,
			pi.name AS invoice_no,
			pi.supplier,
			sup.pan AS pan_no,
			pi.outstanding_amount,
			pi.due_date,
			sup.custom_msme_no,
			sup.custom_msme_category
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabSupplier` sup
			ON sup.name = pi.supplier
		WHERE
			pi.docstatus = 1
			AND pi.outstanding_amount > 0
			AND sup.custom_msme_no IS NOT NULL
			AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
			{conditions}
	"""
	invoices = frappe.db.sql(query, filters, as_dict=True)
	data = []
	for inv in invoices:
		msme_due_date = add_days(inv.grn_date, 45)
		if today_date > msme_due_date:
			overdue_days = date_diff(today_date, msme_due_date)
		else:
			overdue_days = 0

		row = {
			"grn_date": inv.grn_date,
			"posting_date": inv.posting_date,
			"invoice_no": inv.invoice_no,
			"custom_msme_no": inv.custom_msme_no,
			"custom_msme_category": inv.custom_msme_category,
			"supplier": inv.supplier,
			"pan_no": inv.pan_no,
			"outstanding_amount": inv.outstanding_amount,
			"msme_due_date": msme_due_date,
			"overdue_days": overdue_days
		}
		data.append(row)

	return data
