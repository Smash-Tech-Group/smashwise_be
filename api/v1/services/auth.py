from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from fastapi import HTTPException, status
import secrets
import string
import bcrypt


from api.utils.jwt_handler import create_access_token
from passlib.context import CryptContext




class AuthService:
    """Authentication service for handling registration and login"""



# Create singleton instance
auth_service = AuthService()