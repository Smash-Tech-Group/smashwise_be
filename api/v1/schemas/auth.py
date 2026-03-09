from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re





class SignInRequest(BaseModel):
    """Schema for sign in request"""

    phone_number: str = Field(..., min_length=10, max_length=20)

    @validator("phone_number")
    def validate_phone_number(cls, v):
        v = v.strip().replace(" ", "").replace("-", "")

        if not re.match(r"^\+?[1-9]\d{1,14}$", v):
            raise ValueError("Invalid phone number format")

        if not v.startswith("+"):
            if v.startswith("0"):
                v = "+234" + v[1:]
            elif len(v) == 10:
                v = "+234" + v
            else:
                v = "+" + v

        return v
