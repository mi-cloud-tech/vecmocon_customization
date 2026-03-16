frappe.pages['barcode_generator'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Barcode Generator',
		single_column: true
	});
	new BarcodeGeneratorPage(page);
};

class BarcodeGeneratorPage {
	constructor(page) {
		this.page = page;
		this.current_data = null;
		this.current_barcode_img = null;
		this.code_type = 'Barcode';
		this.fetch_code_type();
		this.make_form();
		this.make_result_area();
		this.setup_actions();
	}

	fetch_code_type() {
		frappe.call({
			method: 'vecmocon_customization.override.barcode_api.get_code_type_setting',
			async: false,
			callback: (r) => {
				if (r.message) {
					this.code_type = r.message;
				}
			}
		});
	}

	get_label() {
		return this.code_type === 'QR Code' ? 'QR Code' : 'Barcode';
	}

	make_form() {
		let me = this;
		this.form = new frappe.ui.FieldGroup({
			fields: [
				{
					fieldtype: 'Section Break',
					label: 'Product Information'
				},
				{
					fieldname: 'vendor_code',
					fieldtype: 'Data',
					label: 'Vendor Code (Supplier Part No)',
					reqd: 1,
					description: 'Max 8 characters (e.g., VS226001) — auto-fetches Part Code',
					maxlength: 8,
					change: function () {
						me.on_vendor_code_change();
					}
				},
				{ fieldtype: 'Column Break' },
				{
					fieldname: 'part_code',
					fieldtype: 'Link',
					options: 'Item',
					label: 'Part Code (Item Code)',
					reqd: 1,
					description: 'Filtered by Vendor Code'
				},
				{
					fieldtype: 'Section Break',
					label: 'Batch & Serial'
				},
				{
					fieldname: 'batch_no',
					fieldtype: 'Data',
					label: 'Batch Number',
					reqd: 1,
					description: 'Max 14 characters (e.g., 00020220115M02)',
					maxlength: 14
				},
				{ fieldtype: 'Column Break' },
				{
					fieldname: 'packet_serial',
					fieldtype: 'Data',
					label: 'Packet Serial No',
					reqd: 1,
					description: 'Max 7 characters (e.g., N1E0009)',
					maxlength: 7
				},
				{
					fieldtype: 'Section Break',
					label: 'Dates & Quantity'
				},
				{
					fieldname: 'mfg_date',
					fieldtype: 'Data',
					label: 'Manufacturing Date (YYMMDD)',
					reqd: 1,
					description: '6 digits (e.g., 220114)',
					maxlength: 6
				},
				{ fieldtype: 'Column Break' },
				{
					fieldname: 'exp_date',
					fieldtype: 'Data',
					label: 'Expiry Date (YYMMDD)',
					reqd: 1,
					description: '6 digits (e.g., 220414)',
					maxlength: 6
				},
				{ fieldtype: 'Section Break' },
				{
					fieldname: 'qty',
					fieldtype: 'Data',
					label: 'Quantity',
					reqd: 1,
					description: 'Up to 7 digits (e.g., 0000261)',
					maxlength: 7
				},
				{ fieldtype: 'Column Break' },
				{
					fieldname: 'constant_text',
					fieldtype: 'Data',
					label: 'Constant Text',
					reqd: 1,
					description: '1 alphabetic character (e.g., A)',
					maxlength: 1
				}
			],
			body: this.page.body
		});
		this.form.make();

		// Filter Part Code Link field by Vendor Code
		let part_field = this.form.fields_dict.part_code;
		if (part_field) {
			part_field.get_query = () => {
				let vendor = (this.form.get_value('vendor_code') || '').toUpperCase().trim();
				if (vendor) {
					return {
						query: 'vecmocon_customization.override.barcode_api.item_query_for_vendor',
						filters: { vendor_code: vendor }
					};
				}
				return {};
			};
		}
	}

	on_vendor_code_change() {
		let vendor = (this.form.get_value('vendor_code') || '').toUpperCase().trim();
		if (!vendor) return;

		// Clear previous part_code when vendor changes
		this.form.set_value('part_code', '');

		frappe.call({
			method: 'vecmocon_customization.override.barcode_api.get_items_for_vendor',
			args: { vendor_code: vendor },
			callback: (r) => {
				if (!r.message || !r.message.length) {
					frappe.show_alert({
						message: __('No items found for vendor {0}', [vendor]),
						indicator: 'orange'
					}, 5);
					return;
				}
				if (r.message.length === 1) {
					// Single item — auto-fill
					this.form.set_value('part_code', r.message[0].item_code);
					frappe.show_alert({
						message: __('Auto-selected: {0}', [r.message[0].item_code]),
						indicator: 'green'
					}, 3);
				} else {
					frappe.show_alert({
						message: __('Found {0} items for this vendor. Select from Part Code.', [r.message.length]),
						indicator: 'blue'
					}, 5);
				}
			}
		});
	}

	make_result_area() {
		this.$result = $(`
			<div class="barcode-result-section" style="display:none; margin-top:20px;
				background:#fff; border-radius:8px; padding:25px;
				box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
				<h5 class="result-title" style="border-bottom:2px solid #27ae60; padding-bottom:10px; color:#2c3e50;">
					Generated ${this.get_label()}
				</h5>
				<div style="display:flex; gap:40px; flex-wrap:wrap; align-items:flex-start;">
					<div style="text-align:center; background:#f5f5f5; border-radius:8px; padding:20px;">
						<img class="barcode-img" src="" alt="Barcode" style="max-width:450px; width:100%;">
					</div>
					<div style="flex:1; min-width:250px;">
						<div style="background:#f9f9f9; padding:15px; border-radius:4px;
							border-left:4px solid #27ae60;">
							<p style="margin:8px 0;"><strong>Barcode String:</strong></p>
							<code class="barcode-string" style="font-size:13px; word-break:break-all;
								background:#ecf0f1; padding:4px 8px; border-radius:3px;
								display:block; margin-bottom:10px;"></code>
							<p class="result-vendor" style="margin:4px 0;"></p>
							<p class="result-part" style="margin:4px 0;"></p>
							<p class="result-batch" style="margin:4px 0;"></p>
							<p class="result-serial" style="margin:4px 0;"></p>
							<p class="result-mfg" style="margin:4px 0;"></p>
							<p class="result-exp" style="margin:4px 0;"></p>
							<p class="result-qty" style="margin:4px 0;"></p>
						</div>
					</div>
				</div>
			</div>
		`).appendTo(this.page.body);
	}

	setup_actions() {
		let label = this.get_label();
		this.page.set_primary_action(
			__('Generate {0}', [label]),
			() => this.generate()
		);
		this.page.set_secondary_action(
			__('Clear'),
			() => this.clear_form()
		);
		this.page.add_inner_button(
			__('Save & Generate'),
			() => this.save_and_generate()
		);
		this.page.add_inner_button(
			__('Print Label'),
			() => this.print_label()
		);
	}

	collect_data() {
		let values = this.form.get_values();
		if (!values) return null;
		return {
			vendor_code: (values.vendor_code || '').toUpperCase().trim(),
			part_code: (values.part_code || '').toUpperCase().trim(),
			batch_no: (values.batch_no || '').toUpperCase().trim(),
			packet_serial: (values.packet_serial || '').toUpperCase().trim(),
			mfg_date: (values.mfg_date || '').trim(),
			exp_date: (values.exp_date || '').trim(),
			qty: (values.qty || '').trim(),
			constant_text: (values.constant_text || '').toUpperCase().trim()
		};
	}

	generate() {
		let data = this.collect_data();
		if (!data) return;

		frappe.call({
			method: 'vecmocon_customization.override.barcode_api.generate_barcode',
			args: { data },
			freeze: true,
			freeze_message: __('Generating {0}...', [this.get_label()]),
			callback: (r) => {
				if (r.message) {
					this.show_result(r.message.barcode_string, r.message.barcode_image, data);
					if (r.message.already_exists) {
						frappe.show_alert({
							message: __('{0} already exists ({1}). Showing for print.', [this.get_label(), r.message.barcode_log]),
							indicator: 'orange'
						}, 7);
					} else {
						frappe.show_alert({ message: __('{0} generated successfully', [this.get_label()]), indicator: 'green' });
					}
				}
			}
		});
	}

	save_and_generate() {
		let data = this.collect_data();
		if (!data) return;

		frappe.call({
			method: 'vecmocon_customization.override.barcode_api.save_barcode_log',
			args: { data },
			freeze: true,
			freeze_message: __('Saving {0} Log...', [this.get_label()]),
			callback: (r) => {
				if (r.message) {
					this.show_result(r.message.barcode_string, r.message.barcode_image, data);
					if (r.message.already_exists) {
						frappe.show_alert({
							message: __('{0} already exists ({1}). Showing for print.', [this.get_label(), r.message.barcode_log]),
							indicator: 'orange'
						}, 7);
					} else {
						frappe.show_alert({
							message: __('{0} saved as {1}', [this.get_label(), r.message.barcode_log]),
							indicator: 'green'
						});
					}
				}
			}
		});
	}

	show_result(barcode_string, barcode_image, data) {
		this.current_data = data;
		this.current_barcode_img = barcode_image;
		this.$result.find('.barcode-img').attr('src', barcode_image);
		this.$result.find('.barcode-string').text(barcode_string);
		this.$result.find('.result-vendor').html(`<strong>Vendor Code:</strong> ${data.vendor_code}`);
		this.$result.find('.result-part').html(`<strong>Part Code:</strong> ${data.part_code}`);
		this.$result.find('.result-batch').html(`<strong>Batch No:</strong> ${data.batch_no}`);
		this.$result.find('.result-serial').html(`<strong>Packet Serial:</strong> ${data.packet_serial}`);
		this.$result.find('.result-mfg').html(`<strong>Mfg Date:</strong> ${data.mfg_date}`);
		this.$result.find('.result-exp').html(`<strong>Exp Date:</strong> ${data.exp_date}`);
		this.$result.find('.result-qty').html(`<strong>Quantity:</strong> ${data.qty}`);
		this.$result.show();
	}

	clear_form() {
		this.form.clear();
		this.$result.hide();
		this.current_data = null;
		this.current_barcode_img = null;
	}

	print_label() {
		if (!this.current_data || !this.current_barcode_img) {
			frappe.msgprint(__('Please generate a {0} first', [this.get_label()]));
			return;
		}

		let barcode_string = this.$result.find('.barcode-string').text();
		let bc_src = this.current_barcode_img;
		let d = this.current_data;

		let w = window.open('', '_blank', 'height=500,width=700');
		w.document.write(`<!DOCTYPE html>
<html>
<head>
	<title>Barcode Label</title>
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
			<div><strong>Part:</strong> ${d.part_code}</div>
			<div><strong>Batch:</strong> ${d.batch_no}</div>
			<div><strong>Serial:</strong> ${d.packet_serial}</div>
			<div><strong>Qty:</strong> ${d.qty}</div>
			<div><strong>Mfg:</strong> ${d.mfg_date}</div>
			<div><strong>Exp:</strong> ${d.exp_date}</div>
		</div>
	</div>
	<script>window.print(); window.close();</script>
</body>
</html>`);
		w.document.close();
	}
}
