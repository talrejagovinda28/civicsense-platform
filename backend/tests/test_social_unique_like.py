from sqlalchemy import func, select

from app.models.community import Like
from app.services.social import like_complaint, unlike_complaint


def test_like_unique_per_user(db, complaint):
    user_id = "liker_1"
    first = like_complaint(db, user_id=user_id, complaint_id=complaint.id)
    second = like_complaint(db, user_id=user_id, complaint_id=complaint.id)
    assert first.id == second.id

    count = db.scalar(
        select(func.count()).select_from(Like).where(
            Like.user_id == user_id,
            Like.complaint_id == complaint.id,
        )
    )
    assert count == 1

    unlike_complaint(db, user_id=user_id, complaint_id=complaint.id)
    count_after = db.scalar(
        select(func.count()).select_from(Like).where(
            Like.user_id == user_id,
            Like.complaint_id == complaint.id,
        )
    )
    assert count_after == 0
