from ..verify_otp.verify_otp import verify_email_otp


# Expose the email verification endpoint through the email_verify package.
# This keeps the public API path stable while using centralized OTP verification logic.
