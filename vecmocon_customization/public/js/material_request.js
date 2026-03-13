frappe.ui.form.on("Material Request", {                                                                                                                   
    setup: function (frm) {                                                                                                                               
        frm.set_query("custom_supplier", "items", function (doc, cdt, cdn) {                                                                              
            let row = locals[cdt][cdn];                                                                                                                   
            if (row._allowed_suppliers && row._allowed_suppliers.length > 0) {                                                                              
                return {                                                                                                                                  
                    filters: {                                                                                                                            
                        name: ["in", row._allowed_suppliers]                                                                                               
                    }                                                                                                                                     
                };                                                                                                                                        
            }                                                                                                                                             
            return {};                                                                                                                                    
        });                                                                                                                                               
    },
    onload: async function(frm) {
        if (frm.doc.items && frm.doc.items.length > 0) {
            for (let item of frm.doc.items) {
                if (item.item_code && !item._allowed_suppliers) {
                    const r = await frappe.call({
                        method: "vecmocon_customization.override.material_request.get_allowed_suppliers",
                        args: { item_code: item.item_code },
                    });
                    item._allowed_suppliers = r.message || [];
                    frm.refresh_field('items');
                }
            }
        }
    },
    refresh(frm) {
        frm.remove_custom_button('Purchase Order', 'Create');
        if (!frm.doc.name) {
            return;
        }

        // existing PO logic
        frappe.call({
            method: 'vecmocon_customization.override.material_request.has_purchase_orders',
            args: { material_request: frm.doc.name },
            callback: function (r) {
                if (!r.message) {
                    frm.add_custom_button(
                        __('Multiple Purchase Orders'),
                        () => {
                            frappe.call({
                                method: 'vecmocon_customization.override.material_request.create_purchase_order_from_material_request',
                                args: {
                                    material_request: frm.doc.name
                                },
                                callback: function (r) {
                                    if (r.message) {
                                        frappe.msgprint(__('Purchase Orders created successfully'));
                                    }
                                }
                            });
                        },
                        __('Create')
                    );
                }
            }
        });
    }
});  
frappe.ui.form.on("Material Request Item", {
    item_code: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.item_code) {                                                                                                                             
            row.allowed_suppliers = [];                                                                                                                   
            return;                                                                                                                                       
        }
        frappe.call({
            method: "vecmocon_customization.override.material_request.get_allowed_suppliers",
            args: {
                item_code: row.item_code
            },
            callback: function (r) {                                                                                                                      
                row._allowed_suppliers = r.message || [];                                                                                                 
                frm.refresh_field('items');
            }
        });
    }
});