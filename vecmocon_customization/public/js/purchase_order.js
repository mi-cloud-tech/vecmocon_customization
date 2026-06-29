// Shared helper that renders the stored plain-text rejection history into a
// nicely formatted set of cards. Defined idempotently so Item and Purchase
// Order form scripts can both reuse it.
frappe.provide("vecmocon.rejection");

vecmocon.rejection.render = function(frm, fieldname) {
    const field = frm.fields_dict[fieldname];
    if (!field) return;

    // Remove any previously rendered block so refreshes don't stack up.
    field.$wrapper.find(".rejection-history-pretty").remove();

    const raw = (frm.doc[fieldname] || "").trim();
    const default_display = field.$wrapper.find(".control-input-wrapper, .control-value");

    if (!raw) {
        default_display.show();
        return;
    }

    // Hide the default plain-text display and show our formatted version.
    default_display.hide();

    const entries = raw
        .split(/\n*-{3,}\n*/)
        .map((block) => block.trim())
        .filter(Boolean)
        .map((block) => {
            const m = block.match(/^Rejected by (.+?) on (\d{4}-\d{2}-\d{2}):\s*([\s\S]*)$/);
            return m
                ? { role: m[1], date: m[2], reason: m[3].trim() }
                : { role: null, date: null, reason: block };
        });

    const cards = entries
        .map((e, i) => {
            const is_latest = i === entries.length - 1;
            const role = frappe.utils.escape_html(e.role || __("Unknown"));
            const date_str = e.date ? frappe.datetime.str_to_user(e.date) : "";
            const reason = frappe.utils.escape_html(e.reason || "").replace(/\n/g, "<br>");
            const latest_tag = is_latest
                ? ` <span style="font-size:10px; font-weight:500; color:var(--text-muted);">(${__("Latest")})</span>`
                : "";

            return `
                <div style="border:1px solid var(--border-color); border-left:3px solid var(--red-500, #e24c4c);
                            border-radius:var(--border-radius-md, 6px); padding:8px 12px; margin-bottom:8px;
                            background:var(--card-bg, var(--fg-color, #fff));">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-weight:600; color:var(--red-600, #c0392b);">
                            <i class="fa fa-times-circle" style="margin-right:4px;"></i>${role}${latest_tag}
                        </span>
                        <span style="font-size:11px; color:var(--text-muted);">${date_str}</span>
                    </div>
                    <div style="color:var(--text-color); white-space:pre-wrap;">${reason}</div>
                </div>`;
        })
        .join("");

    field.$wrapper.append(`<div class="rejection-history-pretty" style="margin-top:4px;">${cards}</div>`);
};

frappe.ui.form.on("Purchase Order", {
    refresh: function(frm) {
        vecmocon.rejection.render(frm, "custom_reject_reason");
    },

    before_workflow_action: function(frm) {
        // Only intercept the "Reject" action of the PO approval workflow.
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

                            // Append to the existing history (if any) so every
                            // rejection is preserved, not just the latest one.
                            const entry = __("Rejected by {0} on {1}:\n{2}", [rejected_by, today, values.reason]);
                            const existing = (frm.doc.custom_reject_reason || "").trim();
                            const history = existing
                                ? existing + "\n\n--------------------------------\n\n" + entry
                                : entry;

                            // Store the full rejection history in a single read-only field.
                            frm.set_value("custom_reject_reason", history);

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
            // action (so the PO is not rejected without a reason) and make sure
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
