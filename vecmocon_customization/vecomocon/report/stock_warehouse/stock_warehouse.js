// Copyright (c) 2026, MI_Cloud and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Warehouse"] = {
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
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
			get_query: function () {
				const company = frappe.query_report.get_filter_value("company");
				return { filters: { company: company } };
			},
		},
		{
			fieldname: "item_code",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
		{
			fieldname: "brand",
			label: __("Brand"),
			fieldtype: "Link",
			options: "Brand",
		},
		{
			fieldname: "show_zero_stock",
			label: __("Show Zero Stock"),
			fieldtype: "Check",
			default: 0,
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) {
			return value;
		}

		// Highlight quality buckets so hold/rejected stock stands out.
		if (column.fieldname == "available_qty" && flt(data.available_qty) > 0) {
			value = "<span style='color:green;font-weight:bold'>" + value + "</span>";
		} else if (column.fieldname == "hold_qty" && flt(data.hold_qty) > 0) {
			value = "<span style='color:#e65100;font-weight:bold'>" + value + "</span>";
		} else if (column.fieldname == "rejected_qty" && flt(data.rejected_qty) > 0) {
			value = "<span style='color:red;font-weight:bold'>" + value + "</span>";
		}

		return value;
	},
};
