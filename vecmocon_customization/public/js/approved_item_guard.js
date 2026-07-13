// Client-side guard: reject any Item that has not cleared the master-data
// approval workflow the MOMENT it is entered into a transaction, instead of
// waiting for the server `validate` to fire on save. This mirrors the
// authoritative server guard in
// vecmocon_customization/override/item.py (validate_only_approved_items) --
// the server remains the un-bypassable backstop; this is purely for instant UX.
//
// IMPORTANT: we must NOT clear a row's `item_code` to reject it. ERPNext's
// `get_item_details` returns `item_code` and writes it back into the row, so
// clearing it creates an endless ping-pong (clear -> ERPNext refetches & resets
// -> clear -> ...). Instead we REMOVE the whole grid row: frappe skips the
// detail writeback for a deleted row (see form.js "if child row is deleted,
// don't update"), which terminates the loop cleanly.
frappe.provide("vecmocon");

vecmocon.APPROVED_STATE = "Approved";

// Transaction child-table DocTypes whose `item_code` must reference an
// Approved Item. Registering a handler for a table that never appears on the
// current form is harmless, so a single shared file covers every transaction.
vecmocon.APPROVED_ITEM_CHILD_TABLES = [
    "Purchase Order Item",
    "Purchase Receipt Item",
    "Purchase Invoice Item",
    "Material Request Item",
    "Sales Order Item",
    "Sales Invoice Item",
    "Delivery Note Item",
    "Quotation Item",
    "Stock Entry Detail",
    "Stock Reconciliation Item",
    "BOM Item",
    "Subcontracting Order Item",
    "Subcontracting Order Service Item",
    "Subcontracting Receipt Item",
];

// Tracks (row + value) lookups already in flight so a single item entry never
// warns twice. ERPNext fires the `item_code` handler more than once per entry.
vecmocon._approval_checks_in_flight = {};

vecmocon.warn_item_not_approved = function (item_code, state) {
    frappe.msgprint({
        title: __("Item Not Approved"),
        indicator: "red",
        message: __(
            "Item {0} has workflow status {1}. Only Items with status {2} can be used in a transaction.",
            [
                frappe.utils.escape_html(item_code).bold(),
                (state || __("Draft")).bold(),
                vecmocon.APPROVED_STATE.bold(),
            ]
        ),
    });
};

// Resolve the workflow_state of `item_code`; runs `on_not_approved(state)` if it
// is anything other than Approved. De-duplicates rapid repeat triggers for the
// same field + value, and re-checks that the value is still present when the
// lookup returns (the row may have been removed/changed meanwhile).
vecmocon.check_item_approved = function (key, item_code, still_current, on_not_approved) {
    if (vecmocon._approval_checks_in_flight[key]) return;
    vecmocon._approval_checks_in_flight[key] = true;

    frappe.db
        .get_value("Item", item_code, "workflow_state")
        .then((r) => {
            if (!still_current()) return;
            const state = r && r.message ? r.message.workflow_state : null;
            if (state !== vecmocon.APPROVED_STATE) {
                on_not_approved(state);
            }
        })
        .always(() => {
            delete vecmocon._approval_checks_in_flight[key];
        });
};

// Guard for a child-table row: if the entered item is not Approved, remove the
// whole row (loop-proof) and warn once.
vecmocon.guard_child_item = function (frm, cdt, cdn) {
    const row = locals[cdt] && locals[cdt][cdn];
    if (!row || !row.item_code) return;

    const item_code = row.item_code;
    const key = [cdt, cdn, "item_code", item_code].join("::");

    vecmocon.check_item_approved(
        key,
        item_code,
        () => {
            const cur = locals[cdt] && locals[cdt][cdn];
            return cur && cur.item_code === item_code;
        },
        (state) => {
            const grid = frm.fields_dict[row.parentfield] && frm.fields_dict[row.parentfield].grid;
            const grid_row = grid && grid.grid_rows_by_docname && grid.grid_rows_by_docname[cdn];
            if (grid_row) {
                grid_row.remove();
            }
            vecmocon.warn_item_not_approved(item_code, state);
        }
    );
};

// Register the guard on every transaction child table's `item_code` field.
vecmocon.APPROVED_ITEM_CHILD_TABLES.forEach(function (child_doctype) {
    frappe.ui.form.on(child_doctype, {
        item_code: vecmocon.guard_child_item,
    });
});

// BOM also carries a parent-level `item` (the finished good being produced).
// It is not a grid row, so we cannot remove it -- warn instantly and let the
// server-side `validate` block the save.
frappe.ui.form.on("BOM", {
    item: function (frm) {
        const item_code = frm.doc.item;
        if (!item_code) return;

        const key = ["BOM", frm.doc.name || "new", "item", item_code].join("::");
        vecmocon.check_item_approved(
            key,
            item_code,
            () => frm.doc.item === item_code,
            (state) => vecmocon.warn_item_not_approved(item_code, state)
        );
    },
});
