# Copyright (c) 2026, MI_Cloud and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_data(report_filters):
	conditions, params = get_conditions(report_filters)

	# Actuals come from the raw materials consumed by the subcontractor
	# (Subcontracting Receipt Supplied Item); the BOM used sits on the receipt's FG line.
	rows = frappe.db.sql(
		f"""
		select
			sup.parent as name,
			scr.posting_date,
			scr.supplier,
			sup.main_item_code,
			sup.rm_item_code,
			sup.item_name,
			sup.required_qty,
			sup.consumed_qty,
			sup.rate as actual_rate,
			ri.bom as bom_no
		from `tabSubcontracting Receipt Supplied Item` sup
		inner join `tabSubcontracting Receipt` scr on scr.name = sup.parent
		left join `tabSubcontracting Receipt Item` ri on ri.name = sup.reference_name
		where {conditions}
		order by scr.posting_date, sup.parent, sup.idx
		""",
		params,
		as_dict=True,
	)

	if not rows:
		return []

	# Standard rate is the planned rate frozen in the BOM (the plan)
	standard_rates = get_standard_rates(rows)

	grouped = {}
	for d in rows:
		sq = d.required_qty or 0.0
		aq = d.consumed_qty or 0.0
		ar = d.actual_rate or 0.0

		sr = standard_rates.get((d.bom_no, d.rm_item_code))
		# No BOM standard available -> fall back to the actual rate so the rate
		# variance shows 0 instead of a misleading value.
		if sr is None:
			sr = ar

		d.standard_qty = sq
		d.actual_qty = aq
		d.standard_rate = sr
		d.actual_rate = ar
		d.standard_cost = sq * sr
		d.actual_cost = aq * ar

		# Material Quantity Variance = (SQ - AQ) x Standard Rate
		d.qty_variance = (sq - aq) * sr
		# Material Rate Variance = (Standard Rate - Actual Rate) x AQ
		d.rate_variance = (sr - ar) * aq
		d.total_variance = d.qty_variance + d.rate_variance

		grouped.setdefault((d.name, d.main_item_code), []).append(d)

	data = []
	for _key, group in grouped.items():
		for index, row in enumerate(group):
			if index != 0:
				# One receipt/FG has many raw materials: show parent data in the first row only
				for field in ["name", "posting_date", "supplier", "main_item_code"]:
					row[field] = ""
			data.append(row)

	return data


def get_standard_rates(rows):
	"""Standard price per unit for each raw material, taken from the BOM."""
	rates = {}
	bom_nos = list({d.bom_no for d in rows if d.bom_no})
	if not bom_nos:
		return rates

	bom_items = frappe.get_all(
		"BOM Item",
		filters={"parent": ("in", bom_nos)},
		fields=["parent", "item_code", "rate"],
	)

	for d in bom_items:
		rates[(d.parent, d.item_code)] = d.rate or 0.0

	return rates


def get_conditions(report_filters):
	conditions = ["scr.docstatus = 1", "scr.posting_date between %(from_date)s and %(to_date)s"]
	params = {
		"from_date": report_filters.get("from_date"),
		"to_date": report_filters.get("to_date"),
	}

	if report_filters.get("company"):
		conditions.append("scr.company = %(company)s")
		params["company"] = report_filters.get("company")

	if report_filters.get("name"):
		conditions.append("sup.parent = %(name)s")
		params["name"] = report_filters.get("name")

	if report_filters.get("supplier"):
		conditions.append("scr.supplier = %(supplier)s")
		params["supplier"] = report_filters.get("supplier")

	if report_filters.get("production_item"):
		conditions.append("sup.main_item_code = %(production_item)s")
		params["production_item"] = report_filters.get("production_item")

	return " and ".join(conditions), params


def get_columns():
	return [
		{
			"label": _("Subcontracting Receipt"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Subcontracting Receipt",
			"width": 160,
		},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 150,
		},
		{
			"label": _("Finished Good"),
			"fieldname": "main_item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150,
		},
		{
			"label": _("Raw Material"),
			"fieldname": "rm_item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150,
		},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
		{"label": _("Standard Qty"), "fieldname": "standard_qty", "fieldtype": "Float", "width": 120},
		{"label": _("Actual Qty"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 100},
		{
			"label": _("Standard Rate"),
			"fieldname": "standard_rate",
			"fieldtype": "Currency",
			"width": 120,
		},
		{"label": _("Actual Rate"), "fieldname": "actual_rate", "fieldtype": "Currency", "width": 120},
		{
			"label": _("Standard Cost"),
			"fieldname": "standard_cost",
			"fieldtype": "Currency",
			"width": 120,
		},
		{"label": _("Actual Cost"), "fieldname": "actual_cost", "fieldtype": "Currency", "width": 120},
		{
			"label": _("Material Qty Variance"),
			"fieldname": "qty_variance",
			"fieldtype": "Currency",
			"width": 170,
		},
		{
			"label": _("Material Rate Variance"),
			"fieldname": "rate_variance",
			"fieldtype": "Currency",
			"width": 180,
		},
		{
			"label": _("Total Material Variance"),
			"fieldname": "total_variance",
			"fieldtype": "Currency",
			"width": 180,
		},
	]
