import frappe
from frappe.utils import add_days

def purchase_receipt_before_insert(doc, method):
    if doc.is_return:
        return

    for i in doc.items:
        inspection_required_before_purchase = frappe.get_value("Item", i.item_code, "inspection_required_before_purchase")
        if inspection_required_before_purchase and not i.custom_quality_inspection_due_date:
            i.custom_quality_inspection_due_date = add_days(doc.posting_date, 3)

def purchase_receipt_before_save(doc, method):
    if doc.is_return:
        return

    for i in doc.items:
        inspection_required_before_purchase = frappe.get_value("Item", i.item_code, "inspection_required_before_purchase")
        if inspection_required_before_purchase:
            if not i.custom_quality_inspection_due_date:
                i.custom_quality_inspection_due_date = add_days(doc.posting_date, 3)
            quality_warehouse = frappe.get_value("Warehouse", i.warehouse, "custom_is_quality_warehouse")
            if not quality_warehouse:
                default_quality_warehouse = frappe.get_value("Company", doc.company, "custom_default_quality_warehouse")
                if default_quality_warehouse:
                    i.warehouse = default_quality_warehouse
                else:
                    frappe.throw(f"Item {i.item_code} requires quality inspection but no default quality warehouse is set in Company settings.")

def purchase_receipt_before_submit(doc, method):
    """Ensure all items requiring quality inspection have due dates and quality warehouses."""
    if doc.is_return:
        return

    for i in doc.items:
        inspection_required_before_purchase = frappe.get_value("Item", i.item_code, "inspection_required_before_purchase")
        if inspection_required_before_purchase:
            if not i.custom_quality_inspection_due_date:
                i.custom_quality_inspection_due_date = add_days(doc.posting_date, 3)
            quality_warehouse = frappe.get_value("Warehouse", i.warehouse, "custom_is_quality_warehouse")
            if not quality_warehouse:
                frappe.throw(f"Row {i.idx}: Item {i.item_code} requires quality inspection but is not assigned to a quality warehouse.")

def purchase_receipt_on_submit(doc, method):
    """Create Quality Inspection for items requiring inspection and update workflow state."""
    if doc.is_return:
        return

    for i in doc.items:
        inspection_required = frappe.get_value("Item", i.item_code, "inspection_required_before_purchase")
        if not inspection_required:
            continue

        due_date = i.get("custom_quality_inspection_due_date")
        if not due_date:
            continue

        # Check if QI already exists for this PR item
        existing_qi = frappe.db.exists("Quality Inspection", {"reference_type": "Purchase Receipt", "reference_name": doc.name, "item_code": i.item_code})
        if existing_qi:
            continue

        # Create new Quality Inspection
        qi = frappe.new_doc("Quality Inspection")
        qi.inspection_type = "Incoming"
        qi.reference_type = "Purchase Receipt"
        qi.sample_size = i.qty
        qi.reference_name = doc.name
        qi.child_row_reference = i.name
        qi.custom_source_warehouse = i.warehouse
        qi.item_code = i.item_code
        qi.description = i.description or ""
        qi.custom_due_date = due_date
        qi.company = doc.company
        qi.inspected_by = doc.owner
        qi.insert(ignore_permissions=True)
        qi_created = True