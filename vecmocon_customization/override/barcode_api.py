# Copyright (c) 2025, MI_Cloud and contributors
# For license information, please see license.txt

import re
import json
from datetime import datetime

import frappe
from frappe import _
import barcode as python_barcode
from barcode.writer import ImageWriter
import qrcode
from io import BytesIO
import base64


def validate_barcode_data(data):
	"""Validate barcode data format and field lengths."""
	errors = []

	vendor = (data.get("vendor_code") or "").strip()
	if not vendor or len(vendor) > 8:
		errors.append(_("Vendor Code is required (max 8 characters)"))

	part = (data.get("part_code") or "").strip()
	if not part or len(part) > 10:
		errors.append(_("Part Code is required (max 10 characters)"))

	batch = (data.get("batch_no") or "").strip()
	if not batch or len(batch) > 14:
		errors.append(_("Batch Number is required (max 14 characters)"))

	packet = (data.get("packet_serial") or "").strip()
	if not packet or len(packet) > 7:
		errors.append(_("Packet Serial is required (max 7 characters)"))

	mfg_date = (data.get("mfg_date") or "").strip()
	if not mfg_date or not re.match(r"^\d{6}$", mfg_date):
		errors.append(_("Manufacturing Date must be 6 digits in YYMMDD format"))
	else:
		try:
			datetime.strptime(mfg_date, "%y%m%d")
		except ValueError:
			errors.append(_("Manufacturing Date is not a valid date"))

	exp_date = (data.get("exp_date") or "").strip()
	if not exp_date or not re.match(r"^\d{6}$", exp_date):
		errors.append(_("Expiry Date must be 6 digits in YYMMDD format"))
	else:
		try:
			datetime.strptime(exp_date, "%y%m%d")
		except ValueError:
			errors.append(_("Expiry Date is not a valid date"))

	qty = (data.get("qty") or "").strip()
	if not qty or not qty.isdigit() or len(qty) > 7:
		errors.append(_("Quantity must be up to 7 digits"))

	constant = (data.get("constant_text") or "").strip()
	if not constant or len(constant) != 1 or not constant.isalpha():
		errors.append(_("Constant Text must be exactly 1 alphabetic character"))

	if errors:
		frappe.throw("<br>".join(errors), title=_("Validation Error"))

	return True


def build_barcode_string(data):
	"""Build barcode string: vendor/part/batch/packet/mfg/exp/qty/constant"""
	return "/".join([
		data.get("vendor_code", "").strip(),
		data.get("part_code", "").strip(),
		data.get("batch_no", "").strip(),
		data.get("packet_serial", "").strip(),
		data.get("mfg_date", "").strip(),
		data.get("exp_date", "").strip(),
		data.get("qty", "").strip(),
		data.get("constant_text", "").strip(),
	])


def get_code_type():
	"""Get configured code type from Vecmocon Settings (Barcode or QR Code)."""
	return frappe.db.get_single_value("Vecmocon Settings", "code_type") or "Barcode"


def generate_code_image(text):
	"""Generate Code128 barcode or QR Code PNG as base64 data URI based on settings."""
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
		code128.write(buf, options={"write_text": True, "module_height": 15.0, "module_width": 0.3, "quiet_zone": 2.0})

	buf.seek(0)
	return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


@frappe.whitelist()
def generate_barcode(data):
	"""Generate barcode string + Code128 barcode image without saving a log."""
	if isinstance(data, str):
		data = json.loads(data)

	validate_barcode_data(data)
	barcode_string = build_barcode_string(data)

	existing = frappe.db.get_value("Barcode Log", {"barcode_string": barcode_string}, "name")
	if existing:
		return {
			"barcode_string": barcode_string,
			"barcode_image": generate_code_image(barcode_string),
			"barcode_log": existing,
			"already_exists": True,
		}

	return {
		"barcode_string": barcode_string,
		"barcode_image": generate_code_image(barcode_string),
	}


@frappe.whitelist()
def save_barcode_log(data):
	"""Generate barcode image and save a Barcode Log entry."""
	if isinstance(data, str):
		data = json.loads(data)

	validate_barcode_data(data)
	barcode_string = build_barcode_string(data)

	existing = frappe.db.get_value("Barcode Log", {"barcode_string": barcode_string}, "name")
	if existing:
		return {
			"barcode_log": existing,
			"barcode_string": barcode_string,
			"barcode_image": generate_code_image(barcode_string),
			"already_exists": True,
		}

	qr_image = generate_code_image(barcode_string)

	log = frappe.new_doc("Barcode Log")
	log.barcode_string = barcode_string
	log.vendor_code = data["vendor_code"].strip()
	log.part_code = data["part_code"].strip()
	log.batch_no = data["batch_no"].strip()
	log.packet_serial = data["packet_serial"].strip()
	log.mfg_date = datetime.strptime(data["mfg_date"].strip(), "%y%m%d").strftime("%Y-%m-%d")
	log.exp_date = datetime.strptime(data["exp_date"].strip(), "%y%m%d").strftime("%Y-%m-%d")
	log.qty = data["qty"].strip()
	log.constant_text = data["constant_text"].strip()
	log.generated_by = frappe.session.user
	log.generated_on = frappe.utils.now()
	log.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"barcode_log": log.name,
		"barcode_string": barcode_string,
		"barcode_image": qr_image,
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
		"packet_serial": parts[3],
		"mfg_date": parts[4],
		"exp_date": parts[5],
		"qty": parts[6],
		"constant_text": parts[7],
	}


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
	has_serial_no = 0
	if frappe.db.exists("Item", item_code):
		item_doc = frappe.get_cached_doc("Item", item_code)
		item_name = item_doc.item_name
		uom = item_doc.stock_uom
		has_batch_no = item_doc.has_batch_no
		has_serial_no = item_doc.has_serial_no

	# --- Auto-create Batch if item has batch tracking and batch doesn't exist ---
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
		# "serial_no": parsed["packet_serial"],
		"serial_no": "",
		"qty": qty,
		"mfg_date": mfg_date,
		"exp_date": exp_date,
		"supplier": supplier,
		"supplier_name": supplier_name,
		"vendor_code": vendor_code,
		"constant_text": parsed["constant_text"],
		"has_batch_no": has_batch_no,
		"has_serial_no": has_serial_no,
	}


@frappe.whitelist()
def get_barcode_image(barcode_string):
	"""Regenerate barcode/QR code image from a barcode string based on settings."""
	if not barcode_string:
		frappe.throw(_("Barcode string is required"))
	return generate_code_image(barcode_string)


@frappe.whitelist()
def get_code_type_setting():
	"""Return current code type setting for frontend use."""
	return get_code_type()


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
def get_items_for_vendor(vendor_code):
	"""Get items whose Item Supplier child has the given supplier_part_no (Vendor Part Code)."""
	vendor_code = (vendor_code or "").strip()
	if not vendor_code:
		return []

	rows = frappe.get_all(
		"Item Supplier",
		filters={"supplier_part_no": vendor_code},
		fields=["parent as item_code", "supplier"],
	)

	result = []
	for row in rows:
		item_name = frappe.get_value("Item", row["item_code"], "item_name") or ""
		supplier_name = frappe.get_value("Supplier", row["supplier"], "supplier_name") or ""
		result.append({
			"item_code": row["item_code"],
			"item_name": item_name,
			"supplier": row["supplier"],
			"supplier_name": supplier_name,
		})
	return result


@frappe.whitelist()
def item_query_for_vendor(doctype, txt, searchfield, start, page_len, filters):
	"""Link field query: return Items whose Item Supplier child has the given supplier_part_no."""
	vendor_code = (filters.get("vendor_code") or "").strip()

	if not vendor_code:
		return frappe.db.sql("""
			SELECT name, item_name FROM `tabItem`
			WHERE (name LIKE %(txt)s OR item_name LIKE %(txt)s)
			ORDER BY name
			LIMIT %(start)s, %(page_len)s
		""", {"txt": f"%{txt}%", "start": start, "page_len": page_len})

	return frappe.db.sql("""
		SELECT DISTINCT i.name, i.item_name
		FROM `tabItem` i
		INNER JOIN `tabItem Supplier` its ON its.parent = i.name
		WHERE its.supplier_part_no = %(vendor_code)s
		AND (i.name LIKE %(txt)s OR i.item_name LIKE %(txt)s)
		ORDER BY i.name
		LIMIT %(start)s, %(page_len)s
	""", {"vendor_code": vendor_code, "txt": f"%{txt}%", "start": start, "page_len": page_len})
