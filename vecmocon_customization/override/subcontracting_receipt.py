# Copyright (c) 2025, MI_Cloud and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def before_validate(doc, method):
	"""Capture user-entered consumed_qty before ERPNext recalculates from BOM."""
	if not frappe.db.get_single_value("Vecmocon Settings", "allow_manual_consumed_qty_edit"):
		return

	if not doc.supplied_items:
		return

	manual_qtys = {}
	for row in doc.supplied_items:
		if row.consumed_qty:
			key = (row.rm_item_code, row.reference_name)
			manual_qtys[key] = row.consumed_qty

	if manual_qtys:
		doc._manual_consumed_qtys = manual_qtys


def validate(doc, method):
	"""Restore user-entered consumed_qty after ERPNext has recalculated it."""
	manual_qtys = getattr(doc, "_manual_consumed_qtys", None)
	if not manual_qtys:
		return

	for row in doc.supplied_items:
		key = (row.rm_item_code, row.reference_name)
		if key in manual_qtys:
			row.consumed_qty = flt(manual_qtys[key], row.precision("consumed_qty"))
			row.amount = flt(row.consumed_qty * row.rate, row.precision("amount"))

	# Recalculate rm_supp_cost on parent items
	rm_cost_map = {}
	for row in doc.supplied_items:
		rm_cost_map.setdefault(row.reference_name, 0)
		rm_cost_map[row.reference_name] += flt(row.amount)

	for item in doc.items:
		if not item.is_scrap_item and item.name in rm_cost_map and item.qty:
			item.rm_supp_cost = rm_cost_map[item.name]
			item.rm_cost_per_qty = item.rm_supp_cost / item.qty
			item.rate = (
				flt(item.rm_cost_per_qty)
				+ flt(item.service_cost_per_qty)
				+ flt(item.additional_cost_per_qty)
				- flt(item.scrap_cost_per_qty)
			)
			item.amount = flt(item.qty) * flt(item.rate)

	del doc._manual_consumed_qtys
