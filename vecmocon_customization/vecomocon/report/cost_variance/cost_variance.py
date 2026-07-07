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

	# Anchor: the raw materials required per Subcontracting Order (BOM standard,
	# materialised on the order). Each row is one raw material for one order.
	rows = frappe.db.sql(
		f"""
		select
			sco.name as subcontracting_order,
			sco.supplier,
			sco_item.bom as bom_no,
			sup.main_item_code,
			sup.rm_item_code,
			sup.rm_item_code as item_name,
			sup.required_qty
		from `tabSubcontracting Order Supplied Item` sup
		inner join `tabSubcontracting Order` sco on sco.name = sup.parent
		left join `tabSubcontracting Order Item` sco_item
			on sco_item.parent = sco.name and sco_item.item_code = sup.main_item_code
		where {conditions}
		order by sco.transaction_date, sco.name, sup.idx
		""",
		params,
		as_dict=True,
	)

	if not rows:
		return []

	bom_rates = get_bom_rates(rows)  # (bom, rm) -> standard price from BOM
	sent = get_sent(rows)  # (order, rm) -> qty sent + basic_rate from Send-to-Subcontractor SE
	consumed = get_consumed(rows)  # (order, rm) -> consumed qty + rate from Subcontracting Receipt

	data = []
	for d in rows:
		# Standard (from BOM)
		sq = d.required_qty or 0.0
		sp = bom_rates.get((d.bom_no, d.rm_item_code), 0.0)

		# Actual issued (from Send-to-Subcontractor Stock Entry)
		s = sent.get((d.subcontracting_order, d.rm_item_code)) or {}
		qty_sent = s.get("qty", 0.0)
		se_rate = s.get("rate", 0.0)  # basic_rate
		d.stock_entry = s.get("docs", "")

		# Actual consumed (from Subcontracting Receipt)
		c = consumed.get((d.subcontracting_order, d.rm_item_code)) or {}
		consumed_qty = c.get("qty", 0.0)
		scr_rate = c.get("rate", 0.0)
		d.subcontracting_receipt = c.get("docs", "")

		d.standard_qty = sq
		d.standard_price = sp
		d.actual_qty_sent = qty_sent
		d.se_rate = se_rate
		d.consumed_qty = consumed_qty
		d.actual_price = scr_rate

		# Direct Material Quantity Variance
		#   = (Standard Qty[BOM] - Actual Qty[Stock Entry]) x Standard Price[BOM]
		d.qty_variance = (sq - qty_sent) * sp

		# Direct Material Price Variance
		#   = (Stock Entry basic_rate - Receipt rate) x Stock Entry basic_rate
		d.price_variance = (se_rate - scr_rate) * se_rate

		# Direct Material Variance
		#   = Standard Qty[BOM] x Standard Price[BOM] - Consumed Qty[Receipt] x Actual Price[Receipt]
		d.material_variance = (sq * sp) - (consumed_qty * scr_rate)

		data.append(d)

	return data


def get_bom_rates(rows):
	"""Standard price per raw material, from the BOM on the order's FG line."""
	rates = {}
	boms = list({d.bom_no for d in rows if d.bom_no})
	if not boms:
		return rates

	for b in frappe.get_all(
		"BOM Item", filters={"parent": ("in", boms)}, fields=["parent", "item_code", "rate"]
	):
		rates[(b.parent, b.item_code)] = b.rate or 0.0

	return rates


def get_sent(rows):
	"""Qty sent + qty-weighted basic_rate per (order, rm) from Send-to-Subcontractor Stock Entries."""
	result = {}
	orders = list({d.subcontracting_order for d in rows if d.subcontracting_order})
	if not orders:
		return result

	se_rows = frappe.db.sql(
		"""
		select
			se.subcontracting_order,
			sed.item_code,
			sum(sed.qty) as qty,
			sum(sed.basic_rate * sed.qty) as amount,
			avg(sed.basic_rate) as avg_rate,
			group_concat(distinct se.name) as docs
		from `tabStock Entry` se
		inner join `tabStock Entry Detail` sed on sed.parent = se.name
		where se.purpose = 'Send to Subcontractor'
			and se.docstatus = 1
			and se.subcontracting_order in %(orders)s
		group by se.subcontracting_order, sed.item_code
		""",
		{"orders": orders},
		as_dict=True,
	)

	for r in se_rows:
		qty = r.qty or 0.0
		rate = (r.amount / qty) if qty else (r.avg_rate or 0.0)
		result[(r.subcontracting_order, r.item_code)] = {"qty": qty, "rate": rate, "docs": r.docs or ""}

	return result


def get_consumed(rows):
	"""Consumed qty + qty-weighted rate per (order, rm) from Subcontracting Receipts."""
	result = {}
	orders = list({d.subcontracting_order for d in rows if d.subcontracting_order})
	if not orders:
		return result

	scr_rows = frappe.db.sql(
		"""
		select
			sup.subcontracting_order,
			sup.rm_item_code,
			sum(sup.consumed_qty) as qty,
			sum(sup.rate * sup.consumed_qty) as amount,
			avg(sup.rate) as avg_rate,
			group_concat(distinct sup.parent) as docs
		from `tabSubcontracting Receipt Supplied Item` sup
		inner join `tabSubcontracting Receipt` scr on scr.name = sup.parent
		where scr.docstatus = 1
			and sup.subcontracting_order in %(orders)s
		group by sup.subcontracting_order, sup.rm_item_code
		""",
		{"orders": orders},
		as_dict=True,
	)

	for r in scr_rows:
		qty = r.qty or 0.0
		rate = (r.amount / qty) if qty else (r.avg_rate or 0.0)
		result[(r.subcontracting_order, r.rm_item_code)] = {
			"qty": qty,
			"rate": rate,
			"docs": r.docs or "",
		}

	return result


def get_conditions(report_filters):
	conditions = [
		"sco.docstatus = 1",
		"sco.transaction_date between %(from_date)s and %(to_date)s",
	]
	params = {
		"from_date": report_filters.get("from_date"),
		"to_date": report_filters.get("to_date"),
	}

	if report_filters.get("company"):
		conditions.append("sco.company = %(company)s")
		params["company"] = report_filters.get("company")

	if report_filters.get("name"):
		conditions.append("sco.name = %(name)s")
		params["name"] = report_filters.get("name")

	if report_filters.get("supplier"):
		conditions.append("sco.supplier = %(supplier)s")
		params["supplier"] = report_filters.get("supplier")

	if report_filters.get("production_item"):
		conditions.append("sup.main_item_code = %(production_item)s")
		params["production_item"] = report_filters.get("production_item")

	if report_filters.get("bom"):
		conditions.append("sco_item.bom = %(bom)s")
		params["bom"] = report_filters.get("bom")

	return " and ".join(conditions), params


def get_columns():
	return [
		{
			"label": _("Subcontracting Order"),
			"fieldname": "subcontracting_order",
			"fieldtype": "Link",
			"options": "Subcontracting Order",
			"width": 160,
		},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 130,
		},
		{
			"label": _("Finished Good"),
			"fieldname": "main_item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 130,
		},
		{
			"label": _("Raw Material"),
			"fieldname": "rm_item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 140,
		},
		{
			"label": _("BOM"),
			"fieldname": "bom_no",
			"fieldtype": "Link",
			"options": "BOM",
			"width": 160,
		},
		{"label": _("Standard Qty"), "fieldname": "standard_qty", "fieldtype": "Float", "width": 130},
		{
			"label": _("Standard Price"),
			"fieldname": "standard_price",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Stock Entry"),
			"fieldname": "stock_entry",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Actual Qty (Sent)"),
			"fieldname": "actual_qty_sent",
			"fieldtype": "Float",
			"width": 140,
		},
		{
			"label": _("SE Rate"),
			"fieldname": "se_rate",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("Subcontracting Receipt"),
			"fieldname": "subcontracting_receipt",
			"fieldtype": "Data",
			"width": 180,
		},
		{"label": _("Consumed Qty"), "fieldname": "consumed_qty", "fieldtype": "Float", "width": 140},
		{
			"label": _("Actual Price"),
			"fieldname": "actual_price",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Material Qty Variance"),
			"fieldname": "qty_variance",
			"fieldtype": "Currency",
			"width": 170,
		},
		{
			"label": _("Material Price Variance"),
			"fieldname": "price_variance",
			"fieldtype": "Currency",
			"width": 180,
		},
		{
			"label": _("Direct Material Variance"),
			"fieldname": "material_variance",
			"fieldtype": "Currency",
			"width": 190,
		},
	]
