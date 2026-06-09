// Copyright (c) 2026, MI_Cloud and contributors
// For license information, please see license.txt

frappe.query_reports["Custom Stock Ledger"] = {
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
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "MultiSelectList",
			options: "Warehouse",
			get_data: function (txt) {
				const company = frappe.query_report.get_filter_value("company");
				return frappe.db.get_link_options("Warehouse", txt, {
					company: company,
				});
			},
		},
		{
			fieldname: "item_code",
			label: __("Item"),
			fieldtype: "MultiSelectList",
			options: "Item",
			get_data: async function (txt) {
				let { message: data } = await frappe.call({
					method: "erpnext.controllers.queries.item_query",
					args: {
						doctype: "Item",
						txt: txt,
						searchfield: "name",
						start: 0,
						page_len: 10,
						filters: {},
						as_dict: 1,
					},
				});
				return (data || []).map(({ name, ...rest }) => {
					return { value: name, description: Object.values(rest) };
				});
			},
		},
		{
			fieldname: "item_group",
			label: __("Category (Item Group)"),
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
			fieldname: "voucher_no",
			label: __("Document No"),
			fieldtype: "Data",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "valuation_field_type",
			label: __("Valuation Field Type"),
			fieldtype: "Select",
			options: "Currency\nFloat",
			default: "Currency",
			hidden: 1,
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		if (data && data.is_balance_row) {
			// Blank out the Unit Rate cell so it doesn't render as ₹ 0.00.
			if (column.fieldname == "unit_rate") {
				return "";
			}
			value = default_formatter(value, row, column, data);
			return "<span style='font-weight:bold'>" + value + "</span>";
		}
		value = default_formatter(value, row, column, data);
		if (column.fieldname == "actual_qty" && data && data.actual_qty < 0) {
			value = "<span style='color:red'>" + value + "</span>";
		} else if (column.fieldname == "actual_qty" && data && data.actual_qty > 0) {
			value = "<span style='color:green'>" + value + "</span>";
		}
		return value;
	},
};
