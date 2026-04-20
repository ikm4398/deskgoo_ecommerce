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
    username: str | None = None,
    **kwargs,
):
    """
    Public API to register a new user for e-commerce (Frappe 16)

    Features:
    - Username support
    - Phone stored in User (phone + mobile_no)
    - Customer auto creation
    - User Permissions
    - Portal User linking
    """

    # -------------------------
    # 1. VALIDATIONS
    # -------------------------
    if not email or not password or not first_name:
        frappe.throw(_("Email, Password and First Name are required"), title=_("Missing Fields"))

    # Email exists check
    if frappe.db.exists("User", email):
        frappe.throw(_("User with this email already exists"), title=_("Registration Failed"))

    # Username check
    if username and frappe.db.exists("User", {"username": username}):
        frappe.throw(_("Username already taken"), title=_("Registration Failed"))

    # -------------------------
    # 2. CREATE USER
    # -------------------------
    full_name = f"{first_name} {last_name}".strip() or email

    user_doc = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "username": username or email,
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "user_type": "Website User",
        "enabled": 1,
        "language": "en",
        "send_welcome_email": 0,

        # ✅ Phone stored in both fields
        "phone": phone or "",
        "mobile_no": phone or "",
    }).insert(ignore_permissions=True)

    # Assign role
    user_doc.add_roles("Ecommerce Site User", "Customer","Workspace Manager")

    # Set password
    update_password(user_doc.name, password)

    # -------------------------
    # 3. CREATE CUSTOMER
    # -------------------------
    cust_name = customer_name or full_name

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

    # -------------------------
    # 4. USER PERMISSIONS
    # -------------------------
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

    # -------------------------
    # 5. LINK PORTAL USER
    # -------------------------
    link_customer_portal_user(customer_doc.name, user_doc.name)

    frappe.db.commit()

    # -------------------------
    # RESPONSE
    # -------------------------
    return {
        "status": "success",
        "message": _("User registered successfully"),
        "user": email,
        "username": user_doc.username,
        "phone": phone,
        "customer": customer_doc.name,
        "customer_name": customer_doc.customer_name,
    }


@frappe.whitelist(allow_guest=True)
def link_customer_portal_user(customer_name: str, user_email: str):
    """
    Link a User to Customer's Portal Users child table.
    Prevent duplicate entries.
    """

    if not frappe.db.exists("Customer", customer_name):
        frappe.throw(_("Customer not found"), title=_("Link Failed"))

    cust_doc = frappe.get_doc("Customer", customer_name)

    # Prevent duplicate
    if any(row.user == user_email for row in (cust_doc.get("portal_users") or [])):
        return {
            "status": "already_linked",
            "message": f"User {user_email} already linked"
        }

    # Append user
    cust_doc.append("portal_users", {
        "user": user_email
    })

    cust_doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": "success",
        "message": f"User {user_email} linked to Customer {customer_name}"
    }
