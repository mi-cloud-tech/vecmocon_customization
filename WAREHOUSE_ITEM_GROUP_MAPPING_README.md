# Warehouse Item Group Mapping

This feature ensures that specific item groups can only be stored in specific warehouses, providing better inventory control and organization.

## Setup

### 1. Add Allowed Item Groups to Warehouse

To set up warehouse restrictions:

1. Go to **Warehouse** list
2. Open the **Warehouse** you want to configure (e.g., "RM Warehouse", "FG Warehouse")
3. Scroll down to the **Allowed Item Groups** section
4. Add all item groups that are allowed to be stored in this warehouse using the multi-select field
   - Example for RM Warehouse: Add "Raw Material (RM)"
   - Example for FG Warehouse: Add "Finished Goods (FG)"
5. **Save** the warehouse

### 2. Example Setup

**RM Warehouse**
- Allowed Item Groups: Raw Material (RM)

**FG Warehouse**
- Allowed Item Groups: Finished Goods (FG), Semi-Finished Goods

**General Storage Warehouse**
- Allowed Item Groups: (Leave empty or specify multiple groups)

## Validation & Features

The following stock transactions are validated:

1. **Stock Entry** - Both source and target warehouses
2. **Purchase Receipt** - Receipt warehouse
3. **Delivery Note** - Delivery warehouse

### Error Example

If a user tries to create a Stock Entry to store a "Raw Material" item in "FG Warehouse", they will receive:

```
Item RM-001 with Item Group Raw Material (RM) cannot be stored in Warehouse FG Warehouse.
Allowed Item Groups: Finished Goods (FG), Semi-Finished Goods
```

## Notes

- If the **Allowed Item Groups** field is empty for a warehouse, all item groups are allowed
- Each warehouse can have multiple allowed item groups
- The validation prevents data entry at the document level during save
- The validation applies during the document validation phase before submission