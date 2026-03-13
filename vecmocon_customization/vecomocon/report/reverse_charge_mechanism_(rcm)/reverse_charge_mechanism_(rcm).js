// Copyright (c) 2026, MI_Cloud and contributors
// For license information, please see license.txt

frappe.query_reports["Reverse Charge Mechanism (RCM)"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "MultiSelectList",
			options: "Supplier",
			get_data: function(txt) {
				return frappe.db.get_link_options("Supplier", txt, {
					is_reverse_charge_applicable: 1,
				});
			}
		},
		{
			fieldname: "gst_category",
			label: __("GST Category"),
			fieldtype: "Select",
			options: [
				"",
				"Registered Regular",
				"Registered Composition",
				"Unregistered",
				"SEZ",
				"Overseas",
				"Deemed Export",
				"UIN Holders",
			],
		},
		{
			fieldname: "place_of_supply",
			label: __("Place of Supply"),
			fieldtype: "Data",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "total_tax" && data && data.total_tax > 50000) {
			value = `<span style="color: red; font-weight: bold;">${value}</span>`;
		}

		if (column.fieldname === "gst_category" && data && data.gst_category === "Unregistered") {
			value = `<span style="color: orange; font-weight: bold;">${value}</span>`;
		}

		return value;
	},

	onload: function (report) {
		report.page.add_inner_button(__("Export for GSTR-3B"), function () {
			frappe.msgprint(__("Export functionality for GSTR-3B integration"));
		});
	},
};
