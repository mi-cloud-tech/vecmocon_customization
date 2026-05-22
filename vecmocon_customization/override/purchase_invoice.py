import frappe
from frappe.utils import getdate


def purchase_invoice_before_save(self, method):

    pr_list = set()
    pr_date = None

    # Collect unique Purchase Receipts
    for item in self.items:
        if item.purchase_receipt:
            pr_list.add(item.purchase_receipt)

    # Prevent multiple Purchase Receipts
    if len(pr_list) > 1:
        frappe.throw(
            "Multiple Purchase Receipts are not allowed in a single Purchase Invoice."
        )

    # Get Purchase Receipt date
    if pr_list:
        purchase_receipt = list(pr_list)[0]

        pr_date = frappe.db.get_value(
            "Purchase Receipt",
            purchase_receipt,
            "posting_date"
        )

    # Validate Purchase Invoice date
    if pr_date and getdate(self.posting_date) < getdate(pr_date):
        frappe.throw(
            "Purchase Invoice posting date cannot be earlier than the linked Purchase Receipt posting date."
        )

    # Store PR date in custom field
    if pr_date:
        self.custom_purchase_receipt_date = pr_date