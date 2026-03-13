frappe.pages['barcode-generator'] = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Barcode Generator',
		single_column: true
	});

	page.main.html(`
		<div class="barcode-generator-container">
			<form class="barcode-form">
				<div class="barcode-form-section">
					<h4>Barcode Details</h4>
					<div class="barcode-form-grid">
						<div class="form-group">
							<label for="vendor_code">Vendor Code (8 digits)</label>
							<input type="text" id="vendor_code" class="form-control barcode-input" maxlength="8" placeholder="e.g., VS226001" required>
						</div>
						<div class="form-group">
							<label for="part_code">Part Code (10 characters)</label>
							<input type="text" id="part_code" class="form-control barcode-input" maxlength="10" placeholder="e.g., VECESR001" required>
						</div>
						<div class="form-group">
							<label for="batch_no">Batch Number (14 characters)</label>
							<input type="text" id="batch_no" class="form-control barcode-input" maxlength="14" placeholder="e.g., 00020220115M02" required>
						</div>
						<div class="form-group">
							<label for="packet_serial">Packet Serial (7 characters)</label>
							<input type="text" id="packet_serial" class="form-control barcode-input" maxlength="7" placeholder="e.g., N1E0009" required>
						</div>
						<div class="form-group">
							<label for="mfg_date">Manufacturing Date (YYMMDD)</label>
							<input type="text" id="mfg_date" class="form-control barcode-input" maxlength="6" placeholder="e.g., 220114" required>
						</div>
						<div class="form-group">
							<label for="exp_date">Expiry Date (YYMMDD)</label>
							<input type="text" id="exp_date" class="form-control barcode-input" maxlength="6" placeholder="e.g., 220414" required>
						</div>
						<div class="form-group">
							<label for="qty">Quantity (7 digits)</label>
							<input type="text" id="qty" class="form-control barcode-input" maxlength="7" placeholder="e.g., 0000261" required>
						</div>
						<div class="form-group">
							<label for="constant_text">Constant Text (1 character)</label>
							<input type="text" id="constant_text" class="form-control barcode-input" maxlength="1" placeholder="e.g., A" required>
						</div>
					</div>
				</div>

				<div class="barcode-button-group">
					<button type="button" class="btn btn-primary btn-lg" id="btn-generate">
						<i class="fa fa-barcode"></i> Generate Barcode
					</button>
					<button type="button" class="btn btn-info btn-lg" id="btn-print" disabled>
						<i class="fa fa-print"></i> Print Label
					</button>
					<button type="button" class="btn btn-success btn-lg" id="btn-save" disabled>
						<i class="fa fa-save"></i> Save Log
					</button>
				</div>
			</form>

			<div class="barcode-result-section" id="result-section" style="display: none;">
				<div class="result-grid">
					<div class="result-item">
						<h5>QR Code</h5>
						<div id="qr-code-container" class="qr-code-container">
							<img id="qr-code-img" src="" alt="QR Code">
						</div>
					</div>
					<div class="result-item">
						<h5>Barcode Details</h5>
						<div id="barcode-details" class="barcode-details">
							<p><strong>Barcode String:</strong> <code id="barcode-string"></code></p>
							<p><strong>Vendor Code:</strong> <span id="result-vendor"></span></p>
							<p><strong>Part Code:</strong> <span id="result-part"></span></p>
							<p><strong>Batch No:</strong> <span id="result-batch"></span></p>
							<p><strong>Packet Serial:</strong> <span id="result-packet"></span></p>
							<p><strong>Mfg Date:</strong> <span id="result-mfg"></span></p>
							<p><strong>Exp Date:</strong> <span id="result-exp"></span></p>
							<p><strong>Quantity:</strong> <span id="result-qty"></span></p>
							<p><strong>Constant:</strong> <span id="result-constant"></span></p>
						</div>
					</div>
				</div>
			</div>

			<div id="alert-section"></div>
		</div>
	`);

	// Event listeners
	document.getElementById('btn-generate').addEventListener('click', generateBarcode);
	document.getElementById('btn-print').addEventListener('click', printLabel);
	document.getElementById('btn-save').addEventListener('click', saveLog);

	// Store current barcode data globally
	window.currentBarcodeData = null;

	function collectFormData() {
		return {
			vendor_code: document.getElementById('vendor_code').value.toUpperCase(),
			part_code: document.getElementById('part_code').value.toUpperCase(),
			batch_no: document.getElementById('batch_no').value.toUpperCase(),
			packet_serial: document.getElementById('packet_serial').value.toUpperCase(),
			mfg_date: document.getElementById('mfg_date').value,
			exp_date: document.getElementById('exp_date').value,
			qty: document.getElementById('qty').value,
			constant_text: document.getElementById('constant_text').value.toUpperCase()
		};
	}

	function generateBarcode() {
		const formData = collectFormData();
		const alertSection = document.getElementById('alert-section');
		alertSection.innerHTML = '';

		frappe.call({
			method: 'barcode_management.api.barcode_api.generate_barcode',
			args: {
				data: formData
			},
			callback: function(r) {
				if (r.message.status === 'success') {
					window.currentBarcodeData = formData;
					displayBarcode(r.message.barcode_string, r.message.qr_code, formData);
					showAlert('Barcode generated successfully!', 'success', alertSection);
					document.getElementById('btn-print').disabled = false;
					document.getElementById('btn-save').disabled = false;
				} else {
					showAlert(r.message.message, 'error', alertSection);
				}
			},
			error: function() {
				showAlert('Error generating barcode. Please try again.', 'error', alertSection);
			}
		});
	}

	function displayBarcode(barcodeString, qrCode, formData) {
		const resultSection = document.getElementById('result-section');
		document.getElementById('qr-code-img').src = qrCode;
		document.getElementById('barcode-string').textContent = barcodeString;
		document.getElementById('result-vendor').textContent = formData.vendor_code;
		document.getElementById('result-part').textContent = formData.part_code;
		document.getElementById('result-batch').textContent = formData.batch_no;
		document.getElementById('result-packet').textContent = formData.packet_serial;
		document.getElementById('result-mfg').textContent = formData.mfg_date;
		document.getElementById('result-exp').textContent = formData.exp_date;
		document.getElementById('result-qty').textContent = formData.qty;
		document.getElementById('result-constant').textContent = formData.constant_text;
		resultSection.style.display = 'block';
	}

	function printLabel() {
		if (!window.currentBarcodeData) {
			showAlert('Please generate a barcode first', 'warning', document.getElementById('alert-section'));
			return;
		}

		const printWindow = window.open('', '', 'height=400,width=600');
		const barcodeString = document.getElementById('barcode-string').textContent;
		const qrSrc = document.getElementById('qr-code-img').src;

		printWindow.document.write(`
			<!DOCTYPE html>
			<html>
				<head>
					<title>Barcode Label</title>
					<style>
						body {
							font-family: Arial, sans-serif;
							margin: 10mm;
							background: white;
						}
						.label-container {
							width: 100mm;
							height: 60mm;
							border: 2px solid #000;
							padding: 10mm;
							display: flex;
							background: white;
						}
						.qr-section {
							flex: 0 0 30mm;
							text-align: center;
							border-right: 1px solid #ddd;
							padding-right: 10mm;
						}
						.barcode-section {
							flex: 1;
							padding-left: 10mm;
							display: flex;
							flex-direction: column;
							justify-content: center;
						}
						.qr-section img {
							max-width: 30mm;
							height: auto;
						}
						.barcode-string {
							font-size: 11pt;
							font-weight: bold;
							margin: 3mm 0;
							word-break: break-all;
							font-family: monospace;
						}
						.label-row {
							font-size: 10pt;
							margin: 1mm 0;
						}
						.label-row strong {
							width: 25mm;
							display: inline-block;
						}
						@media print {
							body { margin: 0; }
							.label-container { border: none; }
						}
					</style>
				</head>
				<body>
					<div class="label-container">
						<div class="qr-section">
							<img src="${qrSrc}" alt="QR Code">
						</div>
						<div class="barcode-section">
							<div class="barcode-string">${barcodeString}</div>
							<div class="label-row"><strong>Part:</strong> ${document.getElementById('result-part').textContent}</div>
							<div class="label-row"><strong>Batch:</strong> ${document.getElementById('result-batch').textContent}</div>
							<div class="label-row"><strong>Qty:</strong> ${document.getElementById('result-qty').textContent}</div>
							<div class="label-row"><strong>Mfg:</strong> ${document.getElementById('result-mfg').textContent}</div>
							<div class="label-row"><strong>Exp:</strong> ${document.getElementById('result-exp').textContent}</div>
						</div>
					</div>
					<script>
						window.print();
						window.close();
					</script>
				</body>
			</html>
		`);
		printWindow.document.close();
	}

	function saveLog() {
		if (!window.currentBarcodeData) {
			showAlert('Please generate a barcode first', 'warning', document.getElementById('alert-section'));
			return;
		}

		const alertSection = document.getElementById('alert-section');

		frappe.call({
			method: 'barcode_management.api.barcode_api.save_barcode_log',
			args: {
				data: window.currentBarcodeData
			},
			callback: function(r) {
				if (r.message.status === 'success') {
					showAlert(`Barcode saved successfully! (ID: ${r.message.barcode_log})`, 'success', alertSection);
					// Reset form
					document.querySelector('.barcode-form').reset();
					document.getElementById('result-section').style.display = 'none';
					document.getElementById('btn-print').disabled = true;
					document.getElementById('btn-save').disabled = true;
					window.currentBarcodeData = null;
				} else {
					showAlert(r.message.message, 'error', alertSection);
				}
			},
			error: function() {
				showAlert('Error saving barcode log. Please try again.', 'error', alertSection);
			}
		});
	}

	function showAlert(message, type, container) {
		const alertClass = type === 'success' ? 'alert-success' : type === 'error' ? 'alert-danger' : 'alert-warning';
		container.innerHTML = `<div class="alert ${alertClass} alert-dismissible fade show" role="alert">
			${message}
			<button type="button" class="btn-close" data-bs-dismiss="alert"></button>
		</div>`;
	}
};
