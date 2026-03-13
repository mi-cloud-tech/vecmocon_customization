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

	# Enrich each data row with voucher details
	for row in data:
		voucher_type = row.get("voucher_type")
		voucher_no = row.get("voucher_no")
		if voucher_type and voucher_no:
			key = (voucher_type, voucher_no)
			details = voucher_details.get(key, {})
			row["voucher_created_by"] = details.get("owner", "")
			row["voucher_created_on"] = details.get("creation", "")
			row["voucher_submitted_by"] = details.get("submitted_by", "")
		else:
			# Opening / Total / Closing rows - leave blank
			row["voucher_created_by"] = ""
			row["voucher_created_on"] = ""
			row["voucher_submitted_by"] = ""

	return columns, data


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