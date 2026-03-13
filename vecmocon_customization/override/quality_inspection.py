import frappe

def quality_inspection_before_insert(doc, method):
    if doc.reference_type != "Purchase Receipt":
        return

    if doc.child_row_reference:
        row = frappe.db.get_value("Purchase Receipt Item", doc.child_row_reference, "custom_quality_inspection_due_date", as_dict=True)
        if row:
            doc.custom_due_date = row.custom_quality_inspection_due_date

def quality_inspection_before_save(doc, method):
    if doc.reference_type != "Purchase Receipt":
        return

    if doc.child_row_reference and not doc.custom_due_date:
        row = frappe.db.get_value("Purchase Receipt Item", doc.child_row_reference, "custom_quality_inspection_due_date", as_dict=True)
        if row:
            doc.custom_due_date = row.custom_quality_inspection_due_date

def quality_inspection_before_submit(doc, method):
    if doc.reference_type != "Purchase Receipt":
        return
    if doc.status == "Rejected":
        target_warehouse = frappe.get_value("Warehouse", doc.custom_warehouse, "is_rejected_warehouse")
        if not target_warehouse:
            frappe.throw("Selected warehouse is not marked as Rejected Warehouse. Please select a valid warehouse.")
    
    if doc.sample_size != (doc.custom_accetped_qty + doc.custom_rejected_qty):
        frappe.throw(f"The sum of Acceted Qty & Rejected Qty. Not Matching to Total Qty")

    doc.custom_submitted_date = frappe.utils.now_datetime().date()
    doc.custom_delay_days = (doc.custom_submitted_date - doc.custom_due_date).days if doc.custom_due_date else 0

def quality_inspection_on_submit(doc, method):
    #Create Stock Entry to transfer items to quality warehouse if inspection is accepted
    if doc.reference_type != "Purchase Receipt":
        return
    docstatus = frappe.db.get_value("Purchase Receipt", doc.reference_name, "docstatus")    
    if docstatus != 1:
        frappe.throw("Purchase Receipt is not submitted")

    if not doc.custom_warehouse and doc.custom_rejected_qty > 0:
        frappe.throw("Rejected Warehouse not specified in Quality Inspection")
    if not doc.custom_accetped_warehouse and doc.custom_accetped_qty > 0:
        frappe.throw("Accetped Warehouse not specified in Quality Inspection")

    if doc.custom_accetped_qty == 0 and doc.custom_rejected_qty == 0:
        frappe.throw("Qty Cannot Be Zero")
    
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Transfer"
    stock_entry.company = doc.company
    stock_entry.posting_date = frappe.utils.nowdate()
    
    if doc.custom_accetped_qty > 0:
        stock_entry.append("items", {
            "item_code": doc.item_code,
            "item_name": frappe.get_value("Item", doc.item_code, "item_name"),
            "item_group": frappe.get_value("Item", doc.item_code, "item_group"),
            "s_warehouse": doc.custom_source_warehouse,
            "t_warehouse": doc.custom_accetped_warehouse,
            "basic_rate": 0,
            "basic_amount": 0,
            "qty": doc.custom_accetped_qty,
        })

    if doc.custom_rejected_qty > 0:
        stock_entry.append("items", {
            "item_code": doc.item_code,
            "item_name": frappe.get_value("Item", doc.item_code, "item_name"),
            "item_group": frappe.get_value("Item", doc.item_code, "item_group"),
            "s_warehouse": doc.custom_source_warehouse,
            "t_warehouse": doc.custom_warehouse,
            "basic_rate": 0,
            "basic_amount": 0,
            "qty": doc.custom_rejected_qty,
        })
    stock_entry.custom_quality_inspection = doc.name
    stock_entry.insert()
    stock_entry.submit()

# def quality_inspection_on_submit(doc, method):
#     if doc.reference_type != "Purchase Receipt":
#         return
   
#     filters = (
#         {"name": doc.child_row_reference} if doc.child_row_reference else {"parent": doc.reference_name, "item_code": doc.item_code}
#     )
#     rejected = doc.custom_rejected_qty or 0
#     if rejected <= 0:
#         frappe.db.set_value("Purchase Receipt Item", filters, {"custom_qi_before_purchase": 0})
#         return

#     row = frappe.db.get_value("Purchase Receipt Item", filters, ["received_qty", "rejected_qty"], as_dict=True)
#     if not row:
#         return

#     new_rejected = (row.rejected_qty or 0) + rejected
#     new_qty = (row.received_qty or 0) - new_rejected
#     frappe.db.set_value("Purchase Receipt Item", filters, {"rejected_qty": new_rejected, "qty": max(new_qty, 0)})
#     frappe.db.set_value("Purchase Receipt Item", filters, {"custom_qi_before_purchase": 0})

# def quality_inspection_on_cancel(doc, method):
#     if doc.reference_type != "Purchase Receipt":
#         return
#     filters = (
#         {"name": doc.child_row_reference} if doc.child_row_reference else {"parent": doc.reference_name, "item_code": doc.item_code}
#     )
#     rejected = doc.custom_rejected_qty or 0
#     if rejected <= 0:
#         frappe.db.set_value("Purchase Receipt Item", filters, {"custom_qi_before_purchase": 1})
#         return

#     row = frappe.db.get_value("Purchase Receipt Item", filters, ["received_qty", "rejected_qty"], as_dict=True)
#     if not row:
#         return

#     new_rejected = max((row.rejected_qty or 0) - rejected, 0)
#     new_qty = (row.received_qty or 0) - new_rejected

#     frappe.db.set_value("Purchase Receipt Item", filters, {"rejected_qty": new_rejected, "qty": new_qty})
#     frappe.db.set_value("Purchase Receipt Item", filters, {"custom_qi_before_purchase": 1})