# Copyright (c) 2026, MI_Cloud and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	report_summary = get_report_summary(data)
	chart = get_chart_data(data)

	return columns, data, None, chart, report_summary


def get_columns(filters):
	return [
		{
			"label": _("Challan Number"),
			"fieldname": "challan_no",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Challan Date"),
			"fieldname": "challan_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 150,
		},
		{
			"label": _("Payment Entry"),
			"fieldname": "payment_entry",
			"fieldtype": "Link",
			"options": "Payment Entry",
			"width": 160,
		},
		{
			"label": _("Purchase Invoice"),
			"fieldname": "purchase_invoice",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 160,
		},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 140,
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Invoice Amount"),
			"fieldname": "invoice_amount",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("TDS Category"),
			"fieldname": "tds_category",
			"fieldtype": "Link",
			"options": "Tax Withholding Category",
			"width": 180,
		},
		{
			"label": _("TDS Rate (%)"),
			"fieldname": "tds_rate",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("TDS Amount"),
			"fieldname": "tds_amount",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("BSR Code"),
			"fieldname": "bsr_code",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Bank Name"),
			"fieldname": "bank_name",
			"fieldtype": "Data",
			"width": 130,
		},
	]


def get_data(filters):
	conditions = get_conditions(filters)

	data = frappe.db.sql(
		"""
		SELECT
			tc.name as tds_challan,
			tc.challan_no,
			tc.challan_date,
			tc.status,
			tc.company,
			tc.payment_entry,
			tc.bsr_code,
			tc.bank_name,
			tc.total_tds_amount,
			tci.purchase_invoice,
			tci.supplier,
			tci.supplier_name,
			tci.invoice_amount,
			tci.tds_category,
			tci.tds_rate,
			tci.tds_amount
		FROM `tabTDS Challan` tc
		INNER JOIN `tabTDS Challan Item` tci ON tci.parent = tc.name
		WHERE tc.docstatus = 1
			{conditions}
		ORDER BY tc.challan_date DESC, tc.name DESC
	""".format(
			conditions=conditions
		),
		filters,
		as_dict=1,
	)

	return data


def get_conditions(filters):
	conditions = []

	if filters.get("company"):
		conditions.append("tc.company = %(company)s")

	if filters.get("from_date"):
		conditions.append("tc.challan_date >= %(from_date)s")

	if filters.get("to_date"):
		conditions.append("tc.challan_date <= %(to_date)s")

	if filters.get("status"):
		conditions.append("tc.status = %(status)s")

	if filters.get("supplier"):
		conditions.append("tci.supplier = %(supplier)s")

	if filters.get("payment_entry"):
		conditions.append("tc.payment_entry = %(payment_entry)s")

	if filters.get("tax_withholding_category"):
		conditions.append("tci.tds_category = %(tax_withholding_category)s")

	return " AND " + " AND ".join(conditions) if conditions else ""


def get_report_summary(data):
	if not data:
		return []

	total_tds = sum(flt(d.get("tds_amount")) for d in data)
	total_invoice = sum(flt(d.get("invoice_amount")) for d in data)

	# Count unique challans
	unique_challans = len(set(d.get("tds_challan") for d in data))

	paid_challans = len(
		set(d.get("tds_challan") for d in data if d.get("status") == "Paid")
	)
	unpaid_challans = unique_challans - paid_challans

	return [
		{
			"value": unique_challans,
			"label": _("Total Challans"),
			"datatype": "Int",
			"indicator": "blue",
		},
		{
			"value": paid_challans,
			"label": _("Paid Challans"),
			"datatype": "Int",
			"indicator": "green",
		},
		{
			"value": unpaid_challans,
			"label": _("Unpaid Challans"),
			"datatype": "Int",
			"indicator": "red",
		},
		{
			"value": total_invoice,
			"label": _("Total Invoice Amount"),
			"datatype": "Currency",
			"indicator": "blue",
		},
		{
			"value": total_tds,
			"label": _("Total TDS Amount"),
			"datatype": "Currency",
			"indicator": "orange",
		},
	]


def get_chart_data(data):
	if not data:
		return None

	# Group by month
	monthly_data = {}
	for row in data:
		if row.challan_date:
			month_key = row.challan_date.strftime("%Y-%m")
		else:
			month_key = "Unknown"

		if month_key not in monthly_data:
			monthly_data[month_key] = {"paid": 0, "unpaid": 0}

		if row.status == "Paid":
			monthly_data[month_key]["paid"] += flt(row.tds_amount)
		else:
			monthly_data[month_key]["unpaid"] += flt(row.tds_amount)

	sorted_months = sorted(monthly_data.keys())

	return {
		"data": {
			"labels": sorted_months,
			"datasets": [
				{
					"name": _("Paid TDS"),
					"values": [monthly_data[m]["paid"] for m in sorted_months],
				},
				{
					"name": _("Unpaid TDS"),
					"values": [monthly_data[m]["unpaid"] for m in sorted_months],
				},
			],
		},
		"type": "bar",
		"colors": ["#28a745", "#dc3545"],
		"barOptions": {"stacked": True},
	}
