app_name = "vecmocon_customization"
app_title = "Vecomocon"
app_publisher = "MI_Cloud"
app_description = "Vecmocon"
app_email = "contact@mi_cloud.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "vecmocon_customization",
# 		"logo": "/assets/vecmocon_customization/logo.png",
# 		"title": "Vecomocon",
# 		"route": "/vecmocon_customization",
# 		"has_permission": "vecmocon_customization.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/vecmocon_customization/css/vecmocon_customization.css"
# app_include_js = "/assets/vecmocon_customization/js/vecmocon_customization.js"

# include js, css files in header of web template
# web_include_css = "/assets/vecmocon_customization/css/vecmocon_customization.css"
# web_include_js = "/assets/vecmocon_customization/js/vecmocon_customization.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "vecmocon_customization/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js, css files in header of desk.html
app_include_css = "/assets/vecmocon_customization/css/barcode_generator.css"
app_include_js = "/assets/vecmocon_customization/js/barcode_scanner.js"

# include js in doctype views
doctype_js = {
    "Purchase Receipt": "public/js/purchase_receipt.js",
    "Company": "public/js/company.js",
    "Material Request": "public/js/material_request.js",
    "Payment Entry": "public/js/payment_entry.js",
    "Quality Inspection": "public/js/quality_inspection.js",
    "Subcontracting Receipt": "public/js/subcontracting_receipt.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "vecmocon_customization/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "vecmocon_customization.utils.jinja_methods",
# 	"filters": "vecmocon_customization.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "vecmocon_customization.install.before_install"
after_install = "vecmocon_customization.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "vecmocon_customization.uninstall.before_uninstall"
# after_uninstall = "vecmocon_customization.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "vecmocon_customization.utils.before_app_install"
# after_app_install = "vecmocon_customization.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "vecmocon_customization.utils.before_app_uninstall"
# after_app_uninstall = "vecmocon_customization.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "vecmocon_customization.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Stock Entry": "vecmocon_customization.override.stock_entry.CustomStockEntry"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
    
# }

# existing commented example kept for reference
# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"vecmocon_customization.tasks.all"
# 	],
# 	"daily": [
# 		"vecmocon_customization.tasks.daily"
# 	],
# 	"hourly": [
# 		"vecmocon_customization.tasks.hourly"
# 	],
# 	"weekly": [
# 		"vecmocon_customization.tasks.weekly"
# 	],
# 	"monthly": [
# 		"vecmocon_customization.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "vecmocon_customization.install.before_tests"

# Overriding Methods
# ------------------------------

override_whitelisted_methods = {
	"erpnext.stock.utils.scan_barcode": "vecmocon_customization.override.barcode_api.custom_scan_barcode"
}

# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "vecmocon_customization.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "vecmocon_customization.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["vecmocon_customization.utils.before_request"]
# after_request = ["vecmocon_customization.utils.after_request"]

# Job Events
# ----------
# before_job = ["vecmocon_customization.utils.before_job"]
# after_job = ["vecmocon_customization.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"vecmocon_customization.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

doc_events = {
    "Sales Order": {
        "before_submit": "vecmocon_customization.override.sales_order.incoterm_customization_before_submit",
        "before_insert": "vecmocon_customization.override.sales_order.incoterm_customization_before_insert",
    },
    "Delivery Note": {
        "before_save": "vecmocon_customization.override.delivery_note.vehicle_number_regex",
        "on_update_after_submit": "vecmocon_customization.override.delivery_note.on_update_after_submit",
        "before_submit": "vecmocon_customization.override.delivery_note.custom_on_submit",
        "validate": "vecmocon_customization.override.stock_validations.validate_delivery_note",
    },
    "Purchase Receipt": {
        "before_insert": "vecmocon_customization.override.purchase_receipt.purchase_receipt_before_insert",
        "before_save": "vecmocon_customization.override.purchase_receipt.purchase_receipt_before_save",
        "validate": "vecmocon_customization.override.stock_validations.validate_purchase_receipt",
        "before_submit": "vecmocon_customization.override.purchase_receipt.purchase_receipt_before_submit",
        "on_submit": "vecmocon_customization.override.purchase_receipt.purchase_receipt_on_submit",
    },
    "Stock Entry": {
        "validate": "vecmocon_customization.override.stock_validations.validate_stock_entry",
        "before_submit": "vecmocon_customization.override.stock_entry.stock_entry_before_submit",
    },
    "Quality Inspection": {
        "before_insert": "vecmocon_customization.override.quality_inspection.quality_inspection_before_insert",
        "before_save": "vecmocon_customization.override.quality_inspection.quality_inspection_before_save",
        "before_submit": "vecmocon_customization.override.quality_inspection.quality_inspection_before_submit",
        "on_submit": "vecmocon_customization.override.quality_inspection.quality_inspection_on_submit",
    },
    "Purchase Invoice": {
        "before_save": "vecmocon_customization.override.purchase_invoice.purchase_invoice_before_save",
    },
    "Purchase Order": {
        "before_save": "vecmocon_customization.override.purchase_order.purchase_order_before_save",
    },
    "Material Request": {
        "on_update_after_submit": "vecmocon_customization.override.material_request.material_request_on_update_after_submit",
    },
    "Payment Entry": {
        "before_save": "vecmocon_customization.override.payment_entry.payment_entry_before_save",
        "validate": "vecmocon_customization.override.payment_entry.validate_payment_entry",
        "on_submit": "vecmocon_customization.override.payment_entry.on_submit",
        "on_cancel": "vecmocon_customization.override.payment_entry.on_cancel",
    },
    "Subcontracting Receipt": {
        "before_validate": "vecmocon_customization.override.subcontracting_receipt.before_validate",
        "validate": "vecmocon_customization.override.subcontracting_receipt.validate",
    },
}

fixtures = [
    {
        "dt": "Client Script",
        "filters": [
            ["name", "in", ["Customer Customization", "Hide Updates", "Purchase Receipt", "Purchase Order", "Sales Order"]]
        ]
    },
    {
        "dt": "Property Setter",
        "filters": [
            ["name", "in", [
                "Sales Order Item-customer_item_code-read_only",
                "Quality Inspection-custom_due_date-depends_on",
                "Quality Inspection-custom_accetped_qty-depends_on",
                "Quality Inspection-custom_rejected_qty-depends_on",
                "Quality Inspection-custom_warehouse-depends_on",
                "Quality Inspection-custom_accetped_warehouse-depends_on",
                "Quality Inspection-custom_source_warehouse-depends_on",
                "Quality Inspection-custom_submitted_date-depends_on",
                "Quality Inspection-custom_delay_days-depends_on",
                "Quality Inspection-custom_rejected_status-depends_on",
                "Quality Inspection-custom_rejected_decision_date-depends_on"
            ]]
        ]
    },
    {
        "dt": "Workflow",
        "filters": [
            ["name", "in", [
                "Quanlity Inspection at Purchase Receipt", "Quality Inspection Workflow", "Supplier Onboarding Workflow"
            ]]
        ]
    },
    {
        "dt": "Workflow State"
    },
    {
        "dt": "Workflow Action"
    },
    {
        "dt": "Print Format",
        "filters": [
            ["name", "in", ["Purchase Order", "Purchase Receipt", "Purchase Invoice", "Tax-Invoice", "Delivery Challan", 
            "Delivery Challan Without Values", "Goods Sales Order", "Services Sales Order", "SE Delivery Challan", "SE Delivery Challan Without Values"]]
        ]
    },
]