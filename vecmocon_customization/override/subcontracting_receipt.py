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

	changed = False
	for row in doc.supplied_items:
		key = (row.rm_item_code, row.reference_name)
		if key in manual_qtys:
			row.consumed_qty = flt(manual_qtys[key], row.precision("consumed_qty"))
			changed = True

	if changed:
		# Let ERPNext recompute everything downstream from the restored consumed_qty:
		# per-row amount, items' rm_supp_cost / rm_cost_per_qty / rate / amount,
		# additional_cost_per_qty (when distributed by Amount), and parent total / total_qty.
		doc.calculate_additional_costs()
		doc.calculate_items_qty_and_amount()

	del doc._manual_consumed_qtys
