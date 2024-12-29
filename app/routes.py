from fastapi import APIRouter, HTTPException, Depends
from pydantic import ValidationError
from sqlalchemy.orm import Session
from typing import Union

from .database import get_db
from sqlalchemy.exc import SQLAlchemyError
from .models import (
    UserTable, SocialMediaData, PlatformRegistrationData, BasicSignupData, RegistrationType
)
from .schema import (
    SocialMediaSignup, PlatformRegistration, BasicSignup, UserRequest, UserResponse, UserResponseUpdated
)

router = APIRouter()

def create_user_data(data: Union[SocialMediaSignup, PlatformRegistration, BasicSignup], reg_type: RegistrationType, db: Session):
    print(reg_type, "reg_type")
    if reg_type == RegistrationType.SOCIAL_MEDIA:
        existing_user = db.query(SocialMediaData).filter(SocialMediaData.mobile_number == data.mobile_number).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this mobile number already exists")
        user_data = SocialMediaData(
            mobile_number=data.mobile_number,
            first_name=data.first_name,
            last_name=data.last_name,
            hashtag=data.hashtag,
        )
    elif reg_type == RegistrationType.PROJECT_MANAGEMENT:
        existing_user = db.query(PlatformRegistrationData).filter(PlatformRegistrationData.email == data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        user_data = PlatformRegistrationData(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password=data.password,
            company_name=data.company_name,
        )
    elif reg_type == RegistrationType.COMMON_SIGNUP:
        existing_user = db.query(BasicSignupData).filter(BasicSignupData.mobile_number == data.mobile_number).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this mobile number already exists")
        user_data = BasicSignupData(
            mobile_number=data.mobile_number,
            first_name=data.first_name,
            last_name=data.last_name,
            dob=data.dob,
        )
    else:
        raise HTTPException(status_code=400, detail=f'Invalid registration type or data is not correct')
    
    db.add(user_data)
    db.commit()  
    db.refresh(user_data)  
    
    print(user_data.id, "user_specific_data_id")  
    
    return user_data


# add user route
@router.post("/add_user",response_model=UserResponseUpdated)
def register_user(data: UserRequest, db: Session = Depends(get_db)):
    reg_type = None
    valid_data = None
    user_entry = None
    user_specific_data = None
    print(data, "data")
    # data = data.model_dump()

    try:
        valid_data = SocialMediaSignup(**data.dict())
        reg_type = RegistrationType.SOCIAL_MEDIA
    except ValidationError:
        pass

    if not reg_type:
        try:
            valid_data = PlatformRegistration(**data.dict())
            reg_type = RegistrationType.PROJECT_MANAGEMENT
        except ValidationError:
            pass

    if not reg_type:
        try:
            valid_data = BasicSignup(**data.dict())
            reg_type = RegistrationType.COMMON_SIGNUP
        except ValidationError:
            pass

    if not reg_type:
        raise HTTPException(status_code=400, detail="Invalid registration type")

    try:
        user_entry = UserTable(type=reg_type)
        db.add(user_entry)
        db.commit()  
        
        try:
            user_specific_data = create_user_data(valid_data, reg_type, db)
            print(user_specific_data, "user_specific_data")
            print(user_specific_data.id, "user_specific_data_id")
        except Exception as e:
            db.delete(user_entry)  
            db.commit()  
            raise HTTPException(status_code=400, detail=f"Error creating specific data: {e}")

        if reg_type == RegistrationType.SOCIAL_MEDIA:
            user_entry.social_media_id = user_specific_data.id
        elif reg_type == RegistrationType.PROJECT_MANAGEMENT:
            user_entry.platform_registration_id = user_specific_data.id
        elif reg_type == RegistrationType.COMMON_SIGNUP:
            user_entry.basic_signup_id = user_specific_data.id

        db.commit()
        db.refresh(user_entry)
        db.refresh(user_specific_data)


    except SQLAlchemyError as e:
        if user_entry:
            db.delete(user_entry)  
            db.commit()
        raise HTTPException(status_code=400, detail=f"Error creating user entry: {e}")
    user_specific_data_dict = {key: value for key, value in user_specific_data.__dict__.items() if not key.startswith('_')}

    user_specific_data_without_id = {key: value for key, value in user_specific_data_dict.items() if key != "id"}
    print(user_specific_data_without_id, "user_specific_data_without_id")
    response = {
        "id": user_entry.id,
        "user_data": user_specific_data_without_id
    }
    return response

# update user route
@router.put("/update_user/{user_id}/")
def update_user(user_id: int, data: dict, db: Session = Depends(get_db)):
    try:
        user = db.query(UserTable).filter(UserTable.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        allowed_fields_by_type = {
            RegistrationType.SOCIAL_MEDIA: {"first_name", "last_name", "mobile_number", "hashtag"},
            RegistrationType.PROJECT_MANAGEMENT: {"first_name", "last_name", "email", "password", "company_name"},
            RegistrationType.COMMON_SIGNUP: {"first_name", "last_name", "mobile_number", "dob"}
        }
        
        allowed_fields = allowed_fields_by_type.get(user.type, set())
        
        extra_fields = [key for key in data.keys() if key not in allowed_fields]
        if extra_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid fields provided: {extra_fields}. Allowed fields: {list(allowed_fields)}"
            )
        
        if user.type == RegistrationType.SOCIAL_MEDIA:
            user_data = db.query(SocialMediaData).filter(SocialMediaData.id == user.social_media_id).first()
        elif user.type == RegistrationType.PROJECT_MANAGEMENT:
            user_data = db.query(PlatformRegistrationData).filter(PlatformRegistrationData.id == user.platform_registration_id).first()
        elif user.type == RegistrationType.COMMON_SIGNUP:
            user_data = db.query(BasicSignupData).filter(BasicSignupData.id == user.basic_signup_id).first()
        else:
            raise HTTPException(status_code=400, detail="Unsupported registration type")
        
        if not user_data:
            raise HTTPException(status_code=404, detail=f"No data found for user type {user.type}")
        
        for key, value in data.items():
            if hasattr(user_data, key):
                setattr(user_data, key, value)
        
        db.commit()
        db.refresh(user_data)
        
        return {"message": "User updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating user: {e}")

# delete user route
@router.delete("/delete_user/{user_id}/")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(UserTable).filter(UserTable.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.type == RegistrationType.SOCIAL_MEDIA:
            user_data = db.query(SocialMediaData).filter(SocialMediaData.id == user.social_media_id).first()
        elif user.type == RegistrationType.PROJECT_MANAGEMENT:
            user_data = db.query(PlatformRegistrationData).filter(PlatformRegistrationData.id == user.platform_registration_id).first()
        elif user.type == RegistrationType.COMMON_SIGNUP:
            user_data = db.query(BasicSignupData).filter(BasicSignupData.id == user.basic_signup_id).first()
        else:
            raise HTTPException(status_code=400, detail="Unsupported registration type")
        
        if user_data:
            db.delete(user_data)
        
        db.delete(user)
        db.commit()
        
        return {"message": f"User with ID {user_id} has been deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deleting user: {e}")

# get user route
@router.get("/get_user/{user_id}/",response_model=UserResponseUpdated)
def get_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(UserTable).filter(UserTable.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.type == RegistrationType.SOCIAL_MEDIA:
            user_data = db.query(SocialMediaData).filter(SocialMediaData.id == user.social_media_id).first()
        elif user.type == RegistrationType.PROJECT_MANAGEMENT:
            user_data = db.query(PlatformRegistrationData).filter(PlatformRegistrationData.id == user.platform_registration_id).first()
        elif user.type == RegistrationType.COMMON_SIGNUP:
            user_data = db.query(BasicSignupData).filter(BasicSignupData.id == user.basic_signup_id).first()
        else:
            raise HTTPException(status_code=400, detail="Unsupported registration type")
        
        if not user_data:
            raise HTTPException(status_code=404, detail=f"No data found for user type {user.type}")
        
        user_data = {key: value for key, value in user_data.__dict__.items() if not key.startswith('_')}

        user_data = {key: value for key, value in user_data.items() if key != "id"}
        response = {
            "id": user.id,
            "user_data": user_data
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching user data: {e}")
