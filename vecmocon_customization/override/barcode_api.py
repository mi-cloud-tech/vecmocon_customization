# Copyright (c) 2025, MI_Cloud and contributors
# For license information, please see license.txt

import re
from datetime import datetime

import frappe
import qrcode
from io import BytesIO
import base64


def generate_barcode_string(data):
	"""
	Generate barcode string from structured data
	Format: {vendor}/{part}/{batch}/{packet}/{mfg}/{exp}/{qty}/{constant}
	"""
	try:
		barcode = f"{data.get('vendor_code')}/{data.get('part_code')}/{data.get('batch_no')}/{data.get('packet_serial')}/{data.get('mfg_date')}/{data.get('exp_date')}/{data.get('qty')}/{data.get('constant_text')}"
		return barcode
	except Exception as e:
		frappe.throw(f"Error generating barcode: {str(e)}")


def validate_barcode_data(data):
	"""
	Validate barcode data format and field lengths
	"""
	errors = []
	
	# Vendor Code - 8 digits
	vendor = data.get('vendor_code', '').strip()
	if not vendor or len(vendor) != 8 or not vendor.isalnum():
		errors.append("Vendor Code must be 8 alphanumeric characters")
	
	# Part Code - 10 characters
	part = data.get('part_code', '').strip()
	if not part or len(part) != 10 or not part.isalnum():
		errors.append("Part Code must be 10 alphanumeric characters")
	
	# Batch Number - 14 characters
	batch = data.get('batch_no', '').strip()
	if not batch or len(batch) != 14 or not batch.isalnum():
		errors.append("Batch Number must be 14 alphanumeric characters")
	
	# Packet Serial - 7 characters
	packet = data.get('packet_serial', '').strip()
	if not packet or len(packet) != 7 or not packet.isalnum():
		errors.append("Packet Serial must be 7 alphanumeric characters")
	
	# Manufacturing Date - YYMMDD format
	mfg_date = data.get('mfg_date', '').strip()
	if not mfg_date or not re.match(r'^\d{6}$', mfg_date):
		errors.append("Manufacturing Date must be in YYMMDD format (6 digits)")
	
	# Expiry Date - YYMMDD format
	exp_date = data.get('exp_date', '').strip()
	if not exp_date or not re.match(r'^\d{6}$', exp_date):
		errors.append("Expiry Date must be in YYMMDD format (6 digits)")
	
	# Quantity - 7 digits
	qty = data.get('qty', '').strip()
	if not qty or len(qty) != 7 or not qty.isdigit():
		errors.append("Quantity must be 7 digits")
	
	# Constant Text - 1 character
	constant = data.get('constant_text', '').strip()
	if not constant or len(constant) != 1 or not constant.isalpha():
		errors.append("Constant Text must be 1 alphabetic character")
	
	if errors:
		frappe.throw("\n".join(errors))
	
	return True


def check_duplicate_barcode(barcode_string):
	"""
	Check if barcode already exists in the system
	"""
	existing = frappe.db.exists('Barcode Log', {'barcode_string': barcode_string})
	if existing:
		frappe.throw(f"Barcode already exists: {barcode_string}")
	return False


def generate_qr_code(barcode_string):
	"""
	Generate QR code image from barcode string
	Returns base64 encoded PNG image
	"""
	try:
		qr = qrcode.QRCode(
			version=1,
			error_correction=qrcode.constants.ERROR_CORRECT_L,
			box_size=10,
			border=4,
		)
		qr.add_data(barcode_string)
		qr.make(fit=True)
		
		img = qr.make_image(fill_color="black", back_color="white")
		
		# Convert image to base64
		img_buffer = BytesIO()
		img.save(img_buffer, format='PNG')
		img_buffer.seek(0)
		img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
		
		return f"data:image/png;base64,{img_base64}"
	except Exception as e:
		frappe.throw(f"Error generating QR code: {str(e)}")


@frappe.whitelist()
def generate_barcode(data):
	"""
	Main endpoint to generate barcode
	Endpoint: /api/method/vecmocon_customization.override.barcode_api.generate_barcode
	"""
	try:
		# Parse data if it's a string
		if isinstance(data, str):
			import json
			data = json.loads(data)
		
		# Validate data
		validate_barcode_data(data)
		barcode_string = generate_barcode_string(data)
		
		# Check for duplicates
		check_duplicate_barcode(barcode_string)
		
		# Generate QR code
		qr_code_image = generate_qr_code(barcode_string)
		
		return {
			'barcode_string': barcode_string,
			'qr_code': qr_code_image,
			'status': 'success'
		}
	except Exception as e:
		return {
			'status': 'error',
			'message': str(e)
		}


@frappe.whitelist()
def save_barcode_log(data):
	"""
	Save barcode log entry
	Endpoint: /api/method/vecmocon_customization.override.barcode_api.save_barcode_log
	"""
	try:
		# Parse data if it's a string
		if isinstance(data, str):
			import json
			data = json.loads(data)
		
		# Validate data
		validate_barcode_data(data)
		barcode_string = generate_barcode_string(data)
		
		# Check for duplicates
		check_duplicate_barcode(barcode_string)
		
		# Create Barcode Log entry
		log = frappe.new_doc('Barcode Log')
		log.barcode_string = barcode_string
		log.vendor_code = data.get('vendor_code')
		log.part_code = data.get('part_code')
		log.batch_no = data.get('batch_no')
		log.packet_serial = data.get('packet_serial')
		log.mfg_date = datetime.strptime(data.get('mfg_date'), '%y%m%d').strftime('%Y-%m-%d')
		log.exp_date = datetime.strptime(data.get('exp_date'), '%y%m%d').strftime('%Y-%m-%d')
		log.qty = data.get('qty')
		log.constant_text = data.get('constant_text')
		log.generated_by = frappe.session.user
		log.generated_on = frappe.utils.now()
		log.save()
		frappe.db.commit()
		
		return {
			'status': 'success',
			'barcode_log': log.name,
			'barcode_string': barcode_string,
			'message': 'Barcode log saved successfully'
		}
	except Exception as e:
		return {
			'status': 'error',
			'message': str(e)
		}


def parse_barcode_string(barcode_string):
	"""
	Parse barcode string to extract individual fields
	"""
	try:
		parts = barcode_string.split('/')
		if len(parts) != 8:
			frappe.throw("Invalid barcode format")
		
		return {
			'vendor_code': parts[0],
			'part_code': parts[1],
			'batch_no': parts[2],
			'packet_serial': parts[3],
			'mfg_date': parts[4],
			'exp_date': parts[5],
			'qty': parts[6],
			'constant_text': parts[7]
		}
	except Exception as e:
		frappe.throw(f"Error parsing barcode: {str(e)}")


@frappe.whitelist()
def scan_barcode(barcode_string):
	"""
	Process scanned barcode and fetch data
	Used by client script to populate fields during scan
	"""
	try:
		parsed_data = parse_barcode_string(barcode_string)
		
		# Convert date format from YYMMDD to YYYY-MM-DD
		mfg_date = datetime.strptime(parsed_data['mfg_date'], '%y%m%d').strftime('%Y-%m-%d')
		exp_date = datetime.strptime(parsed_data['exp_date'], '%y%m%d').strftime('%Y-%m-%d')
		
		return {
			'status': 'success',
			'item_code': parsed_data['part_code'],
			'batch_no': parsed_data['batch_no'],
			'qty': int(parsed_data['qty']),
			'mfg_date': mfg_date,
			'exp_date': exp_date,
			'vendor_code': parsed_data['vendor_code'],
			'packet_serial': parsed_data['packet_serial'],
			'constant_text': parsed_data['constant_text']
		}
	except Exception as e:
		return {
			'status': 'error',
			'message': str(e)
		}
