import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_admin
from app.core.security import ClerkUser
from app.schemas.submission import (
    AttachReferenceRequest,
    AttestSentRequest,
    ConsentCreateRequest,
    ConsentResponse,
    DispatchRequest,
    DispatchResponse,
    ExternalReferenceResponse,
    IntentResponse,
    ReconcileRequest,
)
from app.services import submission_engine

router = APIRouter(tags=["submissions"])


@router.post("/complaints/{complaint_id}/authorization", response_model=ConsentResponse)
def create_authorization(
    complaint_id: uuid.UUID,
    payload: ConsentCreateRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ConsentResponse:
    consent = submission_engine.create_consent(
        db,
        user_id=current_user.user_id,
        complaint_id=complaint_id,
        channel_id=payload.channel_id,
        disclosure_json=payload.disclosure_json,
        scope=payload.scope,
    )
    return ConsentResponse.model_validate(consent)


@router.post("/complaints/{complaint_id}/submissions", response_model=DispatchResponse)
def dispatch_submission(
    complaint_id: uuid.UUID,
    payload: DispatchRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> DispatchResponse:
    result = submission_engine.create_intent_and_dispatch(
        db,
        user_id=current_user.user_id,
        complaint_id=complaint_id,
        consent_id=payload.consent_id,
        idempotency_key=payload.idempotency_key,
        test_scenario=payload.test_scenario,
    )
    return DispatchResponse(**result)


@router.post("/submissions/{intent_id}/attest-sent", response_model=IntentResponse)
def attest_submission_sent(
    intent_id: uuid.UUID,
    payload: AttestSentRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> IntentResponse:
    intent = submission_engine.attest_sent(
        db,
        user_id=current_user.user_id,
        intent_id=intent_id,
        attestation_note=payload.attestation_note,
    )
    return IntentResponse.model_validate(intent)


@router.post("/submissions/{intent_id}/reference", response_model=ExternalReferenceResponse)
def attach_submission_reference(
    intent_id: uuid.UUID,
    payload: AttachReferenceRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ExternalReferenceResponse:
    ref = submission_engine.attach_reference(
        db,
        user_id=current_user.user_id,
        intent_id=intent_id,
        reference_value=payload.reference_value,
        reference_type=payload.reference_type,
        tracking_url=payload.tracking_url,
    )
    return ExternalReferenceResponse.model_validate(ref)


@router.post("/submissions/{intent_id}/reconcile", response_model=IntentResponse)
def reconcile_submission(
    intent_id: uuid.UUID,
    payload: ReconcileRequest,
    db: Session = Depends(get_db),
    admin_user: ClerkUser = Depends(require_admin),
) -> IntentResponse:
    intent = submission_engine.reconcile_unknown(
        db,
        admin_user_id=admin_user.user_id,
        intent_id=intent_id,
        determination=payload.determination,
    )
    return IntentResponse.model_validate(intent)
