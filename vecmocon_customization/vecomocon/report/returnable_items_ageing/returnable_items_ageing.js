// Copyright (c) 2025, MI_Cloud and contributors
// For license information, please see license.txt

frappe.query_reports["Returnable Items Ageing"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Delivery Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname": "item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "delivery_note",
			"label": __("Delivery Note"),
			"fieldtype": "Link",
			"options": "Delivery Note"
		},
	]
};
