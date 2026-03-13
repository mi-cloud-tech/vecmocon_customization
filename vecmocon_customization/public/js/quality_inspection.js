frappe.ui.form.on("Quality Inspection", {
    refresh: function(frm) {

        if (
            frm.doc.docstatus === 1 &&
            frm.doc.status === "Rejected" &&
            !frm.doc.custom_rejected_status
        ) {

            frm.add_custom_button(__("Rejection Decision"), function() {

                let d = new frappe.ui.Dialog({
                    title: "Rejection Decision",
                    fields: [
                        {
                            label: "Rejected Status",
                            fieldname: "rejected_status",
                            fieldtype: "Select",
                            options: "Return to Vendor\nScrap",
                            reqd: 1
                        },
                        {
                            label: "Decision Date",
                            fieldname: "decision_date",
                            fieldtype: "Date",
                            default: frappe.datetime.get_today(),
                            reqd: 1
                        }
                    ],
                    primary_action_label: "Submit",
                    primary_action(values) {

                        frm.set_value("custom_rejected_status", values.rejected_status);
                        frm.set_value("custom_rejected_decision_date", values.decision_date);

                        d.hide();
                        frm.save();
                    }
                });

                d.show();
            });
        }
    }
});