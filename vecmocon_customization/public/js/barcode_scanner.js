// Client Script for Barcode Scanning in Stock Documents
// This script intercepts barcode scans and parses the custom format

/**
 * Barcode Format: VS226001/VECESR001/00020220115M02/N1E0009/220114/220414/0000261/A
 * 
 * Fields:
 * - vendor_code: 8 digits (index 0)
 * - part_code: 10 chars (index 1)
 * - batch_no: 14 chars (index 2)
 * - packet_serial: 7 chars (index 3)
 * - mfg_date: 6 digits YYMMDD (index 4)
 * - exp_date: 6 digits YYMMDD (index 5)
 * - qty: 7 digits (index 6)
 * - constant_text: 1 char (index 7)
 */

// Apply to Purchase Receipt
frappe.ui.form.on('Purchase Receipt', {
	onload: function(frm) {
		setupBarcodeScanning(frm);
	}
});

// Apply to Stock Entry
frappe.ui.form.on('Stock Entry', {
	onload: function(frm) {
		setupBarcodeScanning(frm);
	}
});

// Apply to Delivery Note
frappe.ui.form.on('Delivery Note', {
	onload: function(frm) {
		setupBarcodeScanning(frm);
	}
});

/**
 * Setup barcode scanning for the form
 */
function setupBarcodeScanning(frm) {
	const tableName = getTableName(frm.doctype);
	if (!tableName) return;

	// Create a hidden input to capture barcode scans
	if (!frm.custom_barcode_scanner) {
		const barcodeInputId = `barcode_scanner_${frm.doctype}`;
		if (!document.getElementById(barcodeInputId)) {
			const input = $(`<input type="hidden" id="${barcodeInputId}" />`);
			$(frm.wrapper).append(input);
			frm.custom_barcode_scanner = input;
		}

		// Listen for barcode input
		$(document).on('keydown', function(e) {
			// Only capture if form is active
			if (!frm.get_active_tab) return;

			// Ctrl+B or Cmd+B to start barcode input
			if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
				e.preventDefault();
				startBarcodeInput(frm);
			}
		});
	}
}

/**
 * Get table name based on DocType
 */
function getTableName(doctype) {
	const tableMap = {
		'Purchase Receipt': 'items',
		'Stock Entry': 'items',
		'Delivery Note': 'items'
	};
	return tableMap[doctype];
}

/**
 * Start barcode input capture
 */
function startBarcodeInput(frm) {
	const dialog = new frappe.ui.Dialog({
		title: 'Scan Barcode',
		fields: [
			{
				fieldname: 'barcode_input',
				fieldtype: 'Data',
				label: 'Barcode',
				reqd: 1,
				placeholder: 'Scan barcode here...'
			}
		],
		primary_action_label: 'Process',
		primary_action(values) {
			processBarcodeInput(frm, values.barcode_input);
			dialog.hide();
		},
		secondary_action() {
			dialog.hide();
		}
	});

	dialog.show();

	// Focus on the input field for immediate scanning
	dialog.get_field('barcode_input').input.focus();

	// Also allow Enter key to submit
	dialog.get_field('barcode_input').input.addEventListener('keypress', function(e) {
		if (e.key === 'Enter') {
			dialog.get_primary_btn().click();
		}
	});
}

/**
 * Process scanned barcode
 */
function processBarcodeInput(frm, barcodeString) {
	// Check if it's our custom format (contains '/')
	if (!barcodeString.includes('/')) {
		frappe.msgprint({
			title: 'Info',
			message: 'Standard barcode detected. Using standard scanning.',
			indicator: 'blue'
		});
		return;
	}

	// Parse the barcode
	const parsedData = parseBarcodeString(barcodeString);

	if (parsedData.error) {
		frappe.msgprint({
			title: 'Error',
			message: parsedData.error,
			indicator: 'red'
		});
		return;
	}

	// Call backend to get additional info
	frappe.call({
		method: 'barcode_management.api.barcode_api.scan_barcode',
		args: {
			barcode_string: barcodeString
		},
		callback: function(r) {
			if (r.message && r.message.status === 'success') {
				populateFormFromBarcode(frm, r.message, parsedData);
			} else {
				frappe.msgprint({
					title: 'Error',
					message: r.message ? r.message.message : 'Error processing barcode',
					indicator: 'red'
				});
			}
		}
	});
}

/**
 * Parse barcode string into components
 */
function parseBarcodeString(barcodeString) {
	try {
		const parts = barcodeString.trim().split('/');

		if (parts.length !== 8) {
			return {
				error: `Invalid barcode format. Expected 8 fields, got ${parts.length}`
			};
		}

		// Validate field lengths
		if (parts[0].length !== 8) return { error: 'Vendor Code must be 8 characters' };
		if (parts[1].length !== 10) return { error: 'Part Code must be 10 characters' };
		if (parts[2].length !== 14) return { error: 'Batch Number must be 14 characters' };
		if (parts[3].length !== 7) return { error: 'Packet Serial must be 7 characters' };
		if (parts[4].length !== 6) return { error: 'Mfg Date must be 6 digits (YYMMDD)' };
		if (parts[5].length !== 6) return { error: 'Exp Date must be 6 digits (YYMMDD)' };
		if (parts[6].length !== 7) return { error: 'Quantity must be 7 digits' };
		if (parts[7].length !== 1) return { error: 'Constant Text must be 1 character' };

		return {
			vendor_code: parts[0],
			part_code: parts[1],
			batch_no: parts[2],
			packet_serial: parts[3],
			mfg_date: parts[4],
			exp_date: parts[5],
			qty: parts[6],
			constant_text: parts[7]
		};
	} catch (e) {
		return { error: `Error parsing barcode: ${e.message}` };
	}
}

/**
 * Convert YYMMDD format to YYYY-MM-DD format for date fields
 */
function convertDateFormat(dateStr) {
	try {
		// Format: YYMMDD
		const yy = dateStr.substring(0, 2);
		const mm = dateStr.substring(2, 4);
		const dd = dateStr.substring(4, 6);

		// Convert to full year
		const year = parseInt(yy) > 40 ? `19${yy}` : `20${yy}`;

		return `${year}-${mm}-${dd}`;
	} catch (e) {
		return null;
	}
}

/**
 * Populate form fields from scanned barcode
 */
function populateFormFromBarcode(frm, barcodeData, parsedData) {
	const tableName = getTableName(frm.doctype);
	if (!tableName) {
		frappe.msgprint({
			title: 'Error',
			message: 'Unsupported document type for barcode scanning',
			indicator: 'red'
		});
		return;
	}

	// Create a new row in the items table
	const newRow = frm.add_child(tableName);

	// Populate fields
	newRow.item_code = barcodeData.item_code;
	newRow.batch_no = barcodeData.batch_no;
	newRow.qty = barcodeData.qty;

	// Set custom fields if available
	if (barcodeData.mfg_date) {
		newRow.mfg_date = barcodeData.mfg_date;
	}
	if (barcodeData.exp_date) {
		newRow.exp_date = barcodeData.exp_date;
	}

	// Try to set warehouse if available
	if (frm.doctype === 'Delivery Note' && !newRow.warehouse) {
		// For Delivery Note, try to get source warehouse
		const suppliers = frappe.get_list('Supplier', {
			filters: { name: barcodeData.vendor_code },
			fields: ['name']
		});
	}

	// Refresh the table
	frm.refresh_field(tableName);

	// Show success message with details
	frappe.msgprint({
		title: 'Barcode Scanned Successfully',
		message: `
			<div style="padding: 10px;">
				<p><strong>Item Code:</strong> ${barcodeData.item_code}</p>
				<p><strong>Batch:</strong> ${barcodeData.batch_no}</p>
				<p><strong>Quantity:</strong> ${barcodeData.qty}</p>
				<p><strong>Mfg Date:</strong> ${barcodeData.mfg_date}</p>
				<p><strong>Exp Date:</strong> ${barcodeData.exp_date}</p>
				<p><strong>Vendor:</strong> ${barcodeData.vendor_code}</p>
				<p><strong>Packet Serial:</strong> ${barcodeData.packet_serial}</p>
			</div>
		`,
		indicator: 'green'
	});
}

/**
 * Add barcode scanning button to toolbar
 */
frappe.ui.form.on('Purchase Receipt', {
	refresh: function(frm) {
		addBarcodeButton(frm);
	}
});

frappe.ui.form.on('Stock Entry', {
	refresh: function(frm) {
		addBarcodeButton(frm);
	}
});

frappe.ui.form.on('Delivery Note', {
	refresh: function(frm) {
		addBarcodeButton(frm);
	}
});

/**
 * Add barcode scanning button to form
 */
function addBarcodeButton(frm) {
	// Check if button already exists
	if (frm.custom_barcode_btn_added) return;

	frm.add_custom_button(__('Scan Barcode'), function() {
		startBarcodeInput(frm);
	}, __('Barcode'));

	frm.custom_barcode_btn_added = true;
}

// Shortcut key hint in console
console.log('Barcode Scanner Ready: Press Ctrl+B (or Cmd+B on Mac) to start scanning, or use the "Scan Barcode" button in the toolbar.');
