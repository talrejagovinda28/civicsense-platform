from fastapi import APIRouter, FastAPI


def register_routers(app: FastAPI, prefix: str) -> None:
    from app.routers import admin, categories, cities, complaints, health, uploads, users

    routers: list[APIRouter] = [
        health.router,
        users.router,
        categories.router,
        cities.router,
        complaints.router,
        uploads.router,
        admin.router,
    ]
    for router in routers:
        app.include_router(router, prefix=prefix)
