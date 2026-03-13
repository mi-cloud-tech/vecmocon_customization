# Copyright (c) 2026, MI_Cloud and contributors
# For license information, please see license.txt

import frappe
from vecmocon_customization.override.warehouse_validation import validate_warehouse_item_group


def validate_stock_entry(doc, method):
    """Validate Stock Entry items against warehouse-item group mapping."""
    validate_warehouse_item_group("Stock Entry", doc)


def validate_purchase_receipt(doc, method):
    """Validate Purchase Receipt items against warehouse-item group mapping."""
    validate_warehouse_item_group("Purchase Receipt", doc)


def validate_delivery_note(doc, method):
    """Validate Delivery Note items against warehouse-item group mapping."""
    validate_warehouse_item_group("Delivery Note", doc)
