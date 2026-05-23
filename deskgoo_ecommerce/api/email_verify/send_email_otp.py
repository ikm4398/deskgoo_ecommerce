# deskgoo_ecommerce/api/email_verify/send_email_otp.py

import frappe
from frappe import _
from ..otp import send_otp


@frappe.whitelist(allow_guest=True)
def send_email_otp(email: str):
    # keep same public API but delegate logic to central send_otp
    if not email or "@" not in email:
        frappe.throw(_("Valid email is required"), title=_("Invalid Email"))

    if frappe.db.exists("User", email):
        frappe.throw(_("This email is already registered"), title=_("Registration Failed"))

    # send OTP for purpose 'email_verify'
    send_otp(email, purpose="email_verify")

    return {
        "status": "success",
        "message": _("OTP sent successfully to your email"),
        "email": email,
    }