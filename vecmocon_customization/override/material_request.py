import frappe

@frappe.whitelist()
def create_purchase_order_from_material_request(material_request):
    doc = frappe.get_doc("Material Request", material_request)
    suppliers = set()
    for item in doc.items:
        if not item.custom_supplier:
            frappe.throw(f"Supplier is required for item {item.item_code} in Material Request {material_request}")
        else:
            suppliers.add(item.custom_supplier)

    for s in suppliers:
        po = frappe.new_doc("Purchase Order")
        po.supplier = s
        po.material_request = material_request
        for item in doc.get("items", {"custom_supplier": s}):
            po.append("items", {
                "item_code": item.item_code,
                "qty": item.qty,
                "uom": item.uom,
                "schedule_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
                "material_request": material_request,
                "material_request_item": item.name
            })
        po.insert()
    return "Purchase Orders created successfully for all suppliers."

@frappe.whitelist()
def get_allowed_suppliers(item_code):
    suppliers = frappe.db.get_list("Party Specific Item", filters={"restrict_based_on": "Item", "party_type": "Supplier", "based_on_value": item_code}, pluck="party")
    return suppliers

@frappe.whitelist()
def has_purchase_orders(material_request):
    """Return True if any Purchase Order (draft or submitted) exists for this Material Request."""
    exists = frappe.db.exists("Purchase Order Item",{"material_request": material_request, "docstatus": ["in", [0, 1]]},)
    return bool(exists)

@frappe.whitelist()
def material_request_on_update_after_submit(doc, method):
    po = frappe.db.get_value("Purchase Order Item",{"material_request": doc.name, "docstatus": ["in", [0, 1]]}, 'parent')
    if po:
        frappe.throw(
            f"Material Request {doc.name} cannot be updated as it is linked to Purchase Order {po}. "
            "Please update the Purchase Order instead."
        )