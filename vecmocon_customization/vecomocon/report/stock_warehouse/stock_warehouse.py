# Copyright (c) 2026, MI_Cloud and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt


def execute(filters=None):
	filters = frappe._dict(filters or {})

	if not filters.get("company"):
		frappe.throw(_("Please select a Company."))

	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 130},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 160},
		{"label": _("Item Description"), "fieldname": "description", "fieldtype": "Data", "width": 200},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 180,
		},
		{"label": _("Available Qty"), "fieldname": "available_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Reserved Qty"), "fieldname": "reserved_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Quality Hold Qty"), "fieldname": "hold_qty", "fieldtype": "Float", "width": 120},
		{"label": _("Quality Rejected Qty"), "fieldname": "rejected_qty", "fieldtype": "Float", "width": 130},
		{"label": _("Total Stock"), "fieldname": "total_qty", "fieldtype": "Float", "width": 110},
		{
			"label": _("Unit Cost"),
			"fieldname": "valuation_rate",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 110,
		},
		{
			"label": _("Value"),
			"fieldname": "stock_value",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
	]


def get_data(filters):
	conditions = ["w.company = %(company)s"]

	if not cint(filters.get("show_zero_stock")):
		conditions.append("b.actual_qty != 0")
	if filters.get("warehouse"):
		conditions.append("b.warehouse = %(warehouse)s")
	if filters.get("item_code"):
		conditions.append("b.item_code = %(item_code)s")
	if filters.get("item_group"):
		conditions.append("i.item_group = %(item_group)s")
	if filters.get("brand"):
		conditions.append("i.brand = %(brand)s")

	where_clause = " AND ".join(conditions)

	default_currency = frappe.get_cached_value("Company", filters.get("company"), "default_currency")

	rows = frappe.db.sql(
		"""
		SELECT
			b.item_code,
			i.item_name,
			i.description,
			b.warehouse,
			b.actual_qty,
			b.reserved_qty,
			b.valuation_rate,
			b.stock_value,
			IFNULL(w.custom_is_quality_warehouse, 0) AS is_quality,
			IFNULL(w.is_rejected_warehouse, 0) AS is_rejected
		FROM `tabBin` b
		INNER JOIN `tabItem` i ON i.name = b.item_code
		INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
		WHERE {where_clause}
		ORDER BY b.item_code, b.warehouse
		""".format(where_clause=where_clause),
		filters,
		as_dict=True,
	)

	data = []
	for r in rows:
		actual = flt(r.actual_qty)

		# The warehouse's classification routes the whole on-hand qty into exactly
		# one bucket, so Available + Hold + Rejected always equals Total Stock.
		hold_qty = actual if r.is_quality else 0.0
		rejected_qty = actual if (r.is_rejected and not r.is_quality) else 0.0
		available_qty = actual if not (r.is_quality or r.is_rejected) else 0.0

		data.append(
			{
				"item_code": r.item_code,
				"item_name": r.item_name,
				"description": r.description,
				"warehouse": r.warehouse,
				"available_qty": available_qty,
				"reserved_qty": flt(r.reserved_qty),
				"hold_qty": hold_qty,
				"rejected_qty": rejected_qty,
				"total_qty": actual,
				"valuation_rate": flt(r.valuation_rate),
				"stock_value": flt(r.stock_value),
				"currency": default_currency,
			}
		)

	return data
