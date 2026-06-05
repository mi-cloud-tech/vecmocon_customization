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

def stock_entry_before_save(doc, method):
    if not doc.items:
        return

    warehouse = doc.items[0].s_warehouse
    letter_head = frappe.db.get_value("Warehouse", warehouse, "custom_letter_head")

    if not letter_head:
        parent_warehouse = frappe.db.get_value("Warehouse", warehouse, "parent_warehouse")
        if parent_warehouse:
            letter_head = frappe.db.get_value("Warehouse", parent_warehouse, "custom_letter_head")

    if letter_head:
        doc.letter_head = letter_head