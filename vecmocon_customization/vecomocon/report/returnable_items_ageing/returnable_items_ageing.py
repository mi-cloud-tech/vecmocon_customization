# Copyright (c) 2025, MI_Cloud and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = []

	today = frappe.utils.today()
	conditions = []
	values = {}

	# ---- Dynamic Conditions ----
	if filters.get("company"):
		conditions.append("dn.company = %(company)s")
		values["company"] = filters["company"]

	if filters.get("to_date"):
		conditions.append("dn.posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	if filters.get("customer"):
		conditions.append("dn.customer = %(customer)s")
		values["customer"] = filters["customer"]

	if filters.get("delivery_note"):
		conditions.append("dn.name = %(delivery_note)s")
		values["delivery_note"] = filters["delivery_note"]

	if filters.get("item_code"):
		conditions.append("dni.item_code = %(item_code)s")
		values["item_code"] = filters["item_code"]

	condition_str = " AND ".join(conditions)
	if condition_str:
		condition_str = " AND " + condition_str

	# ---- Delivery Note Fetch ----
	dn_items = frappe.db.sql(f"""
		SELECT
			dn.name AS delivery_note,
			dn.posting_date,
			dn.customer,
			dn.custom_return_in_days AS return_in_days,
			dni.item_code,
			dni.qty AS delivered_qty
		FROM `tabDelivery Note` dn
		JOIN `tabDelivery Note Item` dni ON dni.parent = dn.name
		WHERE
			dn.docstatus = 1
			AND dn.custom_is_returnable = 1
			AND dn.is_return = 0
			{condition_str}
	""", values, as_dict=1)

	# ---- Return + Ageing Calculation ----
	for row in dn_items:
		returned_qty = frappe.db.sql("""
			SELECT ABS(SUM(dni.qty))
			FROM `tabDelivery Note Item` dni
			JOIN `tabDelivery Note` dn ON dn.name = dni.parent
			WHERE
				dn.is_return = 1
				AND dn.return_against = %s
				AND dni.item_code = %s
				AND dn.docstatus = 1
		""", (row.delivery_note, row.item_code))[0][0] or 0

		pending_qty = row.delivered_qty - returned_qty

		if pending_qty <= 0:
			continue

		ageing_days = frappe.utils.date_diff(today, row.posting_date)

		data.append({
			"delivery_note": row.delivery_note,
			"customer": row.customer,
			"item_code": row.item_code,
			"delivered_qty": row.delivered_qty,
			"returned_qty": returned_qty,
			"pending_qty": pending_qty,
			"return_in_days": row.return_in_days,
			"ageing_days": ageing_days
		})

	return columns, data

def get_columns():
	return [
		{
			"label": "Delivery Note",
			"fieldname": "delivery_note",
			"fieldtype": "Link",
			"options": "Delivery Note",
			"width": 150
		},
		{
			"label": "Customer",
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 200
		},
		{
			"label": "Item Code",
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150
		},
		{
			"label": "Delivered Qty",
			"fieldname": "delivered_qty",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"label": "Returned Qty",
			"fieldname": "returned_qty",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"label": "Pending Qty",
			"fieldname": "pending_qty",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"label": "Return In Days",
			"fieldname": "return_in_days",
			"fieldtype": "Int",
			"width": 120
		},
		{
			"label": "Ageing (Days)",
			"fieldname": "ageing_days",
			"fieldtype": "Int",
			"width": 120
		}
	]