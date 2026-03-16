/**
 * Barcode / QR Code Scanner for ERPNext Documents
 *
 * Two-layer approach:
 * 1. Server-side: override_whitelisted_methods in hooks.py overrides
 *    erpnext.stock.utils.scan_barcode so our format is always recognized.
 * 2. Client-side: overrides BarcodeScanner.process_scan to set correct
 *    qty and supplier (which ERPNext's default handler doesn't do).
 *
 * Custom format: {vendor}/{part}/{batch}/{serial}/{mfg}/{exp}/{qty}/{constant}
 * Example: VS226001/FG-00001/00020220115M02/N1E0009/220114/220414/0000261/A
 */
(function () {
	'use strict';

	const PURCHASE_DOCTYPES = [
		'Purchase Receipt',
		'Purchase Order',
		'Purchase Invoice'
	];

	function is_custom_barcode(value) {
		return value && value.includes('/') && value.split('/').length === 8;
	}

	/**
	 * Apply prototype override on erpnext.utils.BarcodeScanner.
	 * Retries until ERPNext is loaded.
	 */
	function apply_override() {
		if (typeof erpnext === 'undefined' || !erpnext.utils || !erpnext.utils.BarcodeScanner) {
			setTimeout(apply_override, 300);
			return;
		}

		if (erpnext.utils.BarcodeScanner.__vecmocon_patched) return;
		erpnext.utils.BarcodeScanner.__vecmocon_patched = true;

		const _original_process_scan = erpnext.utils.BarcodeScanner.prototype.process_scan;

		erpnext.utils.BarcodeScanner.prototype.process_scan = function () {
			const input = this.scan_barcode_field
				? (this.scan_barcode_field.value || '').trim()
				: '';

			// Not our format — let ERPNext handle it normally
			if (!is_custom_barcode(input)) {
				return _original_process_scan.call(this);
			}

			// Our custom format — handle it ourselves
			this.scan_barcode_field.set_value('');

			const me = this;
			return new Promise((resolve, reject) => {
				frappe.call({
					method: 'erpnext.stock.utils.scan_barcode',
					args: { search_value: input },
					callback: function (r) {
						const data = r && r.message;
						if (!data || !data.item_code) {
							me.show_alert(__('Could not process scanned code'), 'red');
							me.clean_up();
							reject();
							return;
						}

						// Set supplier on purchase documents first
						if (PURCHASE_DOCTYPES.includes(me.frm.doctype) && data.supplier && !me.frm.doc.supplier) {
							me.frm.set_value('supplier', data.supplier).then(() => {
								add_scanned_row(me, data, resolve, reject);
							});
						} else {
							add_scanned_row(me, data, resolve, reject);
						}
					}
				});
			});
		};
	}

	/**
	 * Add item row directly — sets item_code, then after item details load,
	 * sets qty, batch_no, and serial_no reliably.
	 */
	function add_scanned_row(scanner, data, resolve, reject) {
		frappe.flags.hide_serial_batch_dialog = true;
		frappe.flags.trigger_from_barcode_scanner = true;

		let frm = scanner.frm;
		let child_table = scanner.items_table_name || 'items';
		let row = frm.add_child(child_table);

		// Set item_code first — triggers ERPNext's item detail fetch (rate, UOM, etc.)
		frappe.model.set_value(row.doctype, row.name, 'item_code', data.item_code);
		frm.refresh_field(child_table);

		// Wait for async item-detail fetch, then set remaining fields
		setTimeout(function () {
			let updates = {
				qty: data.qty || 1
			};
			if (data.batch_no) {
				updates.batch_no = data.batch_no;
			}
			if (data.serial_no) {
				updates.serial_no = data.serial_no;
			}

			frappe.model.set_value(row.doctype, row.name, updates);
			frm.refresh_field(child_table);

			frappe.show_alert({
				message: __('Scanned: {0} | Qty: {1} | Batch: {2}', [
					data.item_code,
					data.qty || 1,
					data.batch_no || '-'
				]),
				indicator: 'green'
			}, 7);

			frappe.flags.hide_serial_batch_dialog = false;
			frappe.flags.trigger_from_barcode_scanner = false;
			resolve(row);
		}, 1500);
	}

	// Start trying to apply the override
	apply_override();
})();
