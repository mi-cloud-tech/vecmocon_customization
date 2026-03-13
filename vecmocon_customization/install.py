"""
Setup script for Vecmocon Customization App
Handles initialization of Barcode Log DocType and other configurations
"""

import frappe
import json
import os


def setup_barcode_module():
	"""
	Setup the Barcode Management module and DocType
	Called during app installation
	"""
	try:
		# Create Barcode Log DocType if it doesn't exist
		if not frappe.db.exists('DocType', 'Barcode Log'):
			frappe.msgprint("Creating Barcode Log DocType...")
			setup_barcode_doctype()
		
		# Setup permissions
		setup_barcode_permissions()
		
		# Create module
		if not frappe.db.exists('Module Def', 'Barcode Management'):
			create_module()
		
		frappe.msgprint("✓ Barcode Management module setup completed successfully")
		return True
	except Exception as e:
		frappe.msgprint(f"Error during setup: {str(e)}", alert=True)
		return False


def setup_barcode_doctype():
	"""
	Create the Barcode Log DocType from the JSON definition
	"""
	try:
		# Get the app directory
		app_dir = frappe.get_app_path('vecmocon_customization')
		
		# Read the DocType JSON
		json_path = os.path.join(
			app_dir,
			'vecomocon/doctype/barcode_log/barcode_log.json'
		)
		
		if not os.path.exists(json_path):
			frappe.throw(f"DocType definition not found at {json_path}")
		
		with open(json_path, 'r') as f:
			doctype_dict = json.load(f)
		
		# Ensure module is set correctly
		doctype_dict['module'] = 'Barcode Management'
		
		# Create the DocType
		doc = frappe.get_doc(doctype_dict)
		doc.insert(ignore_if_exists=True, force=True)
		frappe.db.commit()
		
		frappe.msgprint(f"✓ Barcode Log DocType created successfully")
		return True
	except Exception as e:
		frappe.msgprint(f"Error creating Barcode Log DocType: {str(e)}", alert=True)
		raise


def setup_barcode_permissions():
	"""
	Setup role-based permissions for Barcode Log
	"""
	try:
		# Grant permissions to System Manager
		if not frappe.db.exists('DocPerm', {'parent': 'Barcode Log', 'role': 'System Manager'}):
			perm = frappe.new_doc('DocPerm')
			perm.parent = 'Barcode Log'
			perm.parenttype = 'DocType'
			perm.role = 'System Manager'
			perm.permlevel = 0
			perm.read = 1
			perm.write = 1
			perm.create = 1
			perm.delete = 1
			perm.submit = 0
			perm.amend = 0
			perm.print = 1
			perm.report = 1
			perm.insert(ignore_if_exists=True)
			frappe.db.commit()
		
		# Grant permissions to User
		if not frappe.db.exists('DocPerm', {'parent': 'Barcode Log', 'role': 'User'}):
			perm = frappe.new_doc('DocPerm')
			perm.parent = 'Barcode Log'
			perm.parenttype = 'DocType'
			perm.role = 'User'
			perm.permlevel = 0
			perm.read = 1
			perm.write = 0
			perm.create = 0
			perm.delete = 0
			perm.submit = 0
			perm.amend = 0
			perm.print = 1
			perm.report = 1
			perm.insert(ignore_if_exists=True)
			frappe.db.commit()
		
		frappe.msgprint("✓ Barcode Log permissions setup completed")
		return True
	except Exception as e:
		frappe.msgprint(f"Error setting up permissions: {str(e)}", alert=True)
		return False


def create_module():
	"""
	Create the Barcode Management module
	"""
	try:
		if frappe.db.exists('Module Def', 'Barcode Management'):
			return True
		
		module = frappe.new_doc('Module Def')
		module.module_name = 'Barcode Management'
		module.app_name = 'vecmocon_customization'
		module.insert()
		frappe.db.commit()
		
		frappe.msgprint("✓ Barcode Management module created")
		return True
	except Exception as e:
		frappe.msgprint(f"Error creating module: {str(e)}", alert=True)
		return False


def after_install():
	"""
	Called after the app is installed
	"""
	setup_barcode_module()


def before_uninstall():
	"""
	Called before the app is uninstalled
	Cleans up app-specific configurations (optional)
	"""
	pass
