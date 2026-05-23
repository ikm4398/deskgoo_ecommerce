import frappe
import random
from frappe import _


def _cache_key(purpose: str, email: str) -> str:
    return f"otp:{purpose}:{email.lower()}"


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def send_otp(email: str, purpose: str = "email_verify", subject: str | None = None, message_html: str | None = None, expires_in_sec: int = 600):
    """Generate and send an OTP for the given purpose.

    Stores OTP in cache under `otp:{purpose}:{email}` and sends email using frappe.sendmail.
    Returns the generated OTP (useful for tests) or raises on failure.
    """
    if not email or "@" not in email:
        frappe.throw(_("Valid email is required"), title=_("Invalid Email"))

    otp = generate_otp()

    cache_key = _cache_key(purpose, email)
    frappe.cache().set_value(cache_key, otp, expires_in_sec=expires_in_sec)

    sender = frappe.get_value("Email Account", {"default_outgoing": 1}, "email_id") or ""

    if not subject:
        if purpose == "email_verify":
            subject = "🔐 Your Verification OTP - Kunyo Gears"
        elif purpose == "forgot_password":
            subject = "🔐 Your Password Reset OTP - Kunyo Gears"
        else:
            subject = "🔐 Your One-Time Password"

    if not message_html:
        message_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Hello,</h2>
            <p>Your One-Time Password (OTP) is:</p>
            <h1 style="color: #007bff; letter-spacing: 8px;">{otp}</h1>
            <p><strong>This OTP is valid for {int(expires_in_sec/60)} minutes only.</strong></p>
            <p>If you did not request this, please ignore this email.</p>
            <br>
            <p>Thank you,<br>
            <strong>Kunyo Gears Team</strong><br>
            <small>Powered by deskgoo.com</small>
            </p>
        </div>
        """

    try:
        email_queue = frappe.sendmail(
            recipients=[email],
            sender=sender,
            subject=subject,
            message=message_html,
            delayed=False,
            retry=1,
        )

        if email_queue:
            frappe.db.commit()

        return otp

    except Exception as e:
        frappe.log_error(f"OTP Send Failed for {email}: {str(e)}", "OTP Send Error")
        frappe.throw(_("Failed to send OTP. Please try again."), title=_("Email Error"))


def verify_otp(email: str, otp: str, purpose: str = "email_verify") -> bool:
    if not email or not otp:
        frappe.throw(_("Email and OTP are required"))

    cache_key = _cache_key(purpose, email)
    stored_otp = frappe.cache().get_value(cache_key)

    if not stored_otp:
        frappe.throw(_("OTP has expired or not found. Please request a new one."), title=_("Expired"))

    if str(stored_otp) != str(otp).strip():
        frappe.throw(_("Invalid OTP"), title=_("Verification Failed"))

    frappe.cache().delete_value(cache_key)
    return True
