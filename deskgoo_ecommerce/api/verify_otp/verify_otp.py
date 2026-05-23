# deskgoo_ecommerce/api/verify_otp/verify_otp.py

import frappe
from frappe import _
from ..otp import verify_otp as _verify_otp


@frappe.whitelist(allow_guest=True)
def verify_email_otp(email: str, otp: str):
    """Verify email verification OTP."""
    _verify_otp(email, otp, purpose="email_verify")

    return {
        "status": "success",
        "message": _("Email verified successfully"),
        "email": email,
    }


@frappe.whitelist(allow_guest=True)
def verify_password_reset_otp(email: str, otp: str):
    """Verify password reset OTP."""
    _verify_otp(email, otp, purpose="forgot_password")

    return {
        "status": "success",
        "message": _("Password reset OTP verified successfully"),
        "email": email,
    }