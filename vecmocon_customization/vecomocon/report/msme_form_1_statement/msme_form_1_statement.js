// Copyright (c) 2026, MI_Cloud and contributors
// For license information, please see license.txt

frappe.query_reports["MSME Form 1 Statement"] = {
    "filters": [

        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "reqd": 1
        },

        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
			"reqd": 1
        },
		{
			fieldname: "supplier",
			label: "Supplier",
			fieldtype: "MultiSelectList",
			options: "Supplier",

			get_data: function(txt) {
				return frappe.db.get_link_options("Supplier", txt, {
					custom_msme_no: ["is", "set"]
				});
			}
		}
    ]
};
