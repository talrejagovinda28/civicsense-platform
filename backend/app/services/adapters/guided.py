from __future__ import annotations

from urllib.parse import quote

from app.services.adapters.base import (
    EligibilityResult,
    IntentPayload,
    OutcomeState,
    PreparedSubmission,
    SubmissionOutcome,
)


class GuidedPortalAdapter:
    """Never sends — returns composer/link instructions for citizen action."""

    def validate(self, intent: IntentPayload) -> EligibilityResult:
        return EligibilityResult(eligible=True)

    def prepare(self, intent: IntentPayload) -> PreparedSubmission:
        return PreparedSubmission(
            payload_hash=intent.get("payload_hash", ""),
            destination=intent.get("destination", ""),
            transport_metadata={"mode": "guided_portal"},
        )

    def submit(self, intent: IntentPayload, *, idempotency_key: str) -> SubmissionOutcome:
        url = intent.get("destination") or intent.get("url") or ""
        return SubmissionOutcome(
            state=OutcomeState.USER_ACTION_REQUIRED,
            message="Open the verified portal and submit your complaint manually.",
            metadata={
                "instructions": "Copy the prepared text, open the portal link, and file manually.",
                "portal_url": url,
                "composer_text": intent.get("disclosure", {}),
            },
        )

    def reconcile(self, intent: IntentPayload) -> SubmissionOutcome:
        return SubmissionOutcome(
            state=OutcomeState.USER_ACTION_REQUIRED,
            message="Awaiting citizen attestation or reference.",
        )


class GuidedWhatsAppAdapter:
    """Never sends — returns wa.me link with prefilled message."""

    def validate(self, intent: IntentPayload) -> EligibilityResult:
        return EligibilityResult(eligible=True)

    def prepare(self, intent: IntentPayload) -> PreparedSubmission:
        return PreparedSubmission(
            payload_hash=intent.get("payload_hash", ""),
            destination=intent.get("destination", ""),
            transport_metadata={"mode": "guided_whatsapp"},
        )

    def submit(self, intent: IntentPayload, *, idempotency_key: str) -> SubmissionOutcome:
        phone = (intent.get("destination") or "").lstrip("+")
        text = intent.get("disclosure", {}).get("summary", "CivicSense complaint handoff")
        wa_link = f"https://wa.me/{phone}?text={quote(str(text))}" if phone else ""
        return SubmissionOutcome(
            state=OutcomeState.USER_ACTION_REQUIRED,
            message="Open WhatsApp composer and send the message yourself.",
            metadata={
                "instructions": "Tap the link, review the prefilled message, and send manually.",
                "whatsapp_url": wa_link,
            },
        )

    def reconcile(self, intent: IntentPayload) -> SubmissionOutcome:
        return SubmissionOutcome(
            state=OutcomeState.USER_ACTION_REQUIRED,
            message="Awaiting citizen attestation that WhatsApp message was sent.",
        )
