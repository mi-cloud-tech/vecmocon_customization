frappe.ui.form.on('Purchase Receipt', {
	refresh(frm) {
		frm.set_query('purchase_order', 'items', function(doc, cdt, cdn) {
			return {
				filters: {
					docstatus: 1,
					supplier: doc.supplier,
					status: ['not in', ['Closed', 'Completed']]
				}
			};
		});
	}
});