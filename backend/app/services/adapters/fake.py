from __future__ import annotations

import hashlib

from app.services.adapters.base import (
    EligibilityResult,
    IntentPayload,
    OutcomeState,
    PreparedSubmission,
    SubmissionOutcome,
)


class FakeAdapter:
    """Deterministic fake adapter for TEST_ONLY / DISABLED simulation."""

    _SCENARIO_MAP: dict[str, OutcomeState] = {
        "accept_registered": OutcomeState.OFFICIALLY_REGISTERED,
        "transport_only": OutcomeState.PROVIDER_ACCEPTED,
        "reject": OutcomeState.REJECTED,
        "timeout_unknown": OutcomeState.UNKNOWN_OUTCOME,
        "duplicate": OutcomeState.PROVIDER_ACCEPTED,
    }

    def validate(self, intent: IntentPayload) -> EligibilityResult:
        if not intent.get("payload_hash"):
            return EligibilityResult(eligible=False, reason="missing payload_hash")
        return EligibilityResult(eligible=True)

    def prepare(self, intent: IntentPayload) -> PreparedSubmission:
        return PreparedSubmission(
            payload_hash=intent.get("payload_hash", ""),
            destination=intent.get("destination", "fake@example.test"),
        )

    def _resolve_state(self, intent: IntentPayload) -> OutcomeState:
        scenario = intent.get("scenario")
        if scenario and scenario in self._SCENARIO_MAP:
            return self._SCENARIO_MAP[scenario]

        digest = hashlib.sha256(intent.get("payload_hash", "").encode()).hexdigest()
        bucket = int(digest[:2], 16) % len(self._SCENARIO_MAP)
        return list(self._SCENARIO_MAP.values())[bucket]

    def submit(self, intent: IntentPayload, *, idempotency_key: str) -> SubmissionOutcome:
        state = self._resolve_state(intent)
        if state == OutcomeState.OFFICIALLY_REGISTERED:
            return SubmissionOutcome(
                state=state,
                message="Fake official registration",
                provider_message_id=f"fake-{idempotency_key[:8]}",
                official_reference=f"PMC-FAKE-{idempotency_key[:6].upper()}",
                tracking_url="https://example.test/track/fake",
            )
        if state == OutcomeState.PROVIDER_ACCEPTED:
            return SubmissionOutcome(
                state=state,
                message="Transport accepted; government registration not confirmed",
                provider_message_id=f"fake-{idempotency_key[:8]}",
            )
        if state == OutcomeState.REJECTED:
            return SubmissionOutcome(
                state=state,
                message="Fake recipient rejected submission",
                metadata={"error_code": "REJECTED"},
            )
        if state == OutcomeState.UNKNOWN_OUTCOME:
            return SubmissionOutcome(
                state=state,
                message="Fake transport timeout; outcome unknown",
                metadata={"unknown_outcome": True},
            )
        return SubmissionOutcome(state=OutcomeState.NOT_SENT, message="Not sent")

    def reconcile(self, intent: IntentPayload) -> SubmissionOutcome:
        return SubmissionOutcome(
            state=OutcomeState.ACKNOWLEDGED,
            message="Fake reconciliation acknowledged",
        )
