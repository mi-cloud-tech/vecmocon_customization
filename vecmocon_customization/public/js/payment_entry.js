
frappe.ui.form.on("Payment Entry", {
	refresh(frm) {
		// Only show button for submitted Payment Entries with supplier payments
		if (frm.doc.docstatus === 1 && frm.doc.party_type === "Supplier") {
			frm.add_custom_button(__("TDS Challan Entry"),
				function () {
					show_tds_challan_dialog(frm);
				},
				__("Actions")
			);
		}

		// Show linked TDS Challan info
		if (frm.doc.custom_tds_challan) {
			frm.dashboard.add_comment(
				__("TDS Challan: {0} | Challan No: {1} | Amount: {2}", [
					'<a href="/app/tds-challan/' +
						frm.doc.custom_tds_challan +
						'">' +
						frm.doc.custom_tds_challan +
						"</a>",
					frm.doc.custom_tds_challan_no || "-",
					format_currency(frm.doc.custom_tds_challan_amount || 0),
				]),
				"blue"
			);
		}
	},
});

// child table events for Payment Entry Reference
frappe.ui.form.on('Payment Entry Reference', {
    tds_amount(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row && row.tds_amount) {
            // allocate full outstanding so invoice closes
            row.allocated_amount = row.outstanding_amount;
            frm.refresh_field('references');
        }
    }
});

function show_tds_challan_dialog(frm) {
	frappe.call({
		method: "vecmocon_customization.vecomocon.doctype.tds_challan.tds_challan.get_tds_details_for_payment_entry",
		args: {
			payment_entry: frm.doc.name,
		},
		freeze: true,
		freeze_message: __("Fetching TDS details..."),
		callback: function (r) {
			if (!r.message || r.message.length === 0) {
				frappe.msgprint(
					__("No TDS found on the referenced invoices in this Payment Entry.")
				);
				return;
			}

			let tds_items = r.message;
			let total_tds = tds_items.reduce(
				(sum, item) => sum + (item.tds_amount || 0),
				0
			);

			// Build HTML table for displaying TDS details
			let table_html = build_tds_table_html(tds_items, total_tds);

			let d = new frappe.ui.Dialog({
				title: __("TDS Challan Entry"),
				size: "extra-large",
				fields: [
					{
						fieldname: "tds_details_html",
						fieldtype: "HTML",
						options: table_html,
					},
					{
						fieldtype: "Section Break",
						label: __("Challan Details"),
					},
					{
						fieldname: "challan_no",
						fieldtype: "Data",
						label: __("Challan Number"),
						reqd: 1,
					},
					{
						fieldname: "challan_date",
						fieldtype: "Date",
						label: __("Challan Date"),
						default: frappe.datetime.get_today(),
						reqd: 1,
					},
					{
						fieldname: "cb1",
						fieldtype: "Column Break",
					},
					{
						fieldname: "bsr_code",
						fieldtype: "Data",
						label: __("BSR Code"),
					},
					{
						fieldname: "bank_name",
						fieldtype: "Data",
						label: __("Bank Name"),
					},
					{
						fieldtype: "Section Break",
					},
					{
						fieldname: "remarks",
						fieldtype: "Small Text",
						label: __("Remarks"),
					},
				],
				primary_action_label: __("Create TDS Challan"),
				primary_action(values) {
					frappe.call({
						method: "frappe.client.insert",
						args: {
							doc: {
								doctype: "TDS Challan",
								challan_no: values.challan_no,
								challan_date: values.challan_date,
								bsr_code: values.bsr_code,
								bank_name: values.bank_name,
								company: frm.doc.company,
								payment_entry: frm.doc.name,
								remarks: values.remarks,
								items: tds_items.map(function (item) {
									return {
										purchase_invoice: item.purchase_invoice,
										supplier: item.supplier,
										supplier_name: item.supplier_name,
										invoice_amount: item.invoice_amount,
										tds_category: item.tds_category,
										tds_rate: item.tds_rate,
										tds_amount: item.tds_amount,
									};
								}),
							},
						},
						freeze: true,
						freeze_message: __("Creating TDS Challan..."),
						callback: function (r) {
							if (r.message) {
								d.hide();
								frappe.show_alert(
									{
										message: __(
											"TDS Challan {0} created successfully.",
											['<a href="/app/tds-challan/' + r.message.name + '">' + r.message.name + "</a>"]
										),
										indicator: "green",
									},
									10
								);
								frm.reload_doc();
							}
						},
					});
				},
			});

			d.show();
		},
	});
}

function build_tds_table_html(tds_items, total_tds) {
	let rows = tds_items
		.map(function (item) {
			return (
				"<tr>" +
				"<td>" + item.purchase_invoice + "</td>" +
				"<td>" + item.supplier + "</td>" +
				"<td>" + (item.supplier_name || "") + "</td>" +
				"<td class='text-right'>" + format_currency(item.invoice_amount) + "</td>" +
				"<td>" + (item.tds_category || "-") + "</td>" +
				"<td class='text-right'>" + (item.tds_rate || 0) + "%</td>" +
				"<td class='text-right' style='font-weight:bold;'>" + format_currency(item.tds_amount) + "</td>" +
				"</tr>"
			);
		})
		.join("");

	return (
		'<div style="max-height: 300px; overflow-y: auto;">' +
		'<table class="table table-bordered table-condensed" style="margin-bottom: 0;">' +
		"<thead>" +
		"<tr style='background-color: var(--bg-light-gray);'>" +
		"<th>" + __("Invoice") + "</th>" +
		"<th>" + __("Supplier") + "</th>" +
		"<th>" + __("Supplier Name") + "</th>" +
		"<th class='text-right'>" + __("Invoice Amount") + "</th>" +
		"<th>" + __("TDS Category") + "</th>" +
		"<th class='text-right'>" + __("TDS Rate") + "</th>" +
		"<th class='text-right'>" + __("TDS Amount") + "</th>" +
		"</tr>" +
		"</thead>" +
		"<tbody>" +
		rows +
		"</tbody>" +
		"<tfoot>" +
		"<tr style='background-color: var(--bg-light-gray); font-weight: bold;'>" +
		"<td colspan='6' class='text-right'>" + __("Total TDS Amount") + "</td>" +
		"<td class='text-right'>" + format_currency(total_tds) + "</td>" +
		"</tr>" +
		"</tfoot>" +
		"</table>" +
		"</div>"
	);
}