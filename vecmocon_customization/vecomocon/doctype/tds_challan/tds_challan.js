// Copyright (c) 2026, MI_Cloud and contributors
// For license information, please see license.txt

frappe.ui.form.on("TDS Challan", {
	setup(frm) {
		// Set query filter for purchase_invoice in items child table
		frm.set_query('purchase_invoice', 'items', function() {
			return {
				filters: {
					'tax_withholding_category': frm.doc.tax_withholding_category,
                    'apply_tds': 1
				}
			};
		});
	},

	tax_withholding_category(frm) {
		// Clear items table when tax_withholding_category changes
		if (frm.doc.items && frm.doc.items.length > 0) {
			frm.clear_table('items');
			frm.refresh_field('items');
		}
	},
});

frappe.ui.form.on("TDS Challan Item", {
	purchase_invoice(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		
		if (row.purchase_invoice) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Purchase Invoice',
					name: row.purchase_invoice
				},
				callback: function(r) {
					if (r.message) {
						let doc = r.message;
						
						// Set supplier info
						frappe.model.set_value(cdt, cdn, 'supplier', doc.supplier);
						frappe.model.set_value(cdt, cdn, 'supplier_name', doc.supplier_name);
						frappe.model.set_value(cdt, cdn, 'invoice_amount', doc.total);
						frappe.model.set_value(cdt, cdn, 'tds_category', frm.doc.tax_withholding_category);
						
						// Find the TDS tax entry from the purchase invoice matching the tax_withholding_category
						let tds_amount = 0;
						let tds_rate = 0;
						if (doc.taxes && doc.taxes.length > 0 && doc.tax_withholding_category) {
							let tds_tax = doc.taxes.find(tax => tax.is_tax_withholding_account === 1 && tax.add_deduct_tax === "Deduct");
                            if (tds_tax) {
								tds_amount = tds_tax.tax_amount || 0;
								tds_rate = doc.total > 0 ? (tds_amount / doc.total * 100) : 0;
							}
						}
						frappe.model.set_value(cdt, cdn, 'tds_rate', tds_rate || 0);
						frappe.model.set_value(cdt, cdn, 'tds_amount', tds_amount || 0);
						frm.refresh_field('items');
					}
				}
			});
		}
	}
});