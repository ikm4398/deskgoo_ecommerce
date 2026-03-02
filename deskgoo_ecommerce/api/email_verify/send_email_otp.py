# deskgoo_ecommerce/api/email_verify/send_email_otp.py

import frappe
import random
from frappe import _


@frappe.whitelist(allow_guest=True)
def send_email_otp(email: str):
    """
    Send 6-digit OTP to user's email using your configured Email Account
    (Name: "Email" | email_id: kunyo@deskgoo.com | domain: Kunyo Mail)
    """
    if not email or "@" not in email:
        frappe.throw(_("Valid email is required"), title=_("Invalid Email"))

    if frappe.db.exists("User", email):
        frappe.throw(_("This email is already registered"), title=_("Registration Failed"))

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))

    # Store OTP in Redis cache (valid for 10 minutes)
    cache_key = f"otp:email_verify:{email.lower()}"
    frappe.cache().set_value(cache_key, otp, expires_in_sec=600)

    # Get sender from your Email Account (automatically uses correct SMTP + domain)
    sender = frappe.get_value("Email Account", "Email", "email_id") or "kunyo@deskgoo.com"

    subject = "🔐 Your Verification OTP - Kunyo Gears"
    message = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Hello,</h2>
        <p>Your One-Time Password (OTP) for email verification is:</p>
        <h1 style="color: #007bff; letter-spacing: 8px;">{otp}</h1>
        <p><strong>This OTP is valid for 10 minutes only.</strong></p>
        <p>If you did not request this, please ignore this email.</p>
        <br>
        <p>Thank you,<br>
        <strong>Kunyo Gears Team</strong><br>
        <small>Powered by deskgoo.com</small>
        </p>
    </div>
    """

    try:
        frappe.sendmail(
            recipients=[email],
            sender=sender,
            subject=subject,
            message=message,
            delayed=False,          # send immediately
            retry=1
        )

        return {
            "status": "success",
            "message": _("OTP sent successfully to your email"),
            "email": email
        }

    except Exception as e:
        frappe.log_error(f"OTP Send Failed for {email}: {str(e)}", "Email OTP Error")
        frappe.throw(_("Failed to send OTP. Please try again."), title=_("Email Error"))