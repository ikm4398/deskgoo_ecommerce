# # deskgoo_ecommerce/api/user_register/register.py

# # deskgoo_ecommerce/api/user_register/register.py

# import frappe
# from frappe import _
# from frappe.utils.password import update_password


# @frappe.whitelist(allow_guest=True)
# def register(
#     email: str,
#     password: str,
#     first_name: str,
#     last_name: str = "",
#     phone: str | None = None,
#     customer_name: str | None = None,
#     **kwargs,
# ):
#     """
#     Public API to register a new user for e-commerce.
#     - Creates a User (Website User)
#     - Assigns role: Ecommerce Site User
#     - Creates a linked Customer (using naming series CUST-.YYYY.-)
#     - Creates User Permissions (Customer + self User)
#     """

#     # 1. Validate email is not already registered
#     if frappe.db.exists("User", email):
#         frappe.throw(_("User with this email already exists"), title=_("Registration Failed"))

#     # 2. Create User
#     user_doc = frappe.get_doc({
#         "doctype": "User",
#         "email": email,
#         "first_name": first_name,
#         "last_name": last_name,
#         "full_name": f"{first_name} {last_name}".strip() or email,
#         "user_type": "Website User",          # Required for e-commerce portal users
#         "enabled": 1,
#         "language": "en",
#         "send_welcome_email": 0,              # We can trigger manually if needed
#     })

#     user_doc.insert(ignore_permissions=True)

#     # Assign the required role
#     user_doc.add_roles("Ecommerce Site User")

#     # Set password (password field is not stored directly)
#     update_password(user_doc.name, password)

#     # 3. Create Customer (auto naming via series CUST-.YYYY.-)
#     cust_name = customer_name or f"{first_name} {last_name}".strip() or email

#     customer_doc = frappe.get_doc({
#         "doctype": "Customer",
#         "naming_series": "CUST-.YYYY.-",
#         "customer_name": cust_name,
#         "customer_type": "Individual",
#         "customer_group": "All Customer Groups",
#         "territory": "All Territories",
#         "email_id": email,
#         "mobile_no": phone,
#         "language": "en",
#     })

#     customer_doc.insert(ignore_permissions=True)

#     # 4. Create User Permissions (exactly as shown in your example)
#     # Permission for Customer
#     frappe.get_doc({
#         "doctype": "User Permission",
#         "user": email,
#         "allow": "Customer",
#         "for_value": customer_doc.name,
#         "is_default": 0,
#         "apply_to_all_doctypes": 1,
#         "applicable_for": None,
#         "hide_descendants": 0,
#     }).insert(ignore_permissions=True)

#     # Permission for User (self-restriction - common for portal users)
#     frappe.get_doc({
#         "doctype": "User Permission",
#         "user": email,
#         "allow": "User",
#         "for_value": email,
#         "is_default": 0,
#         "apply_to_all_doctypes": 1,
#         "applicable_for": None,
#         "hide_descendants": 0,
#     }).insert(ignore_permissions=True)

#     # Commit everything
#     frappe.db.commit()

#     return {
#         "status": "success",
#         "message": _("User registered successfully"),
#         "user": email,
#         "customer": customer_doc.name,
#         "customer_name": customer_doc.customer_name,
#     }

# deskgoo_ecommerce/api/user_register/register.py

import frappe
from frappe import _
from frappe.utils.password import update_password


@frappe.whitelist(allow_guest=True)
def register(
    email: str,
    password: str,
    first_name: str,
    last_name: str = "",
    phone: str | None = None,
    customer_name: str | None = None,
    **kwargs,
):
    """
    Public API to register a new user for e-commerce (Frappe 16).
    - Creates User + assigns "Ecommerce Site User" role
    - Creates Customer
    - Creates User Permissions (as per your existing setup)
    - NEW: Auto-links User in Customer → Portal Users child table
    """

    if frappe.db.exists("User", email):
        frappe.throw(_("User with this email already exists"), title=_("Registration Failed"))

    # 1. Create User
    user_doc = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "full_name": f"{first_name} {last_name}".strip() or email,
        "user_type": "Website User",
        "enabled": 1,
        "language": "en",
        "send_welcome_email": 0,
    }).insert(ignore_permissions=True)

    user_doc.add_roles("Ecommerce Site User")
    update_password(user_doc.name, password)

    # 2. Create Customer
    cust_name = customer_name or f"{first_name} {last_name}".strip() or email
    customer_doc = frappe.get_doc({
        "doctype": "Customer",
        "naming_series": "CUST-.YYYY.-",
        "customer_name": cust_name,
        "customer_type": "Individual",
        "customer_group": "All Customer Groups",
        "territory": "All Territories",
        "email_id": email,
        "mobile_no": phone,
        "language": "en",
    }).insert(ignore_permissions=True)

    # 3. Create User Permissions (your existing logic)
    frappe.get_doc({
        "doctype": "User Permission",
        "user": email,
        "allow": "Customer",
        "for_value": customer_doc.name,
        "apply_to_all_doctypes": 1,
    }).insert(ignore_permissions=True)

    frappe.get_doc({
        "doctype": "User Permission",
        "user": email,
        "allow": "User",
        "for_value": email,
        "apply_to_all_doctypes": 1,
    }).insert(ignore_permissions=True)

    # 4. NEW: Auto-link User in Customer Portal Users (Frappe 16)
    link_customer_portal_user(customer_doc.name, user_doc.name)

    frappe.db.commit()

    return {
        "status": "success",
        "message": _("User registered successfully"),
        "user": email,
        "customer": customer_doc.name,
        "customer_name": customer_doc.customer_name,
    }


@frappe.whitelist(allow_guest=True)
def link_customer_portal_user(customer_name: str, user_email: str):
    """
    Reusable function to auto-link a User to the Customer's "Portal Users" child table.
    Works in Frappe 16 / ERPNext (fieldname = portal_users, child doctype = Portal User).
    Prevents duplicate entries.
    """
    if not frappe.db.exists("Customer", customer_name):
        frappe.throw(_("Customer not found"), title=_("Link Failed"))

    cust_doc = frappe.get_doc("Customer", customer_name)

    # Avoid duplicate link
    if any(row.user == user_email for row in cust_doc.get("portal_users") or []):
        return {
            "status": "already_linked",
            "message": f"User {user_email} is already linked in Customer Portal Users"
        }

    # Auto-link
    cust_doc.append("portal_users", {
        "user": user_email
    })

    cust_doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": "success",
        "message": f"User {user_email} successfully linked to Customer {customer_name} → Portal Users"
    }