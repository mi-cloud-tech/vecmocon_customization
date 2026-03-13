# Barcode Management System - Complete Setup Guide

## Overview

The Barcode Management system integrated into vecmocon_customization provides a complete solution for generating, managing, and scanning QR/barcodes in warehouse operations.

## Barcode Format

The system uses an 8-field structure separated by "/" (forward slash):

```
VENDOR_CODE/PART_CODE/BATCH_NO/PACKET_SERIAL/MFG_DATE/EXP_DATE/QTY/CONSTANT_TEXT
```

### Field Specifications

| Field | Format | Length | Example | Description |
|-------|--------|--------|---------|-------------|
| Vendor Code | Alphanumeric | 8 | VS226001 | Vendor identifier |
| Part Code | Alphanumeric | 10 | VECESR001 | Product/part identifier |
| Batch Number | Alphanumeric | 14 | 00020220115M02 | Batch/lot number |
| Packet Serial | Alphanumeric | 7 | N1E0009 | Individual packet identifier |
| Mfg Date | YYMMDD | 6 | 220114 | Manufacturing date |
| Exp Date | YYMMDD | 6 | 220414 | Expiry date |
| Quantity | Digit | 7 | 0000261 | Quantity in packet |
| Constant Text | Alphabetic | 1 | A | Constant/fixed value |

**Example Full Barcode:** `VS226001/VECESR001/00020220115M02/N1E0009/220114/220414/0000261/A`

## System Architecture

### 1. Barcode Log DocType
**Location:** `vecmocon_customization/vecomocon/doctype/barcode_log/`

The core data model that stores all generated barcodes with the following fields:
- **barcode_string**: Unique identifier (auto-generated with format: {barcode_string}-{#####})
- **vendor_code**: 8-digit vendor identifier
- **part_code**: 10-character part identifier
- **batch_no**: 14-character batch number
- **packet_serial**: 7-character packet serial
- **mfg_date**: Manufacturing date
- **exp_date**: Expiry date
- **qty**: Quantity
- **constant_text**: Single character constant
- **generated_by**: User who generated the barcode
- **generated_on**: Timestamp of generation

### 2. Backend API Endpoints
**Location:** `vecmocon_customization/override/barcode_api.py`

#### Core Functions

**`generate_barcode(data)`**
- Endpoint: `/api/method/vecmocon_customization.override.barcode_api.generate_barcode`
- Input: Dictionary with barcode field data
- Output: Barcode string and QR code (base64 PNG)
- Validates data, checks for duplicates, generates QR code
- Does NOT save to database

**`save_barcode_log(data)`**
- Endpoint: `/api/method/vecmocon_customization.override.barcode_api.save_barcode_log`
- Input: Dictionary with barcode field data
- Output: Saved barcode log record
- Validates, generates barcode, and saves to database
- Creates audit trail with generated_by and generated_on

**`scan_barcode(barcode_string)`**
- Endpoint: `/api/method/vecmocon_customization.override.barcode_api.scan_barcode`
- Input: Scanned barcode string
- Output: Parsed barcode data with formatted dates
- Used by client script during warehouse document entry
- Converts dates from YYMMDD to YYYY-MM-DD format

#### Supporting Functions

- `generate_barcode_string(data)`: Creates "/" delimited barcode string
- `validate_barcode_data(data)`: Validates all fields against specifications
- `check_duplicate_barcode(barcode_string)`: Prevents duplicate barcodes
- `generate_qr_code(barcode_string)`: Creates QR code image (base64 PNG)
- `parse_barcode_string(barcode_string)`: Splits barcode into components

### 3. Frontend Pages and Scripts
**Location:** `vecmocon_customization/public/js/`, `vecmocon_customization/public/css/`

#### Barcode Generator Page
**File:** `barcode_generator.js`
- Frappe page UI at route: `/app/barcode-generator`
- Provides form with 8 input fields for barcode data
- Features:
  - Real-time validation
  - QR code preview
  - Generate button (creates QR without saving)
  - Save button (saves to database)
  - Print button (generates label)
  - Result display section
  - Field-level validation with error messages

#### Barcode Scanner Integration
**File:** `barcode_scanner.js`
- Client script integrated into warehouse documents
- Auto-includes in: Purchase Receipt, Stock Entry, Delivery Note
- Features:
  - Ctrl+B shortcut to activate scanner
  - Toolbar button for manual activation
  - Real-time barcode parsing during input
  - Auto-population of:
    - item_code (from part_code)
    - batch_no
    - qty
    - mfg_date, exp_date (converted to YYYY-MM-DD)
  - Vendor/packet validation
  - Date format conversion

#### Styling
**File:** `barcode_generator.css`
- Responsive grid layout (2-4 columns based on screen size)
- Professional color scheme with animations
- Button states and hover effects
- Alert/notification styling
- Print-optimized media queries
- Mobile responsive design

### 4. Print Templates
**Location:** `vecmocon_customization/templates/barcode_label.html`

- 100mm × 60mm sticker label format
- QR code display (40mm × 40mm)
- Barcode information section with abbreviated fields
- Barcode string display in monospace font
- Print optimization for standard label printers
- Screen and print-optimized styling

### 5. Utility Functions
**Location:** `vecmocon_customization/override/barcode_utils.py`

- `get_barcode_history(limit=100)`: Retrieve generated barcodes
- `get_barcode_statistics()`: Statistical data by vendor, part, and date
- `check_expiry_barcodes(days_ahead=30)`: Find expiring barcodes
- `export_barcode_log(filters=None)`: Export to CSV
- `import_barcode_log(file_data)`: Import from CSV
- `validate_item_availability(item_code, warehouse=None)`: Check stock
- `bulk_generate_barcodes(data_list)`: Generate multiple barcodes
- `archive_old_barcodes(days=90)`: Archive old records

### 6. Configuration
**Location:** `vecmocon_customization/hooks.py`, `vecmocon_customization/config/desktop.py`

#### hooks.py Configuration

```python
# Page registration
page_js = {
    "barcode-generator": "public/js/barcode_generator.js"
}

# Global includes
app_include_css = "/assets/vecmocon_customization/css/barcode_generator.css"
app_include_js = "/assets/vecmocon_customization/js/barcode_scanner.js"

# DocType-specific scripts
doctype_js = {
    "Purchase Receipt": "public/js/barcode_scanner.js",
    "Stock Entry": "public/js/barcode_scanner.js",
    "Delivery Note": "public/js/barcode_scanner.js"
}

# Installation hook
after_install = "vecmocon_customization.install.after_install"
```

#### desktop.py Configuration

Creates "Barcode Management" module with:
- Barcode Generator page link
- Barcode Log list
- Barcode Log Report

## Setup and Installation

### Prerequisites

```bash
# Required Python packages (in bench environment)
pip install qrcode[pil]
# or
pip install qrcode pillow
```

### Installation Steps

1. **Ensure packages are installed:**
   ```bash
   cd /path/to/bench
   ./env/bin/pip install qrcode pillow
   ```

2. **Migrate database:**
   ```bash
   bench --site site-name migrate
   ```

3. **Restart Frappe:**
   ```bash
   bench restart
   ```

4. **Clear cache:**
   ```bash
   bench --site site-name clear-cache
   ```

### Auto-Setup via Installation Hook

When `bench install-app vecmocon_customization` or `bench migrate` is run:
1. `after_install` hook calls `setup_barcode_module()`
2. Creates Barcode Log DocType automatically
3. Sets up module and permissions
4. Ready to use immediately

## Usage Guide

### Generate a Barcode

1. Navigate to **Barcode Management → Barcode Generator** in the sidebar
2. Fill in all 8 fields:
   - Vendor Code: 8 digits
   - Part Code: 10 characters
   - Batch Number: 14 characters
   - Packet Serial: 7 characters
   - Mfg Date: YYMMDD format
   - Exp Date: YYMMDD format
   - Quantity: 7 digits
   - Constant Text: 1 letter
3. Click **Generate** to preview QR code
4. Click **Save** to store in database
5. Click **Print** to print label
6. View all barcodes in **Barcode Log** list

### Scan During Warehouse Operations

1. **Enable Scanner:**
   - Press `Ctrl+B` or click the "Scan" button in toolbar
   - In Purchase Receipt, Stock Entry, or Delivery Note

2. **Scan Barcode:**
   - Position cursor in any field
   - Scan the barcode with your device
   - System automatically:
     - Parses the barcode
     - Fills item_code, batch_no, qty, dates
     - Converts dates to YYYY-MM-DD format

3. **Review and Submit:**
   - Verify auto-populated data
   - Adjust if needed
   - Submit the document

### Export Barcode Data

```python
# Via Python console
from vecmocon_customization.override.barcode_utils import export_barcode_log

result = export_barcode_log({
    'vendor_code': 'VS226001',
    'date_from': '2025-01-01',
    'date_to': '2025-12-31'
})
```

### Get Statistics

```python
from vecmocon_customization.override.barcode_utils import get_barcode_statistics

stats = get_barcode_statistics()
# Returns: total count, today's count, stats by vendor/part
```

### Check Expiring Items

```python
from vecmocon_customization.override.barcode_utils import check_expiry_barcodes

expiring = check_expiry_barcodes(days_ahead=30)
# Returns barcodes expiring in next 30 days
```

## API Integration Examples

### Generate Barcode via API

```javascript
frappe.call({
    method: 'vecmocon_customization.override.barcode_api.generate_barcode',
    args: {
        data: JSON.stringify({
            vendor_code: 'VS226001',
            part_code: 'VECESR001',
            batch_no: '00020220115M02',
            packet_serial: 'N1E0009',
            mfg_date: '220114',
            exp_date: '220414',
            qty: '0000261',
            constant_text: 'A'
        })
    },
    callback: function(r) {
        if (r.message.status === 'success') {
            console.log('Barcode:', r.message.barcode_string);
            console.log('QR Code:', r.message.qr_code);
        }
    }
});
```

### Save Barcode via API

```javascript
frappe.call({
    method: 'vecmocon_customization.override.barcode_api.save_barcode_log',
    args: {
        data: JSON.stringify({
            vendor_code: 'VS226001',
            part_code: 'VECESR001',
            batch_no: '00020220115M02',
            packet_serial: 'N1E0009',
            mfg_date: '220114',
            exp_date: '220414',
            qty: '0000261',
            constant_text: 'A'
        })
    },
    callback: function(r) {
        if (r.message.status === 'success') {
            frappe.msgprint('Barcode saved: ' + r.message.barcode_log);
        }
    }
});
```

### Scan Barcode via API

```javascript
frappe.call({
    method: 'vecmocon_customization.override.barcode_api.scan_barcode',
    args: {
        barcode_string: 'VS226001/VECESR001/00020220115M02/N1E0009/220114/220414/0000261/A'
    },
    callback: function(r) {
        if (r.message.status === 'success') {
            let data = r.message;
            cur_frm.set_value('item_code', data.item_code);
            cur_frm.set_value('batch_no', data.batch_no);
            // ... populate other fields
        }
    }
});
```

## Troubleshooting

### Barcode Generator Not Accessible
- **Solution:** Clear cache with `bench --site site-name clear-cache`
- Check that page is registered in `page_js` in hooks.py

### Barcode Log Not Appearing in Database
- **Solution:** Run `bench --site site-name migrate --doctypes`
- Check DocType is in database via `frappe.db.exists('DocType', 'Barcode Log')`

### Scanner Not Working in Documents
- **Solution:** Ensure `barcode_scanner.js` is in `doctype_js` for the document type
- Reload the document form (Ctrl+R)
- Check browser console for JavaScript errors

### QR Code Not Displaying
- **Solution:** Verify `qrcode` and `pillow` packages are installed
- Check Python environment: `pip list | grep qrcode`

### Invalid Barcode Format Error
- **Solution:** Verify each field matches required length and format
- Use the Barcode Generator form for validation

## File Structure

```
vecmocon_customization/
├── vecomocon/
│   └── doctype/
│       └── barcode_log/
│           ├── barcode_log.json       # DocType definition
│           ├── barcode_log.py         # DocType class
│           ├── barcode_log.js         # DocType client script
│           └── test_barcode_log.py    # Tests
├── override/
│   ├── barcode_api.py                 # Main API endpoints
│   └── barcode_utils.py               # Utility functions
├── public/
│   ├── js/
│   │   ├── barcode_generator.js       # Generator page script
│   │   └── barcode_scanner.js         # Scanner client script
│   └── css/
│       └── barcode_generator.css      # Styling
├── templates/
│   ├── barcode_label.html             # Print label template
│   └── pages/
│       ├── barcode_generator.html     # Page template
│       └── barcode_generator.py       # Page handler
├── config/
│   └── desktop.py                     # Desktop module config
├── install.py                         # Installation script
└── hooks.py                           # App configuration
```

## Permissions and Security

### Role-Based Access

Default permissions set during installation:

**System Manager:**
- Read, Write, Create, Delete
- Print and Report access

**User:**
- Read-only access
- Print and Report access

### Custom Permissions

Modify in DocType → Permissions tab or via Python:

```python
# Grant permission to custom role
perm = frappe.new_doc('DocPerm')
perm.parent = 'Barcode Log'
perm.parenttype = 'DocType'
perm.role = 'Warehouse Manager'
perm.permlevel = 0
perm.read = 1
perm.write = 1
perm.create = 1
perm.print = 1
perm.insert()
```

## Performance Optimization

### Indexing

The DocType includes index on:
- `barcode_string` (unique)
- `vendor_code`
- `part_code`
- `generated_on`

### Archiving Strategy

Archive old barcodes to maintain performance:

```python
from vecmocon_customization.override.barcode_utils import archive_old_barcodes

# Archive barcodes older than 90 days
result = archive_old_barcodes(days=90)
```

## Support and Maintenance

### Common Issues

1. **Module import error**: Ensure package paths are correct in hooks.py
2. **DocType missing**: Run `bench --site site-name migrate`
3. **QR code not generating**: Install qrcode and pillow: `pip install qrcode pillow`

### Debug Mode

Enable debug logging:

```python
# In Python console
frappe.set_value('System Settings', 'System Settings', 'enable_debug_logging', 1)
```

### Database Cleanup

Remove duplicate/test barcodes:

```python
# Via Python console
frappe.db.delete('Barcode Log', {'barcode_string': 'TEST-001'})
frappe.db.commit()
```

---

**Version:** 1.0  
**Last Updated:** March 2025  
**Maintained By:** Vecmocon Development Team
