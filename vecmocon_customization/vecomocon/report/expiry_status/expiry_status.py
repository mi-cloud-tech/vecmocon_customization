# Copyright (c) 2026, MI_Cloud and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, date_diff, flt, getdate, nowdate

from erpnext.stock.report.batch_wise_balance_history.batch_wise_balance_history import (
	get_item_warehouse_batch_map,
)

# A date far enough in the past that every Stock Ledger Entry falls after it, so
# the wrapped balance map returns the true on-hand qty as of the "as on" date.
OPENING_FROM_DATE = "1900-01-01"


def execute(filters=None):
	filters = frappe._dict(filters or {})

	if not filters.get("company"):
		frappe.throw(_("Please select a Company."))

	as_on_date = getdate(filters.get("as_on_date") or nowdate())
	today = getdate(nowdate())

	columns = get_columns()
	data = get_data(filters, as_on_date, today)
	return columns, data


def get_columns():
	return [
		{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 130},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 160},
		{"label": _("Item Description"), "fieldname": "description", "fieldtype": "Data", "width": 220},
		{"label": _("Batch"), "fieldname": "batch", "fieldtype": "Link", "options": "Batch", "width": 140},
		{"label": _("Mfg Date"), "fieldname": "manufacturing_date", "fieldtype": "Date", "width": 100},
		{"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Remaining Shelf Life (Days)"),
			"fieldname": "remaining_shelf_life",
			"fieldtype": "Int",
			"width": 180,
		},
		{"label": _("Expiry Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": _("Stock Qty"), "fieldname": "stock_qty", "fieldtype": "Float", "width": 100},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 180,
		},
	]


def get_data(filters, as_on_date, today):
	float_precision = cint(frappe.db.get_default("float_precision")) or 3

	# Reuse the standard Batch-Wise Balance History balance map. It handles both
	# legacy SLE.batch_no rows and Serial & Batch Bundle rows transparently.
	map_filters = frappe._dict(filters)
	map_filters.from_date = OPENING_FROM_DATE
	# Pass dates as strings: the batch-bundle helper concatenates to_date with a
	# time string ("... 23:59:59"), which fails on a date object.
	map_filters.to_date = str(as_on_date)
	iwb_map = get_item_warehouse_batch_map(map_filters, float_precision)

	item_map = get_item_details()
	batch_map = get_batch_details(filters)
	allowed_items = get_allowed_items(filters)

	show_zero = cint(filters.get("show_zero_stock"))
	status_filter = filters.get("expiry_status")
	expiring_within = cint(filters.get("expiring_within"))

	data = []
	for item_code in iwb_map:
		if allowed_items is not None and item_code not in allowed_items:
			continue

		item = item_map.get(item_code, {})
		for warehouse in iwb_map[item_code]:
			for batch in iwb_map[item_code][warehouse]:
				qty = flt(iwb_map[item_code][warehouse][batch].bal_qty, float_precision)
				if not show_zero and qty <= 0:
					continue

				batch_info = batch_map.get(batch, {})
				expiry_date = batch_info.get("expiry_date")
				remaining = date_diff(expiry_date, today) if expiry_date else None
				status = get_status(remaining)

				if status_filter and status_filter != "All" and status != status_filter:
					continue
				if (
					expiring_within
					and remaining is not None
					and not (0 <= remaining <= expiring_within)
				):
					continue

				data.append(
					{
						"item_code": item_code,
						"item_name": item.get("item_name"),
						"description": item.get("description"),
						"batch": batch,
						"manufacturing_date": batch_info.get("manufacturing_date"),
						"expiry_date": expiry_date,
						"remaining_shelf_life": remaining,
						"status": status,
						"stock_qty": qty,
						"warehouse": warehouse,
					}
				)

	# Soonest-to-expire first; batches without an expiry date sink to the bottom.
	data.sort(key=lambda r: (r["expiry_date"] is None, r["expiry_date"] or getdate("9999-12-31")))
	return data


def get_status(remaining):
	if remaining is None:
		return "No Expiry"
	if remaining < 0:
		return "Expired"
	if remaining == 0:
		return "Expires Today"
	return "Valid"


def get_item_details():
	item_map = {}
	for d in frappe.get_all(
		"Item", fields=["name", "item_name", "description"], filters={"has_batch_no": 1}
	):
		item_map[d.name] = d
	return item_map


def get_batch_details(filters):
	batch_filters = {}
	if filters.get("batch_no"):
		batch_filters["name"] = filters.get("batch_no")

	batch_map = {}
	for d in frappe.get_all(
		"Batch",
		fields=["name", "manufacturing_date", "expiry_date"],
		filters=batch_filters,
	):
		batch_map[d.name] = d
	return batch_map


def get_allowed_items(filters):
	"""Resolve Item Group / Brand filters to an item-code set, or None if neither set."""
	item_filters = {}
	if filters.get("item_group"):
		item_filters["item_group"] = filters.get("item_group")
	if filters.get("brand"):
		item_filters["brand"] = filters.get("brand")

	if not item_filters:
		return None
	return set(frappe.get_all("Item", filters=item_filters, pluck="name"))
