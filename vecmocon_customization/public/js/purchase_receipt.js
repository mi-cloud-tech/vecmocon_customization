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

		build_po_item_map(frm);

		frm.set_query('item_code', 'items', function() {
			const item_codes = Object.keys(frm._po_item_map || {});
			if (item_codes.length) {
				return { filters: { name: ['in', item_codes] } };
			}
			return {};
		});
	}
});

frappe.ui.form.on('Purchase Receipt Item', {
	item_code(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const po = (frm._po_item_map || {})[row.item_code];
		if (row.item_code && po && !row.purchase_order) {
			frappe.model.set_value(cdt, cdn, 'purchase_order', po);
		}
	},
	purchase_order(frm) {
		build_po_item_map(frm);
	}
});

function build_po_item_map(frm) {
	frm._po_item_map = {};

	const purchase_orders = [
		...new Set((frm.doc.items || []).map(r => r.purchase_order).filter(Boolean))
	];
	if (!purchase_orders.length) return;

	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Purchase Order Item',
			parent: 'Purchase Order',
			filters: { parent: ['in', purchase_orders] },
			fields: ['item_code', 'parent'],
			limit_page_length: 0
		},
		callback(r) {
			(r.message || []).forEach(d => {
				frm._po_item_map[d.item_code] = d.parent;
			});
		}
	});
}
