from sqlalchemy import func, select

from app.models.submission import SubmissionAttempt, SubmissionIntent
from app.services.submission_engine import IntentStatus, create_intent_and_dispatch


def test_unknown_outcome_idempotent_no_second_attempt(db, complaint, consent, test_channel):
    key = "idem-unknown-001"
    first = create_intent_and_dispatch(
        db,
        user_id=complaint.user_id,
        complaint_id=complaint.id,
        consent_id=consent.id,
        idempotency_key=key,
        test_scenario="timeout_unknown",
    )
    assert first["outcome_state"] == IntentStatus.UNKNOWN_OUTCOME
    assert first["unknown_outcome"] is True

    attempt_count = db.scalar(select(func.count()).select_from(SubmissionAttempt))
    assert attempt_count == 1

    replay = create_intent_and_dispatch(
        db,
        user_id=complaint.user_id,
        complaint_id=complaint.id,
        consent_id=consent.id,
        idempotency_key=key,
        test_scenario="timeout_unknown",
    )
    assert replay["idempotent_replay"] is True
    assert replay["status"] == IntentStatus.UNKNOWN_OUTCOME

    attempt_count_after = db.scalar(select(func.count()).select_from(SubmissionAttempt))
    assert attempt_count_after == 1

    intent = db.scalar(select(SubmissionIntent).where(SubmissionIntent.idempotency_key == key))
    assert intent is not None
    assert intent.status == IntentStatus.UNKNOWN_OUTCOME
