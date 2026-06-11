# Copyright (c) 2026, MI_Cloud and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from erpnext.accounts.report.general_ledger.general_ledger import execute as standard_gl_execute


def execute(filters=None):
	if not filters:
		return [], []

	# Run the standard General Ledger report to get full data
	# (with Opening, Closing, Totals, categorize_by, balance, etc.)
	columns, data = standard_gl_execute(filters)

	# Add custom voucher columns after the standard columns
	custom_columns = [
		{
			"label": _("GL Created By"),
			"fieldname": "gl_created_by",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Voucher Created By"),
			"fieldname": "voucher_created_by",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Voucher Created On"),
			"fieldname": "voucher_created_on",
			"fieldtype": "Datetime",
			"width": 160,
		},
		{
			"label": _("Voucher Submitted By"),
			"fieldname": "voucher_submitted_by",
			"fieldtype": "Data",
			"width": 180,
		},
		{"label": _("Sales Order Number"), "fieldname": "so_number", "fieldtype": "Data", "width": 160},
		{"label": _("Sales Order Date"), "fieldname": "so_date", "fieldtype": "Date", "width": 120},
		{"label": _("CN Number"), "fieldname": "cn_number", "fieldtype": "Data", "width": 160},
		{"label": _("CN Date"), "fieldname": "cn_date", "fieldtype": "Date", "width": 120},
		{"label": _("Purchase Order Number"), "fieldname": "po_number", "fieldtype": "Data", "width": 160},
		{"label": _("Purchase Order Date"), "fieldname": "po_date", "fieldtype": "Date", "width": 120},
		{"label": _("Purchase Receipt Number"), "fieldname": "pr_number", "fieldtype": "Data", "width": 160},
		{"label": _("Purchase Receipt Date"), "fieldname": "pr_date", "fieldtype": "Date", "width": 120},
		{"label": _("DN Number"), "fieldname": "dn_number", "fieldtype": "Data", "width": 160},
		{"label": _("DN Date"), "fieldname": "dn_date", "fieldtype": "Date", "width": 120},
	]
	columns.extend(custom_columns)

	if not data:
		return columns, data

	# Collect unique voucher_type + voucher_no combinations from data rows
	voucher_map = {}
	for row in data:
		voucher_type = row.get("voucher_type")
		voucher_no = row.get("voucher_no")
		if voucher_type and voucher_no:
			key = (voucher_type, voucher_no)
			if key not in voucher_map:
				voucher_map[key] = None

	# Fetch voucher details (owner, creation, submitted_by)
	voucher_details = get_voucher_details(voucher_map)

	gl_owners = get_gl_entry_owners(voucher_map)
	owner_full_names = get_user_full_names(gl_owners.values())

	reference_details = get_reference_details(voucher_map)

	reference_fields = (
		"so_number",
		"so_date",
		"cn_number",
		"cn_date",
		"po_number",
		"po_date",
		"pr_number",
		"pr_date",
		"dn_number",
		"dn_date",
	)

	# Enrich each data row with voucher details
	for row in data:
		voucher_type = row.get("voucher_type")
		voucher_no = row.get("voucher_no")
		if voucher_type and voucher_no:
			key = (voucher_type, voucher_no)
			details = voucher_details.get(key, {})
			gl_owner = gl_owners.get(key, "")
			row["gl_created_by"] = owner_full_names.get(gl_owner, gl_owner)
			row["voucher_created_by"] = details.get("owner", "")
			row["voucher_created_on"] = details.get("creation", "")
			row["voucher_submitted_by"] = details.get("submitted_by", "")

			refs = reference_details.get(key, {})
			for field in reference_fields:
				row[field] = refs.get(field, "")
		else:
			# Opening / Total / Closing rows - leave blank
			row["gl_created_by"] = ""
			row["voucher_created_by"] = ""
			row["voucher_created_on"] = ""
			row["voucher_submitted_by"] = ""
			for field in reference_fields:
				row[field] = ""

	return columns, data


def get_reference_details(voucher_map):
	if not voucher_map:
		return {}

	# Group voucher numbers by type for batched queries.
	type_vouchers = {}
	for voucher_type, voucher_no in voucher_map:
		type_vouchers.setdefault(voucher_type, []).append(voucher_no)

	# voucher key -> {ref_kind: set(linked names)}
	links = {}

	def add_link(key, ref_kind, name):
		if name:
			links.setdefault(key, {}).setdefault(ref_kind, set()).add(name)

	# --- Sales Order links ---
	for parent, so in get_child_links(type_vouchers.get("Sales Invoice"), "Sales Invoice Item", "sales_order"):
		add_link(("Sales Invoice", parent), "so", so)
	for parent, so in get_child_links(type_vouchers.get("Delivery Note"), "Delivery Note Item", "against_sales_order"):
		add_link(("Delivery Note", parent), "so", so)
	for so in type_vouchers.get("Sales Order", []):
		add_link(("Sales Order", so), "so", so)

	# --- Purchase Order links ---
	for parent, po in get_child_links(type_vouchers.get("Purchase Invoice"), "Purchase Invoice Item", "purchase_order"):
		add_link(("Purchase Invoice", parent), "po", po)
	for parent, po in get_child_links(type_vouchers.get("Purchase Receipt"), "Purchase Receipt Item", "purchase_order"):
		add_link(("Purchase Receipt", parent), "po", po)
	for po in type_vouchers.get("Purchase Order", []):
		add_link(("Purchase Order", po), "po", po)

	# --- Purchase Receipt links ---
	for pr in type_vouchers.get("Purchase Receipt", []):
		add_link(("Purchase Receipt", pr), "pr", pr)
	for parent, pr in get_child_links(type_vouchers.get("Purchase Invoice"), "Purchase Invoice Item", "purchase_receipt"):
		add_link(("Purchase Invoice", parent), "pr", pr)

	# --- Delivery Note links ---
	for dn in type_vouchers.get("Delivery Note", []):
		add_link(("Delivery Note", dn), "dn", dn)
	for parent, dn in get_child_links(type_vouchers.get("Sales Invoice"), "Sales Invoice Item", "delivery_note"):
		add_link(("Sales Invoice", parent), "dn", dn)

	# Collect all referenced documents per type so dates can be fetched in bulk.
	names_by_doctype = {}
	for ref_links in links.values():
		for ref_kind, names in ref_links.items():
			doctype = REFERENCE_DOCTYPE[ref_kind]
			names_by_doctype.setdefault(doctype, set()).update(names)

	dates = {}
	for doctype, names in names_by_doctype.items():
		date_field = REFERENCE_DATE_FIELD[doctype]
		dates[doctype] = get_document_dates(doctype, names, date_field)

	# Credit Notes: Sales Invoices that are returns.
	cn_dates = get_credit_note_dates(type_vouchers.get("Sales Invoice"))

	details = {}
	for key, ref_links in links.items():
		row_details = {}
		for ref_kind, names in ref_links.items():
			doctype = REFERENCE_DOCTYPE[ref_kind]
			ordered = sorted(names)
			doc_dates = dates.get(doctype, {})
			distinct_dates = sorted({doc_dates[n] for n in ordered if doc_dates.get(n)})
			row_details[f"{ref_kind}_number"] = ", ".join(ordered)
			row_details[f"{ref_kind}_date"] = distinct_dates[0] if len(distinct_dates) == 1 else ""
		details[key] = row_details

	# Overlay Credit Note details (keyed on the Sales Invoice itself).
	for key, cn in cn_dates.items():
		details.setdefault(key, {})
		details[key]["cn_number"] = cn["cn_number"]
		details[key]["cn_date"] = cn["cn_date"]

	return details


REFERENCE_DOCTYPE = {
	"so": "Sales Order",
	"po": "Purchase Order",
	"pr": "Purchase Receipt",
	"dn": "Delivery Note",
}

REFERENCE_DATE_FIELD = {
	"Sales Order": "transaction_date",
	"Purchase Order": "transaction_date",
	"Purchase Receipt": "posting_date",
	"Delivery Note": "posting_date",
}


def get_child_links(parents, child_doctype, field):
	if not parents:
		return

	rows = frappe.db.sql(
		"""
		SELECT parent, {field} AS value
		FROM `tab{child}`
		WHERE parent IN %(parents)s
			AND IFNULL({field}, '') != ''
	""".format(child=child_doctype, field=field),
		{"parents": parents},
		as_dict=1,
	)
	for r in rows:
		yield r.parent, r.value


def get_document_dates(doctype, names, date_field):
	names = list({n for n in names if n})
	if not names:
		return {}

	rows = frappe.db.sql(
		"""
		SELECT name, {date_field} AS doc_date
		FROM `tab{doctype}`
		WHERE name IN %(names)s
	""".format(doctype=doctype, date_field=date_field),
		{"names": names},
		as_dict=1,
	)
	return {r.name: r.doc_date for r in rows}


def get_credit_note_dates(si_vouchers):
	"""A Credit Note is a Sales Invoice with is_return = 1."""
	if not si_vouchers:
		return {}

	rows = frappe.db.sql(
		"""
		SELECT name, posting_date
		FROM `tabSales Invoice`
		WHERE name IN %(names)s
			AND is_return = 1
	""",
		{"names": si_vouchers},
		as_dict=1,
	)
	return {
		("Sales Invoice", r.name): {"cn_number": r.name, "cn_date": r.posting_date}
		for r in rows
	}


def get_voucher_details(voucher_map):
	"""Fetch owner, creation, and submitted_by for each voucher.

	Groups vouchers by type to minimize database queries.
	For submitted documents (docstatus=1), the user who submitted is
	determined from the Version log (docstatus change 0 -> 1).
	"""
	if not voucher_map:
		return {}

	# Group voucher numbers by voucher type
	type_vouchers = {}
	for voucher_type, voucher_no in voucher_map:
		type_vouchers.setdefault(voucher_type, []).append(voucher_no)

	voucher_details = {}

	for voucher_type, voucher_nos in type_vouchers.items():
		try:
			if not frappe.db.exists("DocType", voucher_type):
				continue

			meta = frappe.get_meta(voucher_type)
			is_submittable = meta.is_submittable

			if is_submittable:
				results = frappe.db.sql(
					"""
					SELECT
						name,
						owner,
						creation,
						modified_by,
						docstatus
					FROM `tab{doctype}`
					WHERE name IN %(voucher_nos)s
				""".format(
						doctype=voucher_type
					),
					{"voucher_nos": voucher_nos},
					as_dict=1,
				)

				for r in results:
					submitted_by = ""
					if r.docstatus == 1:
						version_submitted_by = get_submitted_by_from_version(
							voucher_type, r.name
						)
						submitted_by = version_submitted_by or r.modified_by

					voucher_details[(voucher_type, r.name)] = {
						"owner": r.owner,
						"creation": r.creation,
						"submitted_by": submitted_by,
					}
			else:
				results = frappe.db.sql(
					"""
					SELECT
						name,
						owner,
						creation
					FROM `tab{doctype}`
					WHERE name IN %(voucher_nos)s
				""".format(
						doctype=voucher_type
					),
					{"voucher_nos": voucher_nos},
					as_dict=1,
				)

				for r in results:
					voucher_details[(voucher_type, r.name)] = {
						"owner": r.owner,
						"creation": r.creation,
						"submitted_by": "",
					}

		except Exception:
			continue

	return voucher_details


def get_gl_entry_owners(voucher_map):
	if not voucher_map:
		return {}

	# Group voucher numbers by voucher type
	type_vouchers = {}
	for voucher_type, voucher_no in voucher_map:
		type_vouchers.setdefault(voucher_type, []).append(voucher_no)

	owners = {}

	for voucher_type, voucher_nos in type_vouchers.items():
		try:
			results = frappe.db.sql(
				"""
				SELECT voucher_type, voucher_no, owner
				FROM `tabGL Entry`
				WHERE voucher_type = %(voucher_type)s
					AND voucher_no IN %(voucher_nos)s
			""",
				{"voucher_type": voucher_type, "voucher_nos": voucher_nos},
				as_dict=1,
			)

			for r in results:
				key = (r.voucher_type, r.voucher_no)
				if key not in owners:
					owners[key] = r.owner

		except Exception:
			continue

	return owners


def get_user_full_names(users):
	"""Return a mapping of user id (email) -> full name.

	Falls back to the user id itself when no full name is set.
	"""
	users = list({u for u in users if u})
	if not users:
		return {}

	results = frappe.db.sql(
		"""
		SELECT name, full_name
		FROM `tabUser`
		WHERE name IN %(users)s
	""",
		{"users": users},
		as_dict=1,
	)

	return {r.name: (r.full_name or r.name) for r in results}


def get_submitted_by_from_version(doctype, docname):
	"""Get the user who submitted the document from Version log.

	When a document is submitted, Frappe creates a Version entry tracking
	the docstatus change from 0 to 1. The owner of that Version entry
	is the user who performed the submission.
	"""
	version = frappe.db.sql(
		"""
		SELECT owner
		FROM `tabVersion`
		WHERE ref_doctype = %(doctype)s
			AND docname = %(docname)s
			AND data LIKE %(pattern)s
		ORDER BY creation ASC
		LIMIT 1
	""",
		{
			"doctype": doctype,
			"docname": docname,
			"pattern": '%"changed":%"docstatus"%[0, 1]%',
		},
		as_dict=1,
	)

	if version:
		return version[0].owner

	return ""