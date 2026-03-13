frappe.pages['barcode_generator'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Barcode Generator',
		single_column: true
	});
}