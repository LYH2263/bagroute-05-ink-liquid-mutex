from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.seed import seed_if_empty


def ensure_columns() -> None:
    """轻量加列：create_all 不会改已有表，这里补齐后加的 category 列。"""
    inspector = inspect(engine)
    existing = {t: {c["name"] for c in inspector.get_columns(t)} for t in inspector.get_table_names()}
    ddl = []
    if "subscriber_stops" in existing and "category" not in existing["subscriber_stops"]:
        ddl.append("ALTER TABLE subscriber_stops ADD COLUMN category VARCHAR(16) DEFAULT 'normal'")
    if "bag_items" in existing and "category" not in existing["bag_items"]:
        ddl.append("ALTER TABLE bag_items ADD COLUMN category VARCHAR(16) DEFAULT 'normal'")
    if ddl:
        with engine.begin() as conn:
            for stmt in ddl:
                conn.execute(text(stmt))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_columns()
    if settings.seed_on_empty:
        db = SessionLocal()
        try:
            seed_if_empty(db)
        finally:
            db.close()
    yield


app = FastAPI(title="BagRoute", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")
