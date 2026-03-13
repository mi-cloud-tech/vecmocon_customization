import frappe, regex

def vehicle_number_regex(self, method):
    vehicle_number_pattern = r'^[A-Z]{2}\s?[0-9]{1,2}\s?[A-Z]{1,2}\s?[0-9]{4}$'
    if self.vehicle_no:
        if not regex.match(vehicle_number_pattern, self.vehicle_no):
            frappe.throw("Invalid Vehicle Number format. Please enter a valid format (e.g., 'AB 12 CD 3456').")

def custom_on_submit(self, method):
    if not self.custom_proof_of_delivery:
        self.custom_pod_status = "Shipped"

def on_update_after_submit(self, method):
    if self.custom_pod_status == "Delivered" and not self.custom_proof_of_delivery:
        frappe.throw("Proof of Delivery is required when the POD Status is 'Delivered'.")

    if self.custom_proof_of_delivery:
        self.custom_pod_status = "Delivered"