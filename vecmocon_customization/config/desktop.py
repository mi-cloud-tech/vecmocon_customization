"""
Desktop configuration for Vecmocon Customization
Defines app structure, modules, and quick access items
"""

from frappe import _

def get_data():
	return [
		{
			"module_name": "Barcode Management",
			"color": "#1f78d1",
			"icon": "octicon octicon-barcode",
			"type": "module",
			"label": _("Barcode Management"),
			"items": [
				{
					"type": "page",
					"name": "barcode-generator",
					"label": _("Barcode Generator"),
					"description": _("Generate and manage QR barcodes for warehouse operations")
				},
				{
					"type": "doctype",
					"name": "Barcode Log",
					"label": _("Barcode Log"),
					"description": _("Track all generated barcodes")
				},
				{
					"type": "report",
					"name": "Barcode Log Report",
					"doctype": "Barcode Log"
				},
			]
		},
	]
