from model import Session
from fastapi import APIRouter

route = APIRouter(prefix="/api/v1")


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
