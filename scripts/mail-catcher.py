#!/usr/bin/env python3
"""Lokaler Test-SMTP-Server fuer die Entwicklung (ohne Docker).

Faengt alle vom Backend versendeten E-Mails ab, speichert jede Nachricht als
.eml-Datei unter /tmp/beetle-mail/ und gibt einen eventuell enthaltenen
Verifizierungslink direkt (ungepuffert) auf der Konsole aus.

Hintergrund: Der eingebaute ``aiosmtpd``-Debugging-Server puffert seine Ausgabe
beim Umleiten in eine Datei, wodurch abgefangene Mails scheinbar "verschwinden".
Dieser kleine Catcher schreibt jede Mail sofort weg und flusht die Ausgabe.

Passt zu den Werten in restart-backend.sh: SMTP_HOST=127.0.0.1, SMTP_PORT=1025.

Nutzung:
    ~/beetle-venv/bin/python scripts/mail-catcher.py
"""
from __future__ import annotations

import asyncio
import email
import re
from datetime import datetime
from pathlib import Path

from aiosmtpd.controller import Controller

MAIL_DIR = Path("/tmp/beetle-mail")
LINK_PATTERN = re.compile(r"https?://\S*verify-email\S*")


class SaveToFileHandler:
    """Speichert jede eingehende Nachricht und protokolliert den Verify-Link."""

    async def handle_DATA(self, server, session, envelope):  # noqa: N802 (aiosmtpd-API)
        MAIL_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        recipients = ", ".join(envelope.rcpt_tos) or "unbekannt"

        # Rohnachricht ablegen, damit man sie bei Bedarf komplett ansehen kann.
        eml_path = MAIL_DIR / f"{timestamp}.eml"
        eml_path.write_bytes(envelope.content)

        # Klartext extrahieren und den Verifizierungslink herausziehen.
        message = email.message_from_bytes(envelope.content)
        body = _plain_text_body(message)
        match = LINK_PATTERN.search(body)

        print("=" * 70, flush=True)
        print(f"[{timestamp}] E-Mail abgefangen", flush=True)
        print(f"  An:         {recipients}", flush=True)
        print(f"  Betreff:    {message.get('Subject', '(kein Betreff)')}", flush=True)
        print(f"  Gespeichert: {eml_path}", flush=True)
        if match:
            print(f"  Verify-Link: {match.group(0)}", flush=True)
        else:
            print("  Verify-Link: (keiner gefunden)", flush=True)
        print("=" * 70, flush=True)

        return "250 Nachricht angenommen"


def _plain_text_body(message: email.message.Message) -> str:
    """Liefert den (dekodierten) Text-Teil der Nachricht."""
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
        return ""
    payload = message.get_payload(decode=True) or b""
    charset = message.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def main() -> None:
    controller = Controller(SaveToFileHandler(), hostname="127.0.0.1", port=1025)
    controller.start()
    print("Mail-Catcher laeuft auf 127.0.0.1:1025", flush=True)
    print(f"Abgefangene Mails werden in {MAIL_DIR} abgelegt.", flush=True)
    print("Zum Beenden Strg+C druecken.", flush=True)
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        controller.stop()
        print("\nMail-Catcher beendet.", flush=True)


if __name__ == "__main__":
    main()
