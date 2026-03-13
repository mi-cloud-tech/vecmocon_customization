frappe.ui.form.on("Company", {
    refresh: function (frm) {

        // TDS Receivable Account filter
        frm.set_query("custom_default_tds_receivable_account", function () {
            return {
                filters: {
                    is_group: 0,
                    company: frm.doc.name
                }
            };
        });

        // Quality Warehouse filter
        frm.set_query("custom_default_quality_warehouse", function () {
            return {
                filters: {
                    is_group: 0,
                    company: frm.doc.name,
                    custom_is_quality_warehouse: 1
                }
            };
        });

    }
});