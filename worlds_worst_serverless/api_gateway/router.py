from fastapi import APIRouter

from api_gateway import api

api_router = APIRouter()
api_router.include_router(api.router)
