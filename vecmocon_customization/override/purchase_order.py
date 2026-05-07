import frappe

def purchase_order_before_save(doc, method):
    seen_items = set()

    for i in doc.items:
        if i.price_list_rate and i.rate != i.price_list_rate:
            frappe.throw(
                f"Rate for item {i.item_code} does not match the Price List Rate."
            )

        if i.item_code in seen_items:
            frappe.throw(
                f"Duplicate item {i.item_code} is not allowed in the same Purchase Order (Row {i.idx})."
            )

        seen_items.add(i.item_code)

    if doc.billing_address:
        doc.letter_head = frappe.db.get_value("Address", doc.billing_address, "custom_letter_head") or doc.letter_head