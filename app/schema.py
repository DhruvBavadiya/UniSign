from fastapi import HTTPException
from pydantic import BaseModel
from datetime import date
from typing import Optional,Type
from sqlalchemy import Enum
from app.models import RegistrationType

class SocialMediaSignup(BaseModel):
    mobile_number: str
    first_name: str
    last_name: str
    hashtag: str

    class Config:
        from_attributes = True

class PlatformRegistration(BaseModel):
    company_name: str
    first_name: str
    last_name: str
    email: str
    password: str

    class Config:
        from_attributes = True

class BasicSignup(BaseModel):
    mobile_number: str
    first_name: str
    last_name: str
    dob: str

    class Config:
        from_attributes = True

class RegistrationBase(BaseModel):
    type: RegistrationType
    mobile_number: Optional[str] = None
    first_name: str
    last_name: str
    email: Optional[str] = None
    password: Optional[str] = None
    company_name: Optional[str] = None
    dob: Optional[date] = None
    hashtag: Optional[str] = None

    class Config:
        from_attributes = True

class RegistrationResponse(RegistrationBase):
    id: int

    class Config:
        from_attributes = True


def validate_registration_type(data: dict, reg_type: RegistrationType) -> Type[BaseModel]:
    if reg_type == RegistrationType.SOCIAL_MEDIA:
        return SocialMediaSignup(**data)
    elif reg_type == RegistrationType.PROJECT_MANAGEMENT:
        return PlatformRegistration(**data)
    elif reg_type == RegistrationType.COMMON_SIGNUP:
        return BasicSignup(**data)
    else:
        raise HTTPException(status_code=400, detail="Invalid registration type")
