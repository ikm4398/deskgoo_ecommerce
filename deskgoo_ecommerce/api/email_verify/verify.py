# deskgoo_ecommerce/api/email_verify/verify.py

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def verify_email_otp(email: str, otp: str):
    """
    Verify the OTP sent via send_email_otp
    Uses same Email Account / Domain setup
    """
    if not email or not otp:
        frappe.throw(_("Email and OTP are required"))

    cache_key = f"otp:email_verify:{email.lower()}"
    stored_otp = frappe.cache().get_value(cache_key)

    if not stored_otp:
        frappe.throw(_("OTP has expired or not found. Please request a new one."), title=_("Expired"))

    if str(stored_otp) != str(otp).strip():
        frappe.throw(_("Invalid OTP"), title=_("Verification Failed"))

    # OTP verified → delete it
    frappe.cache().delete_value(cache_key)

    return {
        "status": "success",
        "message": _("Email verified successfully"),
        "email": email
    }