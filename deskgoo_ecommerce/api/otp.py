# deskgoo_ecommerce/api/otp.py
"""Central OTP module for sending and verifying OTPs.

This module re-exports the OTP functions from the send_otp module,
providing a centralized interface for all OTP operations across the application.
"""

from .send_otp.send_otp import send_otp, verify_otp, generate_otp

__all__ = ["send_otp", "verify_otp", "generate_otp"]
