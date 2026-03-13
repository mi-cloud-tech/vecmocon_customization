// Copyright (c) 2026, MI_Cloud and contributors
// For license information, please see license.txt

frappe.query_reports["Challan Wise TDS Registor"] = {
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
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
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
			fieldname: "status",
			label: __("Payment Status"),
			fieldtype: "Select",
			options: ["", "Unpaid", "Paid"],
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
		},
		{
			fieldname: "payment_entry",
			label: __("Payment Entry"),
			fieldtype: "Link",
			options: "Payment Entry",
		},
		{
			fieldname: "tax_withholding_category",
			label: __("TDS Category"),
			fieldtype: "Link",
			options: "Tax Withholding Category",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "status" && data) {
			if (data.status === "Paid") {
				value =
					'<span style="color: green; font-weight: bold;">' +
					value +
					"</span>";
			} else if (data.status === "Unpaid") {
				value =
					'<span style="color: red; font-weight: bold;">' +
					value +
					"</span>";
			}
		}

		return value;
	},
};
