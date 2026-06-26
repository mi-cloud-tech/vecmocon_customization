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


def reset_rejected_to_draft(doc, method=None):
    """When a Purchase Order is rejected through the approval workflow, bounce
    it back to the 'Draft' state so the Purchase User can fix and resubmit it.
    The rejection reason (set client-side before the workflow action) is
    preserved so everyone can see it was previously rejected, by whom and why.
    """
    if doc.get("workflow_state") == "Rejected":
        # db_set updates both the in-memory value and the database without
        # re-triggering document events, so this won't recurse.
        doc.db_set("workflow_state", "Draft")