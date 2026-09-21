from fastapi import APIRouter, FastAPI


def register_routers(app: FastAPI, prefix: str) -> None:
    from app.routers import (
        accountability,
        admin,
        categories,
        chats,
        cities,
        complaints,
        feed,
        health,
        moderation,
        profiles,
        resolution,
        social,
        submissions,
        uploads,
        users,
    )

    routers: list[APIRouter] = [
        health.router,
        users.router,
        categories.router,
        cities.router,
        accountability.router,
        complaints.router,
        feed.router,
        social.router,
        profiles.router,
        chats.router,
        submissions.router,
        resolution.router,
        moderation.router,
        uploads.router,
        admin.router,
    ]
    for router in routers:
        app.include_router(router, prefix=prefix)
