
import frappe
from frappe import _
from ..otp import send_otp


@frappe.whitelist(allow_guest=True)
def forgotsendotp(email: str):
	"""Send OTP to existing user email for password reset."""
	if not email or "@" not in email:
		frappe.throw(_("Valid email is required"), title=_("Invalid Email"))

	if not frappe.db.exists("User", email):
		frappe.throw(_("User not found"), title=_("Not Found"))

	send_otp(email, purpose="forgot_password")

	return {
		"status": "success",
		"message": _("OTP sent successfully to your email"),
		"email": email,
	}
