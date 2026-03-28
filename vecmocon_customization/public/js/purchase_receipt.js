frappe.ui.form.on('Purchase Receipt', {
	refresh(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button('Generate Barcode / QR', () => {

				frappe.set_route('app', 'barcode_generator', {
					purchase_receipt: frm.doc.name
				});

			}, 'Actions');
		}
	}
});