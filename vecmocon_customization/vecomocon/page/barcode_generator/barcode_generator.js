frappe.pages['barcode_generator'].on_page_load = function(wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Barcode Generator',
		single_column: true
	});
	new BarcodeGeneratorPage(page);
};

class BarcodeGeneratorPage {
	constructor(page) {
		this.page = page;
		this.current_data = [];

		this.make_form();
		this.make_result_area();
		this.setup_actions();
	}

	// ================= FORM =================
	make_form() {
		let me = this;

		this.form = new frappe.ui.FieldGroup({
			fields: [
				{ fieldtype: 'Section Break', label: 'Purchase Receipt' },
				{
					fieldname: 'purchase_receipt',
					fieldtype: 'Link',
					options: 'Purchase Receipt',
					label: 'Purchase Receipt',
					change: () => me.fetch_pr_items()
				},

				{ fieldtype: 'Section Break', label: 'Items' },

				{
					fieldname: 'items',
					fieldtype: 'Table',
					label: 'Items',
					cannot_add_rows: true,
					in_place_edit: true,
					fields: [
						{ fieldname: 'purchase_order', fieldtype: 'Data', label: 'Purchase Order', in_list_view: 1, read_only: 1 },
						{ fieldname: 'purchase_order_date', fieldtype: 'Date', label: 'PO Date', in_list_view: 1, read_only: 1 },
						{ fieldname: 'purchase_receipt', fieldtype: 'Data', label: 'Purchase Receipt', in_list_view: 1, read_only: 1 },
						{ fieldname: 'purchase_receipt_date', fieldtype: 'Date', label: 'PR Date', in_list_view: 1, read_only: 1 },
						{ fieldname: 'vendor_name', fieldtype: 'Data', label: 'Vendor Name', in_list_view: 1, read_only: 1 },
						{ fieldname: 'column_break_111', fieldtype: 'Column Break', in_list_view: 1, columns:1 },
						{ fieldname: 'vendor_part_code', fieldtype: 'Data', label: 'Supplier Part Code', in_list_view: 1, read_only: 1 },
						{ fieldname: 'part_code', fieldtype: 'Data', label: 'Part Code', in_list_view: 1, read_only: 1 },
						{ fieldname: 'mpn', fieldtype: 'Data', label: 'MPN', in_list_view: 1, read_only: 1 },
						{ fieldname: 'batch_no', fieldtype: 'Data', label: 'Batch', in_list_view: 1 },
						{ fieldname: 'vendor_batch_no', fieldtype: 'Data', label: 'Vendor Batch', in_list_view: 1 },
						{ fieldname: 'column_break_111', fieldtype: 'Column Break', in_list_view: 1, columns:1 },
						{ fieldname: 'mfg_date', fieldtype: 'Data', label: 'Mfg Date', in_list_view: 1 },
						{ fieldname: 'exp_date', fieldtype: 'Data', label: 'Exp Date', in_list_view: 1 },
						{ fieldname: 'qty', fieldtype: 'Data', label: 'Qty', in_list_view: 1 },
						{ fieldname: 'constant_text', fieldtype: 'Data', label: 'Const', in_list_view: 1 }
					]
				}
			],
			body: this.page.body
		});

		this.form.make();
	}

	// ================= FETCH PR =================
	fetch_pr_items() {
		let pr = this.form.get_value('purchase_receipt');
		if (!pr) return;

		frappe.call({
			method: 'vecmocon_customization.override.barcode_api.get_pr_items_with_details',
			args: { pr },
			callback: (r) => {
				let grid = this.form.fields_dict.items.grid;

				grid.df.data = (r.message || []).map(d => ({
					purchase_order: d.purchase_order,
					purchase_order_date: d.purchase_order_date,
					purchase_receipt: d.purchase_receipt,
					purchase_receipt_date: d.purchase_receipt_date,
					vendor_name: d.vendor_name,
					vendor_part_code: d.vendor_part_code, 
					part_code: d.part_code,
					mpn: d.mpn,
					batch_no: d.batch_no,
					vendor_batch_no: d.vendor_batch_no,
					mfg_date: d.mfg_date,
					exp_date: d.exp_date,
					qty: d.qty,
					constant_text: d.constant_text || 'A'
				}));

				grid.refresh();
			}
		});
	}

	// ================= ACTIONS =================
	setup_actions() {
		this.page.set_primary_action('Generate', () => this.generate());
		this.page.set_secondary_action('Clear', () => this.clear());
		this.page.add_inner_button('Save & Generate', () => this.save_and_generate());
		this.page.add_inner_button('Print', () => this.print_labels());
	}

	collect_data() {
		let rows = this.form.fields_dict.items.grid.get_data();

		if (!rows.length) {
			frappe.msgprint('No items found');
			return null;
		}

		return rows;
	}

	// ================= GENERATE =================
	generate() {
		let data = this.collect_data();
		if (!data) return;

		frappe.call({
			method: 'vecmocon_customization.override.barcode_api.generate_barcode_bulk',
			args: { data },
			freeze: true,
			freeze_message: "Generating Barcodes...",
			callback: (r) => {
				this.current_data = r.message || [];
				this.show_result();
			}
		});
	}

	save_and_generate() {
		let data = this.collect_data();
		let pr = this.form.get_value('purchase_receipt');

		if (!data || !pr) {
			frappe.msgprint('Missing data or Purchase Receipt');
			return;
		}

		frappe.call({
			method: 'vecmocon_customization.override.barcode_api.save_barcode_bulk',
			args: { data, purchase_receipt: pr },
			freeze: true,
			callback: (r) => {
				this.current_data = r.message || [];
				this.show_result();

				frappe.show_alert({
					message: 'Barcodes Saved Successfully',
					indicator: 'green'
				});
			}
		});
	}

	// ================= RESULT AREA =================
	make_result_area() {
		this.$result = $(`
			<div style="margin-top:20px;">
				<h4>Generated Labels</h4>
				<div class="barcode-container" 
					style="display:flex; flex-wrap:wrap; gap:15px;">
				</div>
			</div>
		`).appendTo(this.page.body);
	}

	// ================= SHOW RESULT =================
	show_result() {
		let container = this.$result.find('.barcode-container');
		container.empty();

		(this.current_data || []).forEach(d => {
			let entries = Object.entries(d.labels || {}).filter(([k, v]) => v);
			let col1 = "";
			let col2 = "";
			entries.forEach(([key, val], index) => {
				let row = `<div><b>${key}:</b> ${val}</div>`;
				if (index % 2 === 0) {
					col1 += row;
				} else {
					col2 += row;
				}
			});

			let card = $(`
				<div style="border:1px solid #000; padding:10px;">
					<div style="width:650px; background:#fff; font-size:12px; display:flex; justify-content:space-between; align-items:center; gap:10px;">
						<div style="display:flex; gap:10px; align-items:center; ">
							<div style="flex:0 0 70%;">${col1}</div>
							<div style="flex:0 0 70%;">${col2}</div>
							<div style="flex:0 0 60%; text-align:center;"><img src="${d.barcode_image}" style="max-width:100%; max-height:100px;" /></div>
						</div>
					</div>
					<div style="margin-top:6px; font-family:monospace; font-size:12px; text-align:center; word-break:break-all;"><b>${d.barcode_string || ""}</b></div>
				</div>
			`);

			container.append(card);
		});
	}

	// ================= PRINT =================
	print_labels() {
		let w = window.open('', '_blank');

		let html = `
		<html>
		<head>
			<title>Print Labels</title>
			<style>
				body { font-family: Arial, sans-serif; }
				.label {
					border:1px solid #000;
					padding:10px;
					margin-bottom:15px;
					width:650px;
				}
				.row {
					display:flex;
					gap:10px;
					align-items:center;
				}
				.col {
					flex:0 0 40%;
					font-size:12px;
				}
				.img-col {
					flex:1;
					text-align:center;
				}
				.barcode {
					margin-top:6px;
					font-family:monospace;
					font-size:12px;
					text-align:center;
					word-break:break-all;
				}
			</style>
		</head>
		<body>
		`;

		(this.current_data || []).forEach(d => {

			let entries = Object.entries(d.labels || {}).filter(([k, v]) => v);

			let col1 = "";
			let col2 = "";

			// Split labels into 2 columns
			entries.forEach(([key, val], index) => {
				let row = `<div><b>${key}:</b> ${val}</div>`;
				if (index % 2 === 0) {
					col1 += row;
				} else {
					col2 += row;
				}
			});

			html += `
				<div class="label">
					<div class="row">
						<div class="col">${col1}</div>
						<div class="col">${col2}</div>
						<div class="img-col">
							<img src="${d.barcode_image}" style="max-width:100%; max-height:100px;" />
						</div>
					</div>

					<div class="barcode">
						<b>${d.barcode_string || ""}</b>
					</div>
				</div>
			`;
		});

		html += `
			<script>
				window.onload = function() {
					window.print();
				}
			</script>
		</body>
		</html>
		`;

		w.document.write(html);
		w.document.close();
	}
	// ================= CLEAR =================
	clear() {
		this.form.clear();
		this.$result.find('.barcode-container').empty();
	}
}