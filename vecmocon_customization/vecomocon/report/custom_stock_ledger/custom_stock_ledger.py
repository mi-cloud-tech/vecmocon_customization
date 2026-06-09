# Copyright (c) 2026, MI_Cloud and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from erpnext.stock.report.stock_ledger.stock_ledger import execute as standard_sl_execute

# ---------------------------------------------------------------------------
# Configurable field sources (change these if/when custom fields are created)
# ---------------------------------------------------------------------------
# Item field shown in the "VPN" column. Falls back to the Item Code when blank.
VPN_ITEM_FIELD = "default_manufacturer_part_no"

# Header field on the voucher that holds the party (first match wins).
# Display names are preferred over link codes so the report is readable.
PARTY_FIELDS = ("supplier_name", "customer_name", "supplier", "customer")
# Header fields on the voucher that point to a source/related document.
RELATED_HEADER_FIELDS = (
	"work_order",
	"outgoing_stock_entry",
	"purchase_order",
	"sales_order",
	"delivery_note",
	"against_stock_entry",
)
# Child-table source documents (voucher_type -> (child doctype, source field)).
RELATED_CHILD_SOURCES = {
	"Purchase Receipt": ("Purchase Receipt Item", "purchase_order"),
	"Purchase Invoice": ("Purchase Invoice Item", "purchase_order"),
	"Delivery Note": ("Delivery Note Item", "against_sales_order"),
	"Sales Invoice": ("Sales Invoice Item", "sales_order"),
}


def execute(filters=None):
	if not filters:
		return [], []

	filters = frappe._dict(filters)
	# The standard report builds its columns using this filter; default it so
	# the wrapped report works even though we replace the columns afterwards.
	filters.setdefault("valuation_field_type", "Currency")

	# Run the standard Stock Ledger to get opening balance, running balance
	# quantity, and item details (description, item group, UOM) for free.
	_standard_columns, data = standard_sl_execute(filters)

	columns = get_columns()

	if not data:
		return columns, data

	enrich_rows(data)
	append_balance_row(data)

	return columns, data


def get_columns():
	return [
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": _("Transaction Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 140},
		{
			"label": _("Document No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 150,
		},
		{
			"label": _("Supplier/Customer/EMS"),
			"fieldname": "party",
			"fieldtype": "Data",
			"width": 170,
		},
		{"label": _("VPN"), "fieldname": "vpn", "fieldtype": "Data", "width": 120},
		{"label": _("Part Description"), "fieldname": "description", "fieldtype": "Data", "width": 220},
		{
			"label": _("Category"),
			"fieldname": "item_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 120,
		},
		{
			"label": _("UOM"),
			"fieldname": "stock_uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 70,
		},
		{"label": _("Qty"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 90},
		{
			"label": _("Unit Rate"),
			"fieldname": "unit_rate",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 110,
		},
		{"label": _("Related Document"), "fieldname": "related_document", "fieldtype": "Data", "width": 150},
		{
			"label": _("Location"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 160,
		},
		{"label": _("Item Type"), "fieldname": "item_type", "fieldtype": "Data", "width": 120},
	]


def enrich_rows(data):
	"""Add the spreadsheet-specific fields to each Stock Ledger row."""
	item_codes = set()
	voucher_keys = set()
	for row in data:
		item_code = row.get("item_code")
		# Skip the synthetic 'Opening' row (item_code is wrapped in quotes).
		if item_code and not str(item_code).startswith("'"):
			item_codes.add(item_code)
		voucher_type = row.get("voucher_type")
		voucher_no = row.get("voucher_no")
		if voucher_type and voucher_no:
			voucher_keys.add((voucher_type, voucher_no))

	item_info = get_item_info(item_codes)
	voucher_info = get_voucher_info(voucher_keys)

	# Item Type = the parent Item Group of the item's Item Group.
	item_groups = {row.get("item_group") for row in data if row.get("item_group")}
	group_parents = get_item_group_parents(item_groups)

	sr_no = 0
	for row in data:
		voucher_type = row.get("voucher_type")
		voucher_no = row.get("voucher_no")

		if voucher_type and voucher_no:
			sr_no += 1
			row["sr_no"] = sr_no

		info = item_info.get(row.get("item_code"), {})
		row["vpn"] = info.get("vpn", "")
		row["item_type"] = group_parents.get(row.get("item_group"), "")

		v_info = voucher_info.get((voucher_type, voucher_no), {})
		row["party"] = v_info.get("party", "")
		row["related_document"] = v_info.get("related_document", "")

		# Unit rate: use incoming rate for inflows, fall back to valuation rate.
		row["unit_rate"] = row.get("incoming_rate") or row.get("valuation_rate") or 0


def append_balance_row(data):
	"""Append a closing 'Balance Qty' row showing the net of the Qty column."""
	total_qty = sum(
		(row.get("actual_qty") or 0)
		for row in data
		if row.get("voucher_type") and row.get("voucher_no")
	)
	data.append(
		{
			"stock_uom": _("Balance Qty"),
			"actual_qty": total_qty,
			"unit_rate": "",
			"is_balance_row": 1,
		}
	)


def get_item_info(item_codes):
	"""Return {item_code: {"vpn": ...}} for the given items."""
	if not item_codes:
		return {}

	meta = frappe.get_meta("Item")
	fields = ["name"]

	vpn_field = VPN_ITEM_FIELD if VPN_ITEM_FIELD and meta.has_field(VPN_ITEM_FIELD) else None
	if vpn_field:
		fields.append(vpn_field)

	rows = frappe.db.get_all("Item", filters={"name": ("in", list(item_codes))}, fields=fields)

	info = {}
	for r in rows:
		vpn = (r.get(vpn_field) if vpn_field else "") or r["name"]
		info[r["name"]] = {"vpn": vpn}
	return info


def get_item_group_parents(item_groups):
	"""Return {item_group: parent_item_group} for the given Item Groups."""
	if not item_groups:
		return {}

	rows = frappe.db.get_all(
		"Item Group",
		filters={"name": ("in", list(item_groups))},
		fields=["name", "parent_item_group"],
	)
	return {r["name"]: (r.get("parent_item_group") or "") for r in rows}


def get_voucher_info(voucher_keys):
	"""Return {(voucher_type, voucher_no): {party, related_document}}."""
	if not voucher_keys:
		return {}

	type_vouchers = {}
	for voucher_type, voucher_no in voucher_keys:
		type_vouchers.setdefault(voucher_type, set()).add(voucher_no)

	info = {}

	for voucher_type, voucher_nos in type_vouchers.items():
		try:
			if not frappe.db.exists("DocType", voucher_type):
				continue

			meta = frappe.get_meta(voucher_type)

			party_field = next((f for f in PARTY_FIELDS if meta.has_field(f)), None)
			related_fields = [f for f in RELATED_HEADER_FIELDS if meta.has_field(f)]

			select_fields = ["name"]
			if party_field:
				select_fields.append(party_field)
			select_fields.extend(related_fields)

			voucher_nos = list(voucher_nos)
			rows = frappe.db.get_all(
				voucher_type, filters={"name": ("in", voucher_nos)}, fields=select_fields
			)

			# Related document sourced from a child table (e.g. PO on PR Item).
			child_related = get_child_related_documents(voucher_type, voucher_nos)

			for r in rows:
				related = ""
				for f in related_fields:
					if r.get(f):
						related = r.get(f)
						break
				if not related:
					related = child_related.get(r["name"], "")

				info[(voucher_type, r["name"])] = {
					"party": (r.get(party_field) if party_field else "") or "",
					"related_document": related,
				}

		except Exception:
			frappe.log_error(title="Custom Stock Ledger - voucher info")
			continue

	return info


def get_child_related_documents(voucher_type, voucher_nos):
	"""Collect distinct source documents from a voucher's child table."""
	mapping = RELATED_CHILD_SOURCES.get(voucher_type)
	if not mapping or not voucher_nos:
		return {}

	child_doctype, source_field = mapping
	if not frappe.get_meta(child_doctype).has_field(source_field):
		return {}

	rows = frappe.db.get_all(
		child_doctype,
		filters={"parent": ("in", voucher_nos), source_field: ("is", "set")},
		fields=["parent", source_field],
	)

	collected = {}
	for r in rows:
		value = r.get(source_field)
		if value:
			collected.setdefault(r["parent"], set()).add(value)

	return {parent: ", ".join(sorted(values)) for parent, values in collected.items()}
