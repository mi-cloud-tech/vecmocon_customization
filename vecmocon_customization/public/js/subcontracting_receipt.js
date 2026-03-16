frappe.ui.form.on("Subcontracting Receipt", {
	refresh(frm) {
		frappe.db.get_single_value("Vecmocon Settings", "allow_manual_consumed_qty_edit").then((value) => {
			if (value) {
				frm.fields_dict.supplied_items.grid.update_docfield_property(
					"consumed_qty",
					"read_only",
					0
				);
				frm.refresh_field("supplied_items");
			}
		});
	},
});
