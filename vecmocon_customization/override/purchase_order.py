import frappe

def purchase_order_before_save(doc, method):
    for i in doc.items:
        if i.price_list_rate and i.rate != i.price_list_rate:
            frappe.throw(
                f"Rate for item {i.item_code} does not match the Price List Rate."
            )