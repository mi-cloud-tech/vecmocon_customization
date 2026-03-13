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
	columns = [
		{
			"label": _("Invoice"),
			"fieldname": "invoice",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 140,
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 150,
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Supplier GSTIN"),
			"fieldname": "supplier_gstin",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("GST Category"),
			"fieldname": "gst_category",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Place of Supply"),
			"fieldname": "place_of_supply",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Taxable Value"),
			"fieldname": "taxable_value",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("CGST"),
			"fieldname": "cgst_amount",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("SGST"),
			"fieldname": "sgst_amount",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("IGST"),
			"fieldname": "igst_amount",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("Cess"),
			"fieldname": "cess_amount",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("Total Tax"),
			"fieldname": "total_tax",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("Grand Total"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("ITC Classification"),
			"fieldname": "itc_classification",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Bill No"),
			"fieldname": "bill_no",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Bill Date"),
			"fieldname": "bill_date",
			"fieldtype": "Date",
			"width": 100,
		},
	]

	return columns


def get_data(filters):
	conditions = get_conditions(filters)

	# Get Purchase Invoices with Reverse Charge
	invoices = frappe.db.sql(
		"""
		SELECT
			pi.name as invoice,
			pi.posting_date,
			pi.supplier,
			pi.supplier_name,
			pi.supplier_gstin,
			pi.gst_category,
			pi.place_of_supply,
			pi.base_net_total as taxable_value,
			pi.base_total_taxes_and_charges as total_tax,
			pi.base_grand_total as grand_total,
			pi.itc_classification,
			pi.bill_no,
			pi.bill_date,
			pi.company
		FROM `tabPurchase Invoice` pi
		WHERE pi.docstatus = 1
			AND pi.is_reverse_charge = 1
			{conditions}
		ORDER BY pi.posting_date DESC, pi.name DESC
	""".format(
			conditions=conditions
		),
		filters,
		as_dict=1,
	)

	# Get tax breakup for each invoice
	invoice_names = [d.invoice for d in invoices]

	if invoice_names:
		tax_details = get_tax_details(invoice_names)

		for invoice in invoices:
			taxes = tax_details.get(invoice.invoice, {})
			invoice.cgst_amount = taxes.get("cgst", 0)
			invoice.sgst_amount = taxes.get("sgst", 0)
			invoice.igst_amount = taxes.get("igst", 0)
			invoice.cess_amount = taxes.get("cess", 0)

	return invoices


def get_tax_details(invoice_names):
	"""Get CGST, SGST, IGST, Cess breakup for invoices"""
	tax_data = frappe.db.sql(
		"""
		SELECT
			parent,
			account_head,
			base_tax_amount_after_discount_amount as tax_amount
		FROM `tabPurchase Taxes and Charges`
		WHERE parent IN %(invoice_names)s
			AND charge_type != 'Actual'
	""",
		{"invoice_names": invoice_names},
		as_dict=1,
	)

	tax_details = {}

	for tax in tax_data:
		if tax.parent not in tax_details:
			tax_details[tax.parent] = {"cgst": 0, "sgst": 0, "igst": 0, "cess": 0}

		account_head_lower = (tax.account_head or "").lower()

		if "cgst" in account_head_lower:
			tax_details[tax.parent]["cgst"] += flt(tax.tax_amount)
		elif "sgst" in account_head_lower or "utgst" in account_head_lower:
			tax_details[tax.parent]["sgst"] += flt(tax.tax_amount)
		elif "igst" in account_head_lower:
			tax_details[tax.parent]["igst"] += flt(tax.tax_amount)
		elif "cess" in account_head_lower:
			tax_details[tax.parent]["cess"] += flt(tax.tax_amount)

	return tax_details


def get_conditions(filters):
	conditions = []

	if filters.get("company"):
		conditions.append("pi.company = %(company)s")

	if filters.get("from_date"):
		conditions.append("pi.posting_date >= %(from_date)s")

	if filters.get("to_date"):
		conditions.append("pi.posting_date <= %(to_date)s")

	if filters.get("supplier"):
		conditions.append("pi.supplier in %(supplier)s")

	if filters.get("gst_category"):
		conditions.append("pi.gst_category = %(gst_category)s")

	if filters.get("place_of_supply"):
		conditions.append("pi.place_of_supply = %(place_of_supply)s")

	return " AND " + " AND ".join(conditions) if conditions else ""


def get_report_summary(data):
	if not data:
		return []

	total_taxable_value = sum(flt(d.get("taxable_value")) for d in data)
	total_cgst = sum(flt(d.get("cgst_amount")) for d in data)
	total_sgst = sum(flt(d.get("sgst_amount")) for d in data)
	total_igst = sum(flt(d.get("igst_amount")) for d in data)
	total_cess = sum(flt(d.get("cess_amount")) for d in data)
	total_tax = sum(flt(d.get("total_tax")) for d in data)
	total_grand = sum(flt(d.get("grand_total")) for d in data)

	return [
		{
			"value": len(data),
			"label": _("Total Invoices"),
			"datatype": "Int",
			"indicator": "blue",
		},
		{
			"value": total_taxable_value,
			"label": _("Total Taxable Value"),
			"datatype": "Currency",
			"indicator": "green",
		},
		{
			"value": total_cgst,
			"label": _("Total CGST"),
			"datatype": "Currency",
			"indicator": "orange",
		},
		{
			"value": total_sgst,
			"label": _("Total SGST"),
			"datatype": "Currency",
			"indicator": "orange",
		},
		{
			"value": total_igst,
			"label": _("Total IGST"),
			"datatype": "Currency",
			"indicator": "orange",
		},
		{
			"value": total_cess,
			"label": _("Total Cess"),
			"datatype": "Currency",
			"indicator": "grey",
		},
		{
			"value": total_tax,
			"label": _("Total Tax (RCM)"),
			"datatype": "Currency",
			"indicator": "red",
		},
		{
			"value": total_grand,
			"label": _("Grand Total"),
			"datatype": "Currency",
			"indicator": "blue",
		},
	]


def get_chart_data(data):
	if not data:
		return None

	# Group by month for chart
	monthly_data = {}

	for row in data:
		month_key = row.posting_date.strftime("%Y-%m") if row.posting_date else "Unknown"
		if month_key not in monthly_data:
			monthly_data[month_key] = {"taxable_value": 0, "total_tax": 0}

		monthly_data[month_key]["taxable_value"] += flt(row.get("taxable_value"))
		monthly_data[month_key]["total_tax"] += flt(row.get("total_tax"))

	# Sort by month
	sorted_months = sorted(monthly_data.keys())

	return {
		"data": {
			"labels": sorted_months,
			"datasets": [
				{
					"name": _("Taxable Value"),
					"values": [monthly_data[m]["taxable_value"] for m in sorted_months],
				},
				{
					"name": _("RCM Tax"),
					"values": [monthly_data[m]["total_tax"] for m in sorted_months],
				},
			],
		},
		"type": "bar",
		"colors": ["#7cd6fd", "#ff5858"],
		"barOptions": {"stacked": False},
	}