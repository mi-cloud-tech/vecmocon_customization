// Copyright (c) 2026, MI_Cloud and contributors
// For license information, please see license.txt

frappe.query_reports["Expiry Status"] = {
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
			fieldname: "as_on_date",
			label: __("As On Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
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
			get_query: function () {
				return { filters: { has_batch_no: 1 } };
			},
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
			fieldname: "batch_no",
			label: __("Batch"),
			fieldtype: "Link",
			options: "Batch",
		},
		{
			fieldname: "expiry_status",
			label: __("Expiry Status"),
			fieldtype: "Select",
			options: ["All", "Valid", "Expires Today", "Expired", "No Expiry"].join("\n"),
			default: "All",
		},
		{
			fieldname: "expiring_within",
			label: __("Expiring Within (Days)"),
			fieldtype: "Int",
		},
		{
			fieldname: "show_zero_stock",
			label: __("Show Zero Stock Batches"),
			fieldtype: "Check",
			default: 0,
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) {
			return value;
		}

		const highlight =
			column.fieldname == "status" ||
			column.fieldname == "expiry_date" ||
			column.fieldname == "remaining_shelf_life";

		if (highlight) {
			if (data.status == "Expired") {
				value = "<span style='color:red;font-weight:bold'>" + value + "</span>";
			} else if (data.status == "Expires Today") {
				value = "<span style='color:#e65100;font-weight:bold'>" + value + "</span>";
			}
		}

		return value;
	},
};
