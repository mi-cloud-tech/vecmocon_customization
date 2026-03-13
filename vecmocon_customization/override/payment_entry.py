import frappe
from frappe import _
from frappe.utils import flt

def payment_entry_before_save(doc, method):
    if doc.party_type != "Customer":
        return

    for ref in doc.get("references") or []:
        if ref.get("custom_tds_amount") and not ref.get("custom_tds_account"):
            default_tds_account = frappe.get_value("Company", doc.company, "custom_default_tds_receivable_account")
            if not default_tds_account:
                frappe.throw(_("Please set a default TDS Receivable Account in Company settings."))
            ref.custom_tds_account = default_tds_account

def validate_payment_entry(doc, method):
    """Ensure invoice allocation covers outstanding when TDS is provided."""
    if doc.party_type == "Customer":
        for ref in doc.get("references") or []:
            tds = flt(ref.get("custom_tds_amount"))
            if tds and (flt(ref.get("allocated_amount")) + tds) > flt(ref.get("outstanding_amount")):
                frappe.throw(_(f"Allocated amount for {ref.reference_doctype} {ref.reference_name} exceeds outstanding amount when TDS is provided."))

def on_submit(doc, method):
    """Create ONE consolidated Journal Entry for TDS"""

    if doc.party_type != "Customer":
        return

    tds_receivable_acc = frappe.get_value("Company", doc.company, "custom_default_tds_receivable_account")
    if not tds_receivable_acc:
        frappe.throw(_("Please set a TDS Receivable Account in Company settings."))

    total_tds = 0
    tds_rows = []

    for ref in doc.get("references") or []:
        tds_amt = flt(ref.get("custom_tds_amount"))
        if not tds_amt:
            continue

        total_tds += tds_amt
        tds_rows.append({
            "reference_doctype": ref.reference_doctype,
            "reference_name": ref.reference_name,
            "debtors_account": ref.account,
            "amount": tds_amt
        })

    if total_tds > 0:
        je_name = create_single_tds_journal_entry(doc, total_tds, tds_receivable_acc, tds_rows)
        doc.db_set("custom_tds_journal_entry", je_name)

def create_single_tds_journal_entry(doc, total_tds, tds_receivable_acc, tds_rows):
    """Create one consolidated Journal Entry"""

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.posting_date = doc.posting_date
    je.company = doc.company
    je.remark = f"Consolidated TDS for Payment Entry {doc.name}"

    # 1️⃣ Debit Total TDS
    je.append("accounts", {
        "account": tds_receivable_acc,
        "debit_in_account_currency": total_tds,
        "debit": total_tds,
    })

    # 2️⃣ Credit Debtors per Invoice
    for row in tds_rows:
        je.append("accounts", {
            "account": row["debtors_account"],
            "party_type": "Customer",
            "party": doc.party,
            "credit_in_account_currency": row["amount"],
            "credit": row["amount"],
            "reference_type": row["reference_doctype"],
            "reference_name": row["reference_name"],
        })

    je.flags.ignore_permissions = True
    je.insert()
    je.submit()

    return je.name

def on_cancel(doc, method):
    """Cancel consolidated TDS Journal Entry"""

    if doc.party_type != "Customer":
        return

    je_name = doc.get("custom_tds_journal_entry")

    if not je_name:
        return

    if frappe.db.exists("Journal Entry", je_name):
        je = frappe.get_doc("Journal Entry", je_name)
        if je.docstatus == 1:
            je.cancel()

    doc.db_set("custom_tds_journal_entry", None)