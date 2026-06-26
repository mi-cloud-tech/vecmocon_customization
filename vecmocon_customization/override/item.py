import frappe


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
