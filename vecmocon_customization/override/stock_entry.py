# Copyright (c) 2026, MI_Cloud and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt
from frappe.query_builder import DocType
from frappe.query_builder.functions import Sum
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry


class CustomStockEntry(StockEntry):
    """Custom Stock Entry class that overrides validate_subcontract_order method"""

    def validate_subcontract_order(self):
        """Override: Validate subcontract order for custom logic.
        
        Throw exception if more raw material is transferred against Subcontract Order than in
        the raw materials supplied table.
        """
        backflush_raw_materials_based_on = frappe.db.get_single_value(
            "Buying Settings", "backflush_raw_materials_of_subcontract_based_on"
        )

        qty_allowance = flt(frappe.db.get_single_value("Buying Settings", "over_transfer_allowance"))

        if not (self.purpose == "Send to Subcontractor" and self.get(self.subcontract_data.order_field)):
            return

        if backflush_raw_materials_based_on == "BOM":
            subcontract_order = frappe.get_doc(
                self.subcontract_data.order_doctype, self.get(self.subcontract_data.order_field)
            )
            for se_item in self.items:
                item_code = se_item.original_item or se_item.item_code
                precision = cint(frappe.db.get_default("float_precision")) or 3
                required_qty = sum(
                    [
                        flt(d.required_qty)
                        for d in subcontract_order.supplied_items
                        if d.rm_item_code == item_code
                    ]
                )
                custom_over_transfer_allowance = flt(frappe.get_value("Item", item_code, "custom_over_transfer_allowance"))
                if custom_over_transfer_allowance:
                    custom_qty_allowance = custom_over_transfer_allowance
                else:
                    custom_qty_allowance = qty_allowance
                total_allowed = required_qty + (required_qty * (custom_qty_allowance / 100)) 

                if not required_qty:
                    frappe.db.get_value(
                        f"{self.subcontract_data.order_doctype} Item",
                        {
                            "parent": self.get(self.subcontract_data.order_field),
                            "item_code": se_item.subcontracted_item,
                        },
                        "bom",
                    )

                    if se_item.allow_alternative_item:
                        original_item_code = frappe.get_value(
                            "Item Alternative", {"alternative_item_code": item_code}, "item_code"
                        )

                        required_qty = sum(
                            [
                                flt(d.required_qty)
                                for d in subcontract_order.supplied_items
                                if d.rm_item_code == original_item_code
                            ]
                        )
    
                        total_allowed = required_qty + (required_qty * (custom_qty_allowance / 100))

                if not required_qty:
                    frappe.throw(
                        _("Item {0} not found in 'Raw Materials Supplied' table in {1} {2}").format(
                            se_item.item_code,
                            self.subcontract_data.order_doctype,
                            self.get(self.subcontract_data.order_field),
                        )
                    )

                se = frappe.qb.DocType("Stock Entry")
                se_detail = frappe.qb.DocType("Stock Entry Detail")

                total_supplied = (
                    frappe.qb.from_(se)
                    .inner_join(se_detail)
                    .on(se.name == se_detail.parent)
                    .select(Sum(se_detail.transfer_qty))
                    .where(
                        (se.purpose == "Send to Subcontractor")
                        & (se.docstatus == 1)
                        & (se_detail.item_code == se_item.item_code)
                        & (
                            (
                                (se.purchase_order == self.purchase_order)
                                & (se_detail.po_detail == se_item.po_detail)
                            )
                            if self.subcontract_data.order_doctype == "Purchase Order"
                            else (
                                (se.subcontracting_order == self.subcontracting_order)
                                & (se_detail.sco_rm_detail == se_item.sco_rm_detail)
                            )
                        )
                    )
                ).run()[0][0] or 0

                total_returned = 0
                if self.subcontract_data.order_doctype == "Subcontracting Order":
                    total_returned = (
                        frappe.qb.from_(se)
                        .inner_join(se_detail)
                        .on(se.name == se_detail.parent)
                        .select(Sum(se_detail.transfer_qty))
                        .where(
                            (se.purpose == "Material Transfer")
                            & (se.docstatus == 1)
                            & (se.is_return == 1)
                            & (se_detail.item_code == se_item.item_code)
                            & (se_detail.sco_rm_detail == se_item.sco_rm_detail)
                            & (se.subcontracting_order == self.subcontracting_order)
                        )
                    ).run()[0][0] or 0

                if flt(total_supplied - total_returned, precision) > flt(total_allowed, precision):
                    frappe.throw(
                        _("Row {0}# Item {1} cannot be transferred more than {2} against {3} {4}").format(
                            se_item.idx,
                            se_item.item_code,
                            total_allowed,
                            self.subcontract_data.order_doctype,
                            self.get(self.subcontract_data.order_field),
                        )
                    )
                elif not se_item.get(self.subcontract_data.rm_detail_field):
                    filters = {
                        "parent": self.get(self.subcontract_data.order_field),
                        "docstatus": 1,
                        "rm_item_code": se_item.item_code,
                        "main_item_code": se_item.subcontracted_item,
                    }

                    order_rm_detail = frappe.db.get_value(
                        self.subcontract_data.order_supplied_items_field, filters, "name"
                    )
                    if order_rm_detail:
                        se_item.db_set(self.subcontract_data.rm_detail_field, order_rm_detail)
                    else:
                        if not se_item.allow_alternative_item:
                            frappe.throw(
                                _(
                                    "Row {0}# Item {1} not found in 'Raw Materials Supplied' table in {2} {3}"
                                ).format(
                                    se_item.idx,
                                    se_item.item_code,
                                    self.subcontract_data.order_doctype,
                                    self.get(self.subcontract_data.order_field),
                                )
                            )
        elif backflush_raw_materials_based_on == "Material Transferred for Subcontract":
            for row in self.items:
                if not row.subcontracted_item:
                    frappe.throw(
                        _("Row {0}: Subcontracted Item is mandatory for the raw material {1}").format(
                            row.idx, frappe.bold(row.item_code)
                        )
                    )
                elif not row.get(self.subcontract_data.rm_detail_field):
                    filters = {
                        "parent": self.get(self.subcontract_data.order_field),
                        "docstatus": 1,
                        "rm_item_code": row.item_code,
                        "main_item_code": row.subcontracted_item,
                    }

                    order_rm_detail = frappe.db.get_value(
                        self.subcontract_data.order_supplied_items_field, filters, "name"
                    )
                    if order_rm_detail:
                        row.db_set(self.subcontract_data.rm_detail_field, order_rm_detail)

@frappe.whitelist()
def stock_entry_before_submit(doc, method):
    """Before submit, validate subcontract order for custom logic."""
    if doc.purpose == "Send to Subcontractor":
        for item in doc.items:
            standard_packaging_qty = frappe.get_value("Item", item.item_code,'custom_standard_packaging')
            if standard_packaging_qty and item.transfer_qty % standard_packaging_qty != 0:
                frappe.throw(
                    _("Row {0}: Transfer quantity {1} for item {2} must be a multiple of standard packaging quantity {3}.").format(
                        item.idx, item.transfer_qty, item.item_code, standard_packaging_qty
                    )
                )