# Warehouse Item Group Mapping Setup Guide

## Automatic Setup

The custom field `Allowed Item Groups` will be automatically added to the Warehouse doctype when the vecmocon_customization app is installed.

If you need to manually add the field, run:
```bash
bench execute vecmocon_customization.migrations.add_custom_allowed_item_groups_field_to_warehouse.execute
```

## Manual Setup (Alternative)

If the automatic setup doesn't work, you can manually add the custom field:

1. Go to **Customize Form** → **Warehouse**
2. Add a new field with:
   - **Field Name**: `custom_allowed_item_groups`
   - **Type**: Table MultiSelect
   - **Table**: Warehouse Item Group
   - **Label**: Allowed Item Groups
   - **Description**: Item groups allowed to be stored in this warehouse. Leave empty to allow all item groups.
3. Click **Save**

## Configuration

Once the field is added to each Warehouse:

1. Open the **Warehouse** you want to configure
2. Scroll to **Allowed Item Groups** section
3. Click **Add Row** to add item groups
4. Select the **Item Group** from the dropdown
5. **Save** the warehouse

## Examples

### Raw Material Warehouse
- Warehouse: RM Warehouse
- Allowed Item Groups: Raw Material (RM)

### Finished Goods Warehouse  
- Warehouse: FG Warehouse
- Allowed Item Groups: Finished Goods (FG), Semi-Finished Goods

### General Warehouse (No Restrictions)
- Warehouse: General Storage
- Allowed Item Groups: (Leave empty)
