# Copyright (c) 2026, MI_Cloud and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def validate_warehouse_item_group(doctype, doc):
    """
    Validate that items in a stock transaction belong to allowed item groups for their warehouses.
    
    Args:
        doctype: Document type (Stock Entry, Purchase Receipt, Delivery Note, etc.)
        docname: Document name
    """    
    if doctype == "Stock Entry":      
        for item in doc.items:
            if item.t_warehouse:
                validate_item_in_warehouse(item.item_code, item.t_warehouse)
            if item.s_warehouse and doc.purpose == "Material Receipt":
                validate_item_in_warehouse(item.item_code, item.s_warehouse)
    
    elif doctype == "Purchase Receipt":
        items = doc.items
        
        for item in items:
            warehouse = item.warehouse
            if warehouse:
                validate_item_in_warehouse(item.item_code, warehouse)
    
    elif doctype == "Delivery Note":
        items = doc.items
        
        for item in items:
            warehouse = item.warehouse
            if warehouse:
                validate_item_in_warehouse(item.item_code, warehouse)


def validate_item_in_warehouse(item_code, warehouse, doc_name=None):
    """
    Check if item's item group is allowed in the warehouse.
    Uses the custom_allowed_item_group field from the Warehouse doctype.
    
    Args:
        item_code: Item code to validate
        warehouse: Warehouse code
        doc_name: Document name for error message
    """
    # Get item's item group
    item_group = frappe.db.get_value("Item", item_code, "item_group")
    if not item_group:
        return

    warehouse_doc = frappe.get_doc("Warehouse", warehouse)
    if not hasattr(warehouse_doc, 'custom_allowed_item_group') or not warehouse_doc.custom_allowed_item_group:
        return
    
    # Get list of allowed item groups
    allowed_groups = [row.item_group for row in warehouse_doc.custom_allowed_item_group if row.item_group]
    if not allowed_groups:
        # No restrictions if field is empty
        return
    
    # Check if item's group is in allowed groups
    if item_group not in allowed_groups:
        frappe.throw(
            _("Item <b>{0}</b> with Item Group <b>{1}</b> cannot be stored in Warehouse <b>{2}</b>.<br/>" +
                "Allowed Item Groups: <b>{3}</b>").format(
                frappe.bold(item_code),
                frappe.bold(item_group),
                frappe.bold(warehouse),
                ", ".join(allowed_groups)
            )
        )