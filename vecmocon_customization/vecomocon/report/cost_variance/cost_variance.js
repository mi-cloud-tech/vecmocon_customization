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
			label: __("Subcontracting Order"),
			fieldname: "name",
			fieldtype: "Link",
			options: "Subcontracting Order",
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
		{
			label: __("BOM"),
			fieldname: "bom",
			fieldtype: "Link",
			options: "BOM",
			get_query: function () {
				const item = frappe.query_report.get_filter_value("production_item");
				return item ? { filters: { item: item } } : {};
			},
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		// Render Stock Entry / Subcontracting Receipt (one or many, comma-separated)
		// as clickable links to their forms.
		const doc_route = {
			stock_entry: "stock-entry",
			subcontracting_receipt: "subcontracting-receipt",
		};
		if (doc_route[column.fieldname] && data && data[column.fieldname]) {
			const route = doc_route[column.fieldname];
			return data[column.fieldname]
				.split(",")
				.map((n) => n.trim())
				.filter((n) => n)
				.map(
					(name) =>
						`<a href="/app/${route}/${encodeURIComponent(name)}">${frappe.utils.escape_html(
							name
						)}</a>`
				)
				.join(", ");
		}

		value = default_formatter(value, row, column, data);

		const variance_fields = ["qty_variance", "price_variance", "material_variance"];
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
