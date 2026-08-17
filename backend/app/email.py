"""Outbound transactional email (verification / password-reset codes).

Uses plain SMTP via stdlib smtplib, configured through env vars - no extra
dependency needed since Flask-Mail would just wrap the same thing. When
SMTP_HOST isn't set (e.g. local dev without a mail server configured) the
message is logged instead of sent, so the flow stays usable without setup;
watch the backend logs for the code in that case.
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

from app.codes import PURPOSE_CHANGE_EMAIL, PURPOSE_PASSWORD_RESET, PURPOSE_VERIFY_EMAIL

logger = logging.getLogger("app.email")

_SUBJECTS = {
    PURPOSE_VERIFY_EMAIL: "Confirm your email - Grade Tracker",
    PURPOSE_CHANGE_EMAIL: "Confirm your new email - Grade Tracker",
    PURPOSE_PASSWORD_RESET: "Reset your password - Grade Tracker",
}

_BODIES = {
    PURPOSE_VERIFY_EMAIL: (
        "Welcome to Grade Tracker!\n\n"
        "Your verification code is: {code}\n\n"
        "Enter it in the app to confirm your email address. "
        "This code expires in {ttl} minutes."
    ),
    PURPOSE_CHANGE_EMAIL: (
        "You asked to change the email on your Grade Tracker account to this address.\n\n"
        "Your verification code is: {code}\n\n"
        "Enter it in Account settings to confirm the change. Your current email stays "
        "active until you do. This code expires in {ttl} minutes. If you didn't request "
        "this, you can safely ignore this email."
    ),
    PURPOSE_PASSWORD_RESET: (
        "Someone requested a password reset for your Grade Tracker account.\n\n"
        "Your reset code is: {code}\n\n"
        "Enter it on the reset password page along with your new password. "
        "This code expires in {ttl} minutes. If you didn't request this, you can safely "
        "ignore this email - your password stays unchanged."
    ),
}


def send_email(to: str, subject: str, body: str) -> None:
    host = os.environ.get("SMTP_HOST")
    if not host:
        # WARNING, not INFO - the default logging config (here and in most
        # WSGI setups) drops INFO records, and this is the only place the
        # code becomes visible when SMTP isn't configured.
        logger.warning("SMTP not configured, not sending email to %s - %s\n%s", to, subject, body)
        return

    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM", user or "no-reply@localhost")
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() != "false"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = to
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            if use_tls:
                smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError):
        # Best-effort delivery: a mail-server hiccup shouldn't turn into a
        # 500 for an action (register, change email, ...) that already
        # committed successfully - the user can always request a resend.
        logger.exception("Failed to send email to %s", to)


def send_verification_code(to: str, purpose: str, code: str) -> None:
    from app.codes import CODE_TTL_MINUTES

    subject = _SUBJECTS[purpose]
    body = _BODIES[purpose].format(code=code, ttl=CODE_TTL_MINUTES)
    send_email(to, subject, body)
