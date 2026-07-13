import frappe
from frappe import _

APPROVED_STATE = "Approved"

LINK_SEARCH_CMD = "frappe.desk.search.search_link"


def item_query_conditions(user=None, doctype=None):
  
    if frappe.form_dict.get("cmd") != LINK_SEARCH_CMD:
        return ""

    return f"`tabItem`.`workflow_state` = {frappe.db.escape(APPROVED_STATE)}"


def _collect_item_codes(doc):
    codes = set()

    def scan(d):
        for df in d.meta.get("fields", {"fieldtype": "Link", "options": "Item"}):
            code = d.get(df.fieldname)
            if code:
                codes.add(code)

    scan(doc)
    for table_df in doc.meta.get_table_fields():
        for row in (doc.get(table_df.fieldname) or []):
            scan(row)
    return codes


def validate_only_approved_items(doc, method=None):
    codes = _collect_item_codes(doc)
    if not codes:
        return

    state_by_item = {
        row.name: row.workflow_state
        for row in frappe.get_all(
            "Item",
            filters={"name": ("in", list(codes))},
            fields=["name", "workflow_state"],
        )
    }

    not_approved = {
        name: state
        for name, state in state_by_item.items()
        if state != APPROVED_STATE
    }
    if not_approved:
        lines = "".join(
            f"<li>{frappe.bold(name)} &mdash; {_('current status')}: {state or _('Draft')}</li>"
            for name, state in sorted(not_approved.items())
        )
        frappe.throw(
            _(
                "The following Item(s) have not been Approved and cannot be used"
                " in this document. Only Items whose workflow status is"
                " {0} can be used in any transaction:"
            ).format(frappe.bold(APPROVED_STATE))
            + f"<ul>{lines}</ul>",
            title=_("Item Not Approved"),
        )


def reset_rejected_to_draft(doc, method=None):
    """When an Item is rejected through the Master Data approval workflow,
    bounce it back to the 'Draft' state so the Purchase User can fix and
    resubmit it. The rejection reason (set client-side before the workflow
    action) is preserved so everyone can see it was previously rejected,
    by whom and why.
    """
    if doc.get("workflow_state") == "Rejected":
        # db_set updates both the in-memory value and the database without
        # re-triggering document events, so this won't recurse.
        doc.db_set("workflow_state", "Draft")
