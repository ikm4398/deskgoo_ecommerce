import frappe
from frappe import _
from ..otp import verify_otp
from frappe.utils.password import update_password


@frappe.whitelist(allow_guest=True)
def reset_password(email: str, otp: str, new_password: str):
    """Verify OTP for forgot password and set new password."""
    if not email or not otp or not new_password:
        frappe.throw(_("Email, OTP and new password are required"), title=_("Missing Fields"))

    if not frappe.db.exists("User", email):
        frappe.throw(_("User not found"), title=_("Not Found"))

    # verify OTP stored for forgot_password
    verify_otp(email, otp, purpose="forgot_password")

    # update password using frappe helper
    update_password(email, new_password)

    frappe.db.commit()

    return {
        "status": "success",
        "message": _("Password updated successfully"),
        "email": email,
    }
