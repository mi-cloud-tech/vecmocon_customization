# Copyright (c) 2025, MI_Cloud and contributors
# For license information, please see license.txt

# Copyright (c) 2025
import frappe
import json
import base64
from io import BytesIO
from datetime import datetime

import barcode as python_barcode
from barcode.writer import ImageWriter
import qrcode


# =========================================================
# 🔹 SETTINGS
# =========================================================
def get_code_type():
	return frappe.db.get_single_value("Vecmocon Settings", "code_type") or "Barcode"


# =========================================================
# 🔹 COMMON HELPERS
# =========================================================
def format_date(date):
	if not date:
		return ""
	return date.strftime("%y%m%d")


def build_barcode_string(d):
	"""
	FORMAT:
	vendor/part/batch/mfg/exp/qty/constant
	"""
	return "/".join([
		(d.get("vendor_part_code") or "").strip(),
		(d.get("part_code") or "").strip(),
		(d.get("batch_no") or "").strip(),
		(d.get("mpn") or "").strip(),
		(d.get("mfg_date") or "").strip(),
		(d.get("exp_date") or "").strip(),
		(d.get("qty") or "").strip(),
		(d.get("constant_text") or "").strip(),
		(d.get("purchase_order") or "").strip(),
		(d.get("purchase_order_date") or "").strip(),
		(d.get("purchase_receipt") or "").strip(),
		(d.get("purchase_receipt_date") or "").strip(),
		(d.get("vendor_name") or "").strip()
	])


def generate_code_image(text):
	code_type = get_code_type()
	buf = BytesIO()

	if code_type == "QR Code":
		qr = qrcode.QRCode(version=1, box_size=6, border=2)
		qr.add_data(text)
		qr.make(fit=True)
		img = qr.make_image(fill_color="black", back_color="white")
		img.save(buf, format="PNG")
	else:
		code128 = python_barcode.get("code128", text, writer=ImageWriter())
		code128.write(buf, {
			"write_text": True,
			"module_height": 15,
			"module_width": 0.3
		})

	buf.seek(0)
	return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# =========================================================
# 🔹 FETCH PR ITEMS WITH DETAILS
# =========================================================
@frappe.whitelist()
def get_pr_items_with_details(pr):
	doc = frappe.get_doc("Purchase Receipt", pr)

	result = []

	# ✅ Header Level Data
	purchase_receipt = doc.name
	purchase_receipt_date = doc.posting_date
	vendor_name = doc.supplier

	for row in doc.items:

		# ✅ Purchase Order Details (Row level)
		purchase_order = row.purchase_order or ""
		purchase_order_date = ""

		if purchase_order and frappe.db.exists("Purchase Order", purchase_order):
			purchase_order_date = frappe.db.get_value(
				"Purchase Order",
				purchase_order,
				"transaction_date"
			)

		# ✅ Item Master
		item = frappe.get_doc("Item", row.item_code)
		item_name = item.item_name
		vendor_part_code = ""
		for s in item.supplier_items:
			if s.supplier_part_no:
				vendor_part_code = s.supplier_part_no
				break

		# ✅ Batch Details
		mfg_date = ""
		exp_date = ""
		vendor_batch_no = ""

		if row.batch_no and frappe.db.exists("Batch", row.batch_no):
			batch = frappe.get_doc("Batch", row.batch_no)

			if batch.manufacturing_date:
				mfg_date = format_date(batch.manufacturing_date)

			if batch.expiry_date:
				exp_date = format_date(batch.expiry_date)

			vendor_batch_no = batch.custom_vendor_batch_no or ""

		# ✅ Append Result
		result.append({
			"purchase_order": purchase_order,
			"purchase_order_date": purchase_order_date,
			"purchase_receipt": purchase_receipt,
			"purchase_receipt_date": purchase_receipt_date,
			"vendor_name": vendor_name,
			"vendor_part_code": vendor_part_code,
			"part_code": row.item_code,
			"mpn": item_name,
			"batch_no": row.batch_no,
			"vendor_batch_no": vendor_batch_no,
			"mfg_date": mfg_date,
			"exp_date": exp_date,
			"qty": str(int(row.qty or 0)),
			"constant_text": "A"
		})

	return result

# =========================================================
# 🔹 BULK GENERATE
# =========================================================
@frappe.whitelist()
def generate_barcode_bulk(data):
	data = frappe.parse_json(data)
	result = []

	for d in data:
		barcode_string = build_barcode_string(d)
		image = generate_code_image(barcode_string)

		result.append({
			"barcode_string": barcode_string,
			"barcode_image": image,

			# ✅ Add label-value mapping
			"labels": {
				"Vendor Code": d.get("vendor_code"),
				"Part Code": d.get("part_code"),
				"Batch No": d.get("batch_no"),
				"V-Batch No": d.get("vendor_batch_no"),
				"MFG Date": d.get("mfg_date"),
				"EXP Date": d.get("exp_date"),
				"Qty": d.get("qty"),
				"PO": d.get('purchase_order'),
				"PO Date": d.get('purchase_order_date'),
				"PR": d.get('purchase_receipt'),
				"PR Date": d.get('purchase_receipt_date'),
				"Vendor Name": d.get('vendor_name'),
				"MPN": d.get('mpn')
			}
		})

	return result


# =========================================================
# 🔹 BULK SAVE + GENERATE
# =========================================================
@frappe.whitelist()
def save_barcode_bulk(data, purchase_receipt=None):
	data = frappe.parse_json(data)
	result = []

	for d in data:
		barcode_string = build_barcode_string(d)
		image = generate_code_image(barcode_string)

		# Avoid duplicate
		existing = frappe.db.get_value("Barcode Log", {"barcode_string": barcode_string})
		if existing:
			result.append({
				"barcode_string": barcode_string,
				"barcode_image": image,
				"barcode_log": existing,
				"already_exists": True
			})
			continue

		doc = frappe.get_doc({
			"doctype": "Barcode Log",
			"vendor_code": d.get("vendor_code"),
			"part_code": d.get("part_code"),
			"mpn": d.get("mpn"),
			"batch_no": d.get("batch_no"),
			"mfg_date": datetime.strptime(d.get("mfg_date"), "%y%m%d") if d.get("mfg_date") else None,
			"exp_date": datetime.strptime(d.get("exp_date"), "%y%m%d") if d.get("exp_date") else None,
			"qty": d.get("qty"),
			"constant_text": d.get("constant_text"),
			"barcode_string": barcode_string,
			"purchase_receipt": purchase_receipt
		})

		doc.insert(ignore_permissions=True)

		result.append({
			"barcode_string": barcode_string,
			"barcode_image": image,
			"barcode_log": doc.name
		})

	return result

@frappe.whitelist()
def custom_scan_barcode(search_value):
	"""
	Override ERPNext's erpnext.stock.utils.scan_barcode.
	If the scanned value matches our custom format (8 fields separated by /),
	parse it using our logic. Otherwise, fall through to ERPNext's default.
	"""
	search_value = (search_value or "").strip()

	# Check if it matches our custom format
	if "/" in search_value and len(search_value.split("/")) == 8:
		return scan_barcode(search_value)

	# Fall through to ERPNext's original scan_barcode
	from erpnext.stock.utils import scan_barcode as erp_scan_barcode
	return erp_scan_barcode(search_value)

@frappe.whitelist()
def scan_barcode(barcode_string):
	"""
	Parse a scanned barcode and return ERPNext-mapped field values.
	Looks up Item by part_code and Supplier by vendor_code.
	"""
	parsed = parse_barcode_string(barcode_string)

	mfg_date = datetime.strptime(parsed["mfg_date"], "%y%m%d").strftime("%Y-%m-%d")
	exp_date = datetime.strptime(parsed["exp_date"], "%y%m%d").strftime("%Y-%m-%d")
	qty = int(parsed["qty"])

	# --- Item lookup ---
	item_code = parsed["part_code"]
	item_name = ""
	uom = ""
	has_batch_no = 0
	if frappe.db.exists("Item", item_code):
		item_doc = frappe.get_cached_doc("Item", item_code)
		item_name = item_doc.item_name
		uom = item_doc.stock_uom
		has_batch_no = item_doc.has_batch_no

	batch_no = parsed["batch_no"]
	if has_batch_no and batch_no and not frappe.db.exists("Batch", batch_no):
		batch_doc = frappe.new_doc("Batch")
		batch_doc.batch_id = batch_no
		batch_doc.item = item_code
		batch_doc.manufacturing_date = mfg_date
		batch_doc.expiry_date = exp_date
		batch_doc.save(ignore_permissions=True)
		frappe.db.commit()

	# --- Supplier lookup via supplier_part_no in Item Supplier ---
	supplier = ""
	supplier_name = ""
	vendor_code = parsed["vendor_code"]
	sup_link = frappe.db.get_value(
		"Item Supplier", {"supplier_part_no": vendor_code}, "supplier"
	)
	if sup_link:
		supplier = sup_link
		supplier_name = frappe.get_value("Supplier", sup_link, "supplier_name") or ""

	return {
		"item_code": item_code,
		"item_name": item_name,
		"uom": uom,
		"batch_no": parsed["batch_no"],
		"qty": qty,
		"mfg_date": mfg_date,
		"exp_date": exp_date,
		"supplier": supplier,
		"supplier_name": supplier_name,
		"vendor_code": vendor_code,
		"constant_text": parsed["constant_text"],
		"has_batch_no": has_batch_no,
	}

def parse_barcode_string(barcode_string):
	"""Split a barcode string into its 8 components."""
	parts = barcode_string.strip().split("/")
	if len(parts) != 8:
		frappe.throw(
			_("Invalid barcode format. Expected 8 fields separated by '/', got {0}").format(len(parts))
		)
	return {
		"vendor_code": parts[0],
		"part_code": parts[1],
		"batch_no": parts[2],
		"mpn": parts[3],
		"mfg_date": parts[4],
		"exp_date": parts[5],
		"qty": parts[6],
		"constant_text": parts[7],
	}