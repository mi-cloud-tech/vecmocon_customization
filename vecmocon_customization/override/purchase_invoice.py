import frappe
from frappe.utils import getdate

def purchase_invoice_before_save(self, method):
    date = None
    pr = self.get("items",{"purchase_receipt": ["!=", ""]})
    if len(pr) > 1:
        frappe.throw("Multiple Purchase Receipts are not allowed in a single Purchase Invoice.")

    for item in self.items:
        if item.purchase_receipt:
            date = frappe.get_value("Purchase Receipt", item.purchase_receipt, "posting_date")
            break
    
    if date and getdate(self.posting_date) < getdate(date):
        frappe.throw("Purchase Invoice posting date cannot be earlier than the linked Purchase Receipt posting date.")

    if date:
        self.custom_purchase_receipt_date = date