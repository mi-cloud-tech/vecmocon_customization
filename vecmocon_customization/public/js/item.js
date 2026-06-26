frappe.ui.form.on("Item", {
    before_workflow_action: function(frm) {
        // Only intercept the "Reject" action of the Master Data approval workflow.
        if (frm.selected_workflow_action !== "Reject") {
            return;
        }

        // Frappe freezes (dims/blurs) the whole page before firing this hook and
        // only unfreezes after the action completes. Since we pause here to ask
        // for a reason, clear that freeze so the dialog is usable.
        frappe.dom.unfreeze();

        return new Promise((resolve, reject) => {
            let submitted = false;

            const d = new frappe.ui.Dialog({
                title: __("Rejection Reason"),
                fields: [
                    {
                        label: __("Reason for Rejection"),
                        fieldname: "reason",
                        fieldtype: "Small Text",
                        reqd: 1
                    }
                ],
                primary_action_label: __("Reject"),
                primary_action(values) {
                    submitted = true;

                    d.hide();

                    // Re-freeze so the workflow save shows a loading state;
                    // Frappe unfreezes again once the action finishes.
                    frappe.dom.freeze(__("Rejecting..."));

                    // Record the rejecting role (e.g. "COO"), which is the role
                    // allowed to perform the Reject transition from the current
                    // state, rather than the individual username.
                    frappe.xcall("frappe.model.workflow.get_transitions", { doc: frm.doc })
                        .then((transitions) => {
                            const reject_txn = (transitions || []).find((t) => t.action === "Reject");
                            const rejected_by = (reject_txn && reject_txn.allowed)
                                || frappe.session.user_fullname
                                || frappe.session.user;
                            const today = frappe.datetime.get_today();

                            // Store who (role) rejected, when and why in a single read-only field.
                            frm.set_value(
                                "custom_rejection_reason",
                                __("Rejected by {0} on {1}:\n{2}", [rejected_by, today, values.reason])
                            );

                            // apply_workflow() calls doc.load_from_db(), which discards any
                            // unsaved field changes. So persist the reason to the DB first,
                            // then let the workflow action proceed.
                            return frm.save();
                        })
                        .then(() => resolve())
                        .catch(() => {
                            frappe.dom.unfreeze();
                            reject();
                        });
                }
            });

            // If the dialog is dismissed without submitting, cancel the workflow
            // action (so the item is not rejected without a reason) and make sure
            // the page is not left frozen.
            d.onhide = () => {
                if (!submitted) {
                    frappe.dom.unfreeze();
                    reject();
                }
            };

            d.show();
        });
    }
});
