"""Versand von E-Mail-Verifizierungsnachrichten ueber den konfigurierten SMTP-Anbieter."""

import smtplib
from email.message import EmailMessage

from backend.config.settings import (
    get_email_verification_base_url,
    get_smtp_from_email,
    get_smtp_host,
    get_smtp_password,
    get_smtp_port,
    get_smtp_username,
    use_smtp_ssl,
    use_smtp_starttls,
)


def build_verification_link(verification_token: str) -> str:
    """Baut eine oeffentliche Verifizierungs-URL fuer einen Token."""
    base = get_email_verification_base_url().rstrip("/")
    return f"{base}/verify-email?token={verification_token}"


def send_verification_email(email: str, verification_token: str) -> None:
    """Versendet eine Verifizierungs-E-Mail ueber den konfigurierten SMTP-Anbieter."""
    smtp_host = get_smtp_host()
    if not smtp_host:
        raise RuntimeError("SMTP_HOST is missing.")

    verification_link = build_verification_link(verification_token)

    msg = EmailMessage()
    msg["Subject"] = "BeetleAtlas: Bitte E-Mail bestaetigen"
    msg["From"] = get_smtp_from_email()
    msg["To"] = email
    msg.set_content(
        "Hallo,\n\n"
        "bitte bestaetige deine E-Mail-Adresse, um deinen BeetleAtlas-Account zu aktivieren:\n\n"
        f"{verification_link}\n\n"
        "Falls du dich nicht registriert hast, ignoriere diese Nachricht.\n"
    )

    smtp_port = get_smtp_port()
    smtp_user = get_smtp_username()
    smtp_password = get_smtp_password()

    if use_smtp_ssl():
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as smtp:
            if smtp_user:
                smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)
        return

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
        if use_smtp_starttls():
            smtp.starttls()
        if smtp_user:
            smtp.login(smtp_user, smtp_password)
        smtp.send_message(msg)
