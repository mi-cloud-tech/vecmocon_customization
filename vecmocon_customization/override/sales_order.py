import frappe

def incoterm_customization_before_submit(self, method):
    if self.incoterm:
        default_incoterm = frappe.get_doc("Customer", self.customer).custom_default_incoterm
        if not default_incoterm:
            frappe.set_value("Customer", self.customer, "custom_default_incoterm", self.incoterm)

def incoterm_customization_before_insert(self, method):
    if not self.incoterm:
        default_incoterm = frappe.get_doc("Customer", self.customer).custom_default_incoterm
        if default_incoterm:
            self.incoterm = default_incoterm

def custom_before_save(doc, method):
    if doc.company_address:
        doc.letter_head = frappe.db.get_value("Address", doc.company_address, "custom_letter_head") or doc.letter_head