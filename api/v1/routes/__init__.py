"""
Routes Registration
File: api/v1/routes/__init__.py

"""
from fastapi import APIRouter

from api.v1.routes.auth_route import auth


api_version_one = APIRouter(prefix="/api/v1")


api_version_one.include_router(auth)
