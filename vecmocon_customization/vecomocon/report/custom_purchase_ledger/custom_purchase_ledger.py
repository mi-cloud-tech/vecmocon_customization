# Copyright (c) 2026, MI_Cloud and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import date_diff, flt

# ---------------------------------------------------------------------------
# Configurable field sources for non-standard / custom fields.
# The first field that actually exists on the doctype is used; otherwise the
# column is left blank.  Adjust these when the corresponding custom fields are
# created so the report picks them up automatically.
# ---------------------------------------------------------------------------
# "Supplier Location" on the Supplier.
SUPPLIER_LOCATION_FIELDS = ("custom_location", "supplier_location", "custom_supplier_location", "country")
# "Debit Note status (Ok/Hold/Rejected)" on the Purchase Invoice (debit note).
DEBIT_NOTE_STATUS_FIELDS = ("custom_debit_note_status", "debit_note_status")


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------
def get_columns():
	return [
		{"label": _("MR No"), "fieldname": "mr_no", "fieldtype": "Link", "options": "Material Request", "width": 130},
		{"label": _("MR Date"), "fieldname": "mr_date", "fieldtype": "Date", "width": 95},
		{"label": _("MR Qty"), "fieldname": "mr_qty", "fieldtype": "Float", "width": 80},
		{"label": _("PO Date"), "fieldname": "po_date", "fieldtype": "Date", "width": 95},
		{"label": _("PO Number"), "fieldname": "po_number", "fieldtype": "Link", "options": "Purchase Order", "width": 140},
		{"label": _("PO Status"), "fieldname": "po_status", "fieldtype": "Data", "width": 100},
		{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": _("Item Description"), "fieldname": "item_description", "fieldtype": "Data", "width": 220},
		{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 70},
		{"label": _("PO Qty"), "fieldname": "po_qty", "fieldtype": "Float", "width": 80},
		{"label": _("Open PO Qty"), "fieldname": "open_po_qty", "fieldtype": "Float", "width": 95},
		{"label": _("Received PO Qty / PR Qty"), "fieldname": "received_qty", "fieldtype": "Float", "width": 120},
		{"label": _("PR Number"), "fieldname": "pr_number", "fieldtype": "Data", "width": 150},
		{"label": _("PR Date"), "fieldname": "pr_date", "fieldtype": "Date", "width": 95},
		{"label": _("PR Status"), "fieldname": "pr_status", "fieldtype": "Data", "width": 100},
		{"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
		{"label": _("Invoice Number"), "fieldname": "invoice_number", "fieldtype": "Data", "width": 150},
		{"label": _("Invoice Date"), "fieldname": "invoice_date", "fieldtype": "Date", "width": 95},
		{"label": _("Payment Status"), "fieldname": "payment_status", "fieldtype": "Data", "width": 110},
		{"label": _("Payment Date"), "fieldname": "payment_date", "fieldtype": "Data", "width": 110},
		{"label": _("Payment Reference No"), "fieldname": "payment_reference_no", "fieldtype": "Data", "width": 140},
		{"label": _("Lead Time (MR to PO Days)"), "fieldname": "lead_time_mr_to_po", "fieldtype": "Int", "width": 110},
		{"label": _("Lead Time (PO to PR Days)"), "fieldname": "lead_time_po_to_pr", "fieldtype": "Int", "width": 110},
		{"label": _("Pending Invoice Qty"), "fieldname": "pending_invoice_qty", "fieldtype": "Float", "width": 110},
		{
			"label": _("Pending Payment Amount"),
			"fieldname": "pending_payment_amount",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 130,
		},
		{"label": _("Supplier Invoice Number"), "fieldname": "supplier_invoice_number", "fieldtype": "Data", "width": 150},
		{"label": _("Supplier Invoice Date"), "fieldname": "supplier_invoice_date", "fieldtype": "Date", "width": 110},
		{
			"label": _("Invoice Amount"),
			"fieldname": "invoice_amount",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 120,
		},
		{
			"label": _("PO Price / Rate"),
			"fieldname": "po_rate",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 110,
		},
		{"label": _("Supplier Code"), "fieldname": "supplier_code", "fieldtype": "Link", "options": "Supplier", "width": 120},
		{"label": _("Supplier Name"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 170},
		{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 170},
		{"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Brand", "width": 110},
		{"label": _("Minimum Order Qty"), "fieldname": "min_order_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Supplier Location"), "fieldname": "supplier_location", "fieldtype": "Data", "width": 130},
		{"label": _("HSN"), "fieldname": "hsn", "fieldtype": "Data", "width": 100},
		{"label": _("Rejection Qty"), "fieldname": "rejection_qty", "fieldtype": "Float", "width": 95},
		{
			"label": _("Debit Note INR"),
			"fieldname": "debit_note_inr",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 110,
		},
		{"label": _("Debit Note Status (Ok/Hold/Rejected)"), "fieldname": "debit_note_status", "fieldtype": "Data", "width": 130},
		{"label": _("Payment Term"), "fieldname": "payment_term", "fieldtype": "Data", "width": 140},
		{"label": _("MR Requester Name"), "fieldname": "mr_requester_name", "fieldtype": "Data", "width": 150},
		{"label": _("PO Creator Name"), "fieldname": "po_creator_name", "fieldtype": "Data", "width": 150},
	]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def get_data(filters):
	po_rows = get_purchase_orders(filters)
	if not po_rows:
		return []

	po_map = {po.name: po for po in po_rows}
	poi_rows = get_purchase_order_items(filters, list(po_map.keys()))
	if not poi_rows:
		return []

	poi_names = [r.name for r in poi_rows]

	# Resolve the optional / custom field names once.
	supplier_loc_field = first_existing_field("Supplier", SUPPLIER_LOCATION_FIELDS)
	debit_status_field = first_existing_field("Purchase Invoice", DEBIT_NOTE_STATUS_FIELDS)

	# Build lookup maps for the related documents.
	mr_map, mri_qty = get_material_request_info(poi_rows)
	pr_map = get_purchase_receipt_info(poi_names)
	pi_map, pi_names = get_purchase_invoice_info(poi_names, debit_status_field)
	payment_map = get_payment_info(pi_names)
	item_map = get_item_info({r.item_code for r in poi_rows})
	supplier_map = get_supplier_info({po.supplier for po in po_rows}, supplier_loc_field)
	user_map = get_user_full_names(
		{po.owner for po in po_rows} | {mr.owner for mr in mr_map.values()}
	)

	data = []
	for poi in poi_rows:
		po = po_map.get(poi.parent)
		if not po:
			continue

		mr = mr_map.get(poi.material_request)
		mr_date = mr.transaction_date if mr else None
		pr = pr_map.get(poi.name, {})
		pi = pi_map.get(poi.name, {})
		item = item_map.get(poi.item_code, {})
		supplier = supplier_map.get(po.supplier, {})

		# Payments aggregated across all invoices linked to this PO line.
		pay = aggregate_payments(pi.get("invoice_names", []), payment_map)

		received_qty = flt(poi.received_qty)
		billed_qty = flt(pi.get("billed_qty"))

		row = {
			"company": po.company,
			# Material Request
			"mr_no": poi.material_request,
			"mr_date": mr_date,
			"mr_qty": mri_qty.get(poi.material_request_item),
			# Purchase Order
			"po_date": po.transaction_date,
			"po_number": po.name,
			"po_status": po.status,
			"item_code": poi.item_code,
			"item_description": poi.description,
			"uom": poi.uom or poi.stock_uom,
			"po_qty": flt(poi.qty),
			"open_po_qty": flt(poi.qty) - received_qty,
			"received_qty": received_qty,
			# Purchase Receipt
			"pr_number": pr.get("numbers"),
			"pr_date": pr.get("earliest_date"),
			"pr_status": pr.get("statuses"),
			"warehouse": poi.warehouse,
			# Purchase Invoice
			"invoice_number": pi.get("invoice_numbers"),
			"invoice_date": pi.get("earliest_date"),
			"supplier_invoice_number": pi.get("supplier_invoice_numbers"),
			"supplier_invoice_date": pi.get("earliest_supplier_date"),
			"invoice_amount": flt(pi.get("amount")),
			# Payment
			"payment_status": derive_payment_status(pi),
			"payment_date": pay.get("dates"),
			"payment_reference_no": pay.get("reference_nos"),
			"pending_payment_amount": flt(pi.get("outstanding")),
			# Lead times
			"lead_time_mr_to_po": days_between(mr_date, po.transaction_date),
			"lead_time_po_to_pr": days_between(po.transaction_date, pr.get("earliest_date")),
			"pending_invoice_qty": received_qty - billed_qty,
			# Rate / supplier / item master
			"po_rate": flt(poi.rate),
			"supplier_code": po.supplier,
			"supplier_name": po.supplier_name,
			"item_group": poi.item_group or item.get("item_group"),
			"item_name": poi.item_name or item.get("item_name"),
			"brand": poi.brand or item.get("brand"),
			"min_order_qty": item.get("min_order_qty"),
			"supplier_location": supplier.get("location"),
			"hsn": poi.get("gst_hsn_code"),
			# Quality / debit note
			"rejection_qty": pr.get("rejected_qty"),
			"debit_note_inr": flt(pi.get("debit_note_amount")),
			"debit_note_status": pi.get("debit_note_status"),
			# Misc
			"payment_term": po.payment_terms_template,
			"mr_requester_name": user_map.get(mr.owner) if mr else None,
			"po_creator_name": user_map.get(po.owner),
		}
		data.append(row)

	return data


def get_purchase_orders(filters):
	conditions = {"docstatus": ["<", 2]}
	if filters.get("company"):
		conditions["company"] = filters.company
	if filters.get("supplier"):
		conditions["supplier"] = filters.supplier
	if filters.get("po_status"):
		conditions["status"] = filters.po_status
	if filters.get("from_date") and filters.get("to_date"):
		conditions["transaction_date"] = ["between", [filters.from_date, filters.to_date]]
	elif filters.get("from_date"):
		conditions["transaction_date"] = [">=", filters.from_date]
	elif filters.get("to_date"):
		conditions["transaction_date"] = ["<=", filters.to_date]

	return frappe.get_all(
		"Purchase Order",
		filters=conditions,
		fields=[
			"name",
			"transaction_date",
			"status",
			"supplier",
			"supplier_name",
			"owner",
			"company",
			"payment_terms_template",
		],
	)


def get_purchase_order_items(filters, po_names):
	conditions = {"parent": ["in", po_names]}
	if filters.get("item_code"):
		conditions["item_code"] = filters.item_code
	if filters.get("item_group"):
		conditions["item_group"] = filters.item_group
	if filters.get("brand"):
		conditions["brand"] = filters.brand

	fields = [
		"name",
		"parent",
		"item_code",
		"item_name",
		"description",
		"uom",
		"stock_uom",
		"qty",
		"received_qty",
		"rate",
		"warehouse",
		"material_request",
		"material_request_item",
		"item_group",
		"brand",
	]
	if frappe.get_meta("Purchase Order Item").has_field("gst_hsn_code"):
		fields.append("gst_hsn_code")

	return frappe.get_all("Purchase Order Item", filters=conditions, fields=fields)


def get_material_request_info(poi_rows):
	mr_names = {r.material_request for r in poi_rows if r.material_request}
	mri_names = {r.material_request_item for r in poi_rows if r.material_request_item}

	mr_map = {}
	if mr_names:
		rows = frappe.get_all(
			"Material Request",
			filters={"name": ["in", list(mr_names)]},
			fields=["name", "transaction_date", "owner"],
		)
		mr_map = {r.name: r for r in rows}

	mri_qty = {}
	if mri_names:
		rows = frappe.get_all(
			"Material Request Item",
			filters={"name": ["in", list(mri_names)]},
			fields=["name", "qty"],
		)
		mri_qty = {r.name: r.qty for r in rows}

	return mr_map, mri_qty


def get_purchase_receipt_info(poi_names):
	"""Aggregate Purchase Receipt data per Purchase Order Item."""
	pri_rows = frappe.get_all(
		"Purchase Receipt Item",
		filters={"purchase_order_item": ["in", poi_names], "docstatus": 1},
		fields=["parent", "purchase_order_item", "received_qty", "rejected_qty"],
	)
	if not pri_rows:
		return {}

	pr_names = {r.parent for r in pri_rows}
	pr_headers = {
		r.name: r
		for r in frappe.get_all(
			"Purchase Receipt",
			filters={"name": ["in", list(pr_names)]},
			fields=["name", "posting_date", "status"],
		)
	}

	agg = defaultdict(lambda: {"numbers": set(), "statuses": set(), "dates": [], "rejected_qty": 0.0})
	for r in pri_rows:
		key = r.purchase_order_item
		header = pr_headers.get(r.parent)
		bucket = agg[key]
		bucket["numbers"].add(r.parent)
		if header:
			if header.status:
				bucket["statuses"].add(header.status)
			if header.posting_date:
				bucket["dates"].append(header.posting_date)
		bucket["rejected_qty"] += flt(r.rejected_qty)

	result = {}
	for key, bucket in agg.items():
		result[key] = {
			"numbers": join_set(bucket["numbers"]),
			"statuses": join_set(bucket["statuses"]),
			"earliest_date": min(bucket["dates"]) if bucket["dates"] else None,
			"rejected_qty": bucket["rejected_qty"],
		}
	return result


def get_purchase_invoice_info(poi_names, debit_status_field):
	"""Aggregate Purchase Invoice data per Purchase Order Item."""
	pii_rows = frappe.get_all(
		"Purchase Invoice Item",
		filters={"po_detail": ["in", poi_names], "docstatus": 1},
		fields=["parent", "po_detail", "qty", "amount"],
	)
	if not pii_rows:
		return {}, []

	pi_names = {r.parent for r in pii_rows}
	header_fields = [
		"name",
		"posting_date",
		"bill_no",
		"bill_date",
		"grand_total",
		"outstanding_amount",
		"status",
		"is_return",
	]
	if debit_status_field:
		header_fields.append(debit_status_field)

	pi_headers = {
		r.name: r
		for r in frappe.get_all(
			"Purchase Invoice", filters={"name": ["in", list(pi_names)]}, fields=header_fields
		)
	}

	agg = defaultdict(
		lambda: {
			"invoice_names": set(),
			"invoice_numbers": set(),
			"supplier_invoice_numbers": set(),
			"invoice_dates": [],
			"supplier_dates": [],
			"amount": 0.0,
			"billed_qty": 0.0,
			"debit_note_amount": 0.0,
			"outstanding_invoices": {},
			"grand_total_invoices": {},
			"debit_note_status": set(),
		}
	)

	for r in pii_rows:
		header = pi_headers.get(r.parent)
		if not header:
			continue
		bucket = agg[r.po_detail]
		bucket["billed_qty"] += flt(r.qty)

		if header.is_return:
			# Debit note (purchase return).
			bucket["debit_note_amount"] += abs(flt(r.amount))
			if debit_status_field and header.get(debit_status_field):
				bucket["debit_note_status"].add(header.get(debit_status_field))
			continue

		bucket["invoice_names"].add(header.name)
		bucket["invoice_numbers"].add(header.name)
		bucket["amount"] += flt(r.amount)
		if header.bill_no:
			bucket["supplier_invoice_numbers"].add(header.bill_no)
		if header.posting_date:
			bucket["invoice_dates"].append(header.posting_date)
		if header.bill_date:
			bucket["supplier_dates"].append(header.bill_date)
		# Outstanding / grand total are header-level: store once per invoice.
		bucket["outstanding_invoices"][header.name] = flt(header.outstanding_amount)
		bucket["grand_total_invoices"][header.name] = flt(header.grand_total)

	result = {}
	for key, bucket in agg.items():
		result[key] = {
			"invoice_names": list(bucket["invoice_names"]),
			"invoice_numbers": join_set(bucket["invoice_numbers"]),
			"supplier_invoice_numbers": join_set(bucket["supplier_invoice_numbers"]),
			"earliest_date": min(bucket["invoice_dates"]) if bucket["invoice_dates"] else None,
			"earliest_supplier_date": min(bucket["supplier_dates"]) if bucket["supplier_dates"] else None,
			"amount": bucket["amount"],
			"billed_qty": bucket["billed_qty"],
			"outstanding": sum(bucket["outstanding_invoices"].values()),
			"grand_total": sum(bucket["grand_total_invoices"].values()),
			"debit_note_amount": bucket["debit_note_amount"],
			"debit_note_status": join_set(bucket["debit_note_status"]),
		}

	all_invoice_names = list({n for b in result.values() for n in b["invoice_names"]})
	return result, all_invoice_names


def get_payment_info(pi_names):
	"""Return {purchase_invoice: {dates, reference_nos}} from Payment Entries."""
	if not pi_names:
		return {}

	refs = frappe.get_all(
		"Payment Entry Reference",
		filters={
			"reference_doctype": "Purchase Invoice",
			"reference_name": ["in", pi_names],
			"docstatus": 1,
		},
		fields=["parent", "reference_name"],
	)
	if not refs:
		return {}

	pe_names = {r.parent for r in refs}
	pe_headers = {
		r.name: r
		for r in frappe.get_all(
			"Payment Entry",
			filters={"name": ["in", list(pe_names)], "docstatus": 1},
			fields=["name", "posting_date", "reference_no"],
		)
	}

	result = defaultdict(lambda: {"dates": [], "reference_nos": set()})
	for r in refs:
		header = pe_headers.get(r.parent)
		if not header:
			continue
		bucket = result[r.reference_name]
		if header.posting_date:
			bucket["dates"].append(header.posting_date)
		if header.reference_no:
			bucket["reference_nos"].add(header.reference_no)
	return result


def aggregate_payments(invoice_names, payment_map):
	dates = []
	reference_nos = set()
	for inv in invoice_names:
		pay = payment_map.get(inv)
		if not pay:
			continue
		dates.extend(pay["dates"])
		reference_nos |= pay["reference_nos"]
	return {
		"dates": join_set({str(d) for d in dates}),
		"reference_nos": join_set(reference_nos),
	}


def get_item_info(item_codes):
	item_codes = {c for c in item_codes if c}
	if not item_codes:
		return {}

	rows = frappe.get_all(
		"Item",
		filters={"name": ["in", list(item_codes)]},
		fields=["name", "item_name", "item_group", "brand", "min_order_qty"],
	)
	info = {}
	for r in rows:
		info[r.name] = {
			"item_name": r.item_name,
			"item_group": r.item_group,
			"brand": r.brand,
			"min_order_qty": r.min_order_qty,
		}
	return info


def get_supplier_info(supplier_codes, location_field):
	supplier_codes = {c for c in supplier_codes if c}
	if not supplier_codes or not location_field:
		return {}

	rows = frappe.get_all(
		"Supplier",
		filters={"name": ["in", list(supplier_codes)]},
		fields=["name", location_field],
	)
	return {r.name: {"location": r.get(location_field)} for r in rows}


def get_user_full_names(user_ids):
	user_ids = {u for u in user_ids if u}
	if not user_ids:
		return {}
	rows = frappe.get_all(
		"User", filters={"name": ["in", list(user_ids)]}, fields=["name", "full_name"]
	)
	return {r.name: r.full_name for r in rows}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def first_existing_field(doctype, candidates):
	"""Return the first field from `candidates` that exists on `doctype`."""
	meta = frappe.get_meta(doctype)
	return next((f for f in candidates if meta.has_field(f)), None)


def join_set(values):
	return ", ".join(sorted({str(v) for v in values if v}))


def days_between(start, end):
	if not start or not end:
		return None
	return date_diff(end, start)


def derive_payment_status(pi):
	if not pi or not pi.get("invoice_names"):
		return "Not Invoiced"
	outstanding = flt(pi.get("outstanding"))
	grand_total = flt(pi.get("grand_total"))
	if outstanding <= 0:
		return "Paid"
	if outstanding < grand_total:
		return "Partly Paid"
	return "Unpaid"
