// Copyright (c) 2026, MI_Cloud and contributors
// For license information, please see license.txt

frappe.ui.form.on("Barcode Log", {
	refresh(frm) {
		if (frm.is_new()) return;

		frappe.call({
			method: 'vecmocon_customization.override.barcode_api.get_code_type_setting',
			async: false,
			callback: function (r) {
				frm._code_type = r.message || 'Barcode';
			}
		});

		let label = frm._code_type === 'QR Code' ? 'QR Code' : 'Barcode';

		frm.add_custom_button(__('View {0}', [label]), function () {
			frappe.call({
				method: 'vecmocon_customization.override.barcode_api.get_barcode_image',
				args: { barcode_string: frm.doc.barcode_string },
				callback: function (r) {
					if (r.message) {
						let d = new frappe.ui.Dialog({
							title: __(label),
							fields: [
								{
									fieldtype: 'HTML',
									options: `
										<div style="text-align:center; padding:15px;">
											<img src="${r.message}" style="max-width:450px; width:100%;">
											<p style="margin-top:12px;">
												<code style="font-size:12px; word-break:break-all;">
													${frm.doc.barcode_string}
												</code>
											</p>
										</div>
									`
								}
							],
							primary_action_label: __('Print'),
							primary_action: function () {
								d.hide();
								print_barcode_label(frm.doc, r.message);
							}
						});
						d.show();
					}
				}
			});
		});
	}
});

function print_barcode_label(doc, bc_src) {
	let w = window.open('', '_blank', 'height=500,width=700');
	w.document.write(`<!DOCTYPE html>
<html>
<head>
	<title>Label</title>
	<style>
		body { font-family: Arial, sans-serif; margin: 10mm; }
		.label {
			width: 120mm; border: 2px solid #000; padding: 6mm;
		}
		.barcode-area {
			text-align: center; margin-bottom: 4mm;
		}
		.barcode-area img { max-width: 110mm; height: auto; }
		.details {
			display: flex; flex-wrap: wrap; font-size: 9pt; gap: 1mm 10mm;
		}
		.details div { flex: 0 0 45%; }
		.details strong { display: inline-block; width: 18mm; }
		@media print { body { margin: 0; } .label { border: none; } }
	</style>
</head>
<body>
	<div class="label">
		<div class="barcode-area">
			<img src="${bc_src}">
		</div>
		<div class="details">
			<div><strong>Part:</strong> ${doc.part_code}</div>
			<div><strong>Batch:</strong> ${doc.batch_no}</div>
			<div><strong>Serial:</strong> ${doc.packet_serial}</div>
			<div><strong>Qty:</strong> ${doc.qty}</div>
			<div><strong>Mfg:</strong> ${doc.mfg_date}</div>
			<div><strong>Exp:</strong> ${doc.exp_date}</div>
		</div>
	</div>
	<script>window.print(); window.close();</script>
</body>
</html>`);
	w.document.close();
}
