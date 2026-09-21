from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.complaint import Complaint, VerificationState
from app.models.resolution import ResolutionEvidence, ResolutionEvidenceStatus, ResolutionReview
from app.services.reputation import EVIDENCE_XP, RESOLUTION_XP, grant_xp


def submit_evidence(
    db: Session,
    *,
    user_id: str,
    complaint_id: uuid.UUID,
    assertion: str,
    submitter_role: str,
    media_url: str | None = None,
) -> ResolutionEvidence:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    evidence = ResolutionEvidence(
        complaint_id=complaint_id,
        submitter_id=user_id,
        submitter_role=submitter_role,
        assertion=assertion.strip(),
        media_url=media_url,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def reporter_confirm(
    db: Session,
    *,
    user_id: str,
    complaint_id: uuid.UUID,
    confirmed: bool,
    reason: str | None = None,
) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    if complaint.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Reporter only")

    complaint.verification_state = (
        VerificationState.CONFIRMED_BY_REPORTER if confirmed else VerificationState.DISPUTED
    )

    db.add(
        ResolutionReview(
            complaint_id=complaint_id,
            decision="reporter_confirmed" if confirmed else "reporter_disputed",
            reason=reason or "",
            reviewer_id=user_id,
        )
    )
    db.commit()
    db.refresh(complaint)
    return complaint


def independent_review(
    db: Session,
    *,
    reviewer_id: str,
    reviewer_role: str,
    complaint_id: uuid.UUID,
    evidence_id: uuid.UUID | None,
    decision: str,
    reason: str | None = None,
) -> ResolutionReview:
    if reviewer_role not in {"officer", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Independent review requires officer or admin role",
        )

    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    if reviewer_role != "admin" and complaint.user_id == reviewer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reporter cannot independently verify own case",
        )

    evidence: ResolutionEvidence | None = None
    if evidence_id is not None:
        evidence = db.get(ResolutionEvidence, evidence_id)
        if evidence is None or evidence.complaint_id != complaint_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
        if reviewer_role == "officer" and evidence.submitter_id == reviewer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Officer cannot independently verify own fix evidence",
            )

    review = ResolutionReview(
        complaint_id=complaint_id,
        evidence_id=evidence_id,
        decision=decision,
        reason=reason or "",
        reviewer_id=reviewer_id,
    )
    db.add(review)

    if decision == "verified_resolved":
        complaint.verification_state = VerificationState.VERIFIED
        grant_xp(
            db,
            user_id=complaint.user_id,
            event_key=f"resolution_verified:{complaint_id}",
            kind="resolution",
            delta=RESOLUTION_XP,
            source_entity_id=str(complaint_id),
        )
        if evidence is not None:
            evidence.status = ResolutionEvidenceStatus.ACCEPTED
            grant_xp(
                db,
                user_id=evidence.submitter_id,
                event_key=f"evidence:{evidence.id}",
                kind="evidence",
                delta=EVIDENCE_XP,
                source_entity_id=str(evidence.id),
            )
    elif decision == "accepted" and evidence is not None:
        evidence.status = ResolutionEvidenceStatus.ACCEPTED
        grant_xp(
            db,
            user_id=evidence.submitter_id,
            event_key=f"evidence:{evidence.id}",
            kind="evidence",
            delta=EVIDENCE_XP,
            source_entity_id=str(evidence.id),
        )
    elif decision == "rejected":
        if evidence is not None:
            evidence.status = ResolutionEvidenceStatus.REJECTED
        complaint.verification_state = VerificationState.DISPUTED

    db.commit()
    db.refresh(review)
    return review
