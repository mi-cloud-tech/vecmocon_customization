frappe.ui.form.on("Journal Entry", {
    custom_business_unit: function(frm) {
        update_child_rows(frm);
    },

    custom_cost_center: function(frm) {
        update_child_rows(frm);
    },

    custom_location: function(frm) {
        update_child_rows(frm);
    }
});

function update_child_rows(frm) {
    (frm.doc.accounts || []).forEach(row => {
        row.business_unit = frm.doc.custom_business_unit;
        row.cost_center = frm.doc.custom_cost_center;
        row.location = frm.doc.custom_location;
    });

    frm.refresh_field("accounts");
}

frappe.ui.form.on("Journal Entry Account", {
    accounts_add: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        row.business_unit = frm.doc.custom_business_unit;
        row.cost_center = frm.doc.custom_cost_center;
        row.location = frm.doc.custom_location;

        frm.refresh_field("accounts");
    }
});