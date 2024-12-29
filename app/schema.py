from pydantic import BaseModel,Field
from datetime import date
from enum import Enum
from typing import Optional, Union
import enum

class RegistrationTypeEnum(enum.Enum):
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    PROJECT_MANAGEMENT = "PROJECT_MANAGEMENT"
    COMMON_SIGNUP = "COMMON_SIGNUP"

class SocialMediaSignup(BaseModel):
    first_name: str = Field(..., min_length=1, description="First name is required")
    last_name: str = Field(..., min_length=1, description="Last name is required")
    mobile_number: str = Field(...,  description="Valid mobile number is required")
    hashtag: str = Field(..., min_length=1, description="Hashtag is required")

    class Config:
        from_attributes = True

class PlatformRegistration(BaseModel):
    first_name: str = Field(..., min_length=1, description="First name is required")
    last_name: str = Field(..., min_length=1, description="Last name is required")
    email: str = Field(..., description="Valid email address is required")
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    company_name: str = Field(None, min_length=1, description="Company name cannot be empty if provided")


    class Config:
        from_attributes = True

class BasicSignup(BaseModel):
    mobile_number: str = Field(..., description="Valid 10-digit mobile number is required")
    first_name: str = Field(..., min_length=1, description="First name is required")
    last_name: str = Field(..., min_length=1, description="Last name is required")
    dob: date = Field(..., description="Date of birth is required in YYYY-MM-DD format")

    class Config:
        from_attributes = True
        
UserRequest = Union[SocialMediaSignup, PlatformRegistration, BasicSignup]

class UserResponseUpdated(BaseModel):
    id: int
    user_data: UserRequest

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    type: RegistrationTypeEnum
    user_data: dict

    class Config:
        from_attributes = True
