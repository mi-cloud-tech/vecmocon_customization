# Copyright (c) 2026, MI_Cloud and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class TDSChallan(Document):
	def validate(self):
		self.validate_duplicate_invoices()
		self.validate_paid_invoice_in_other_challan()
		self.calculate_total_tds()

	def validate_duplicate_invoices(self):
		"""Check for duplicate purchase invoices in items table."""
		if not self.items:
			return
		
		invoices = []
		for item in self.items:
			if item.purchase_invoice:
				if item.purchase_invoice in invoices:
					frappe.throw(
						_("Purchase Invoice {0} is already added in the items table.").format(
							frappe.bold(item.purchase_invoice)
						)
					)
				invoices.append(item.purchase_invoice)

	def validate_paid_invoice_in_other_challan(self):
		"""Check if invoice exists in another paid TDS Challan entry."""
		if not self.items:
			return
		
		for item in self.items:
			if item.purchase_invoice:
				# Check if this invoice exists in any other paid TDS Challan
				existing_challan = frappe.db.get_value(
					"TDS Challan Item",
					{
						"purchase_invoice": item.purchase_invoice,
						"parent": ("!=", self.name),
					},
					["parent"],
					as_dict=False
				)
				
				if existing_challan:
					# Check if that challan is paid
					challan_status = frappe.db.get_value(
						"TDS Challan",
						existing_challan,
						"status"
					)
					
					if challan_status == "Paid":
						frappe.throw(
							_("Purchase Invoice {0} already exists in paid TDS Challan {1}.").format(
								frappe.bold(item.purchase_invoice),
								frappe.bold(existing_challan)
							)
						)

	def calculate_total_tds(self):
		self.total_tds_amount = sum(flt(item.tds_amount) for item in self.items)

	def on_submit(self):
		if self.status == "Paid":
			self.create_journal_entry()

	def on_cancel(self):
		self.clear_journal_entry()

	def create_journal_entry(self):
		"""Create a Journal Entry for TDS payment."""
		if not self.total_tds_amount or self.total_tds_amount <= 0:
			frappe.throw(_("TDS Amount must be greater than 0 to create Journal Entry."))
		
		# Create new Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.posting_date = self.challan_date
		je.company = self.company
		je.tds_challan = self.name
		je.remarks = f"TDS Payment for Challan {self.name} - Challan No: {self.challan_no}"
		
		# Get TDS account from Tax Withholding Category
		tds_account = frappe.db.get_value("Tax Withholding Account", {'parent': self.tax_withholding_category, 'company': self.company}, "account")
		if not tds_account:
			frappe.throw(_("TDS Account not configured in Tax Withholding Category {0}").format(frappe.bold(self.tax_withholding_category)))
		
		# Get bank account
		bank_account = frappe.db.get_value("Bank Account", self.bank_name, "account")
		if not bank_account:
			frappe.throw(_("Bank Account not found for Bank {0} in Company {1}").format(frappe.bold(self.bank_name), frappe.bold(self.company)))
		
		cost_center = frappe.db.get_value("Company", self.company, "cost_center")
		je.append("accounts", {
			"account": tds_account,
			"debit_in_account_currency": self.total_tds_amount,
			"cost_center": cost_center,
			"description": f"TDS Payment - Challan {self.challan_no}"
		})
		
		je.append("accounts", {
			"account": bank_account,
			"credit_in_account_currency": self.total_tds_amount,
			"cost_center": cost_center,
			"description": f"TDS Payment - Challan {self.challan_no}"
		})
		
		je.insert()
		je.submit()
		self.journal_entry = je.name
		frappe.db.set_value("TDS Challan", self.name, "journal_entry", je.name)

	def clear_journal_entry(self):
		"""Cancel the associated Journal Entry."""
		if self.journal_entry:
			try:
				je = frappe.get_doc("Journal Entry", self.journal_entry)
				if je.docstatus == 0:
					je.delete()
				elif je.docstatus == 1:
					je.cancel()
				
				frappe.db.set_value("TDS Challan", self.name, "journal_entry", "")
			except frappe.DoesNotExistError:
				pass


@frappe.whitelist()
def get_tds_details_for_payment_entry(payment_entry):
	"""Fetch TDS details for each referenced invoice in a Payment Entry.

	TDS is deducted at the Purchase Invoice level. This function reads
	TDS from each invoice's taxes table where is_tax_withholding_account = 1.
	"""
	pe = frappe.get_doc("Payment Entry", payment_entry)

	if not pe.references:
		frappe.throw(_("No invoice references found in this Payment Entry."))

	tds_details = []

	for ref in pe.references:
		if ref.reference_doctype == "Purchase Invoice":
			invoice = frappe.get_doc("Purchase Invoice", ref.reference_name)

			# Find TDS tax row from invoice taxes
			tds_amount = 0
			tds_category = invoice.tax_withholding_category or ""

			for tax in invoice.taxes:
				if tax.is_tax_withholding_account:
					tds_amount = abs(flt(tax.tax_amount))
					break

			if tds_amount <= 0:
				continue

			# Get TDS rate from Tax Withholding Category based on posting date
			tds_rate = get_tds_rate(tds_category, invoice.posting_date)
			
			# Fallback: calculate rate from amount if category rate not found
			if not tds_rate and flt(invoice.base_tax_withholding_net_total):
				tds_rate = flt(
					tds_amount / flt(invoice.base_tax_withholding_net_total) * 100, 4
				)

			tds_details.append(
				{
					"purchase_invoice": invoice.name,
					"supplier": invoice.supplier,
					"supplier_name": invoice.supplier_name,
					"invoice_amount": flt(invoice.grand_total),
					"tds_category": tds_category,
					"tds_rate": tds_rate,
					"tds_amount": tds_amount,
				}
			)

	return tds_details

def get_tds_rate(tax_withholding_category, posting_date):
	"""Get TDS rate from Tax Withholding Category for the given posting date."""
	if not tax_withholding_category or not posting_date:
		return 0

	rate = frappe.db.get_value(
		"Tax Withholding Rate",
		{
			"parent": tax_withholding_category,
			"from_date": ("<=", posting_date),
			"to_date": (">=", posting_date),
		},
		"tax_withholding_rate",
	)

	return flt(rate)