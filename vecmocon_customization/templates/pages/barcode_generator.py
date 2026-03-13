"""
Barcode Generator Page
Handles the page registration for the barcode generator interface
"""

import frappe
from frappe import _

def get_context(context):
	"""
	Get context for the barcode generator page
	"""
	context.no_cache = 1
	context.show_sidebar = True
	context.page_title = _("Barcode Generator")
	return context
