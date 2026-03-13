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