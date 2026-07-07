// Copyright (c) 2026, MI_Cloud and contributors
// For license information, please see license.txt

frappe.query_reports["Cost Variance"] = {
	filters: [
		{
			label: __("Company"),
			fieldname: "company",
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			label: __("From Date"),
			fieldname: "from_date",
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
			label: __("Subcontracting Receipt"),
			fieldname: "name",
			fieldtype: "Link",
			options: "Subcontracting Receipt",
			get_query: function () {
				return { filters: { docstatus: 1 } };
			},
		},
		{
			label: __("Supplier"),
			fieldname: "supplier",
			fieldtype: "Link",
			options: "Supplier",
		},
		{
			label: __("Finished Good"),
			fieldname: "production_item",
			fieldtype: "Link",
			options: "Item",
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		const variance_fields = ["qty_variance", "rate_variance", "total_variance"];
		if (variance_fields.includes(column.fieldname) && data) {
			const raw = data[column.fieldname];
			if (raw < 0) {
				value = `<span style="color:red">${value}</span>`;
			} else if (raw > 0) {
				value = `<span style="color:green">${value}</span>`;
			}
		}

		return value;
	},
};
