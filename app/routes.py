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
    SocialMediaSignup, PlatformRegistration, BasicSignup, UserResponse
)

router = APIRouter()

# Helper function to create type-specific data
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
    
    # Add the user data to the session
    db.add(user_data)
    db.commit()  # Commit the data to make it persistent
    db.refresh(user_data)  # Refresh the object to get the id
    
    print(user_data.id, "user_specific_data_id")  # This should print the id after commit and refresh
    
    return user_data

@router.post("/add_user/")
def register_user(data: dict, db: Session = Depends(get_db)):
    reg_type = None
    valid_data = None
    user_entry = None
    user_specific_data = None

    # Determine the registration type and data schema
    try:
        valid_data = SocialMediaSignup(**data)
        reg_type = RegistrationType.SOCIAL_MEDIA
    except ValidationError:
        pass

    if not reg_type:
        try:
            valid_data = PlatformRegistration(**data)
            reg_type = RegistrationType.PROJECT_MANAGEMENT
        except ValidationError:
            pass

    if not reg_type:
        try:
            valid_data = BasicSignup(**data)
            reg_type = RegistrationType.COMMON_SIGNUP
        except ValidationError:
            pass

    if not reg_type:
        raise HTTPException(status_code=400, detail="Invalid registration type")

    try:
        # Create the UserTable entry
        user_entry = UserTable(type=reg_type)
        db.add(user_entry)
        db.commit()  # Commit the UserTable entry
        
        # Create the user-specific data entry based on the registration type
        try:
            user_specific_data = create_user_data(valid_data, reg_type, db)
            print(user_specific_data, "user_specific_data")
            print(user_specific_data.id, "user_specific_data_id")
        except Exception as e:
            # Rollback user table creation and raise the exception
            db.delete(user_entry)  # Delete the user entry if user-specific data creation fails
            db.commit()  # Commit the deletion
            raise HTTPException(status_code=400, detail=f"Error creating specific data: {e}")

        # Set the correct foreign key based on the registration type
        if reg_type == RegistrationType.SOCIAL_MEDIA:
            user_entry.social_media_id = user_specific_data.id
        elif reg_type == RegistrationType.PROJECT_MANAGEMENT:
            user_entry.platform_registration_id = user_specific_data.id
        elif reg_type == RegistrationType.COMMON_SIGNUP:
            user_entry.basic_signup_id = user_specific_data.id

        # Commit the changes after both UserTable and user-specific data are created
        db.commit()
        db.refresh(user_entry)
        db.refresh(user_specific_data)


    except SQLAlchemyError as e:
        # Rollback and delete the user entry if something goes wrong
        if user_entry:
            db.delete(user_entry)  # Delete the user entry if there was an error
            db.commit()
        raise HTTPException(status_code=400, detail=f"Error creating user entry: {e}")

    # Prepare and return the response
    response = {
        "id": user_entry.id,
        "type": user_entry.type,
        "user_data": user_specific_data
    }
    return response


@router.put("/update_user/{user_id}/")
def update_user(user_id: int, data: dict, db: Session = Depends(get_db)):
    try:
    # Retrieve user record
        user = db.query(UserTable).filter(UserTable.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Define allowed fields for each registration type
        allowed_fields_by_type = {
            RegistrationType.SOCIAL_MEDIA: {"first_name", "last_name", "mobile_number", "hashtag"},
            RegistrationType.PROJECT_MANAGEMENT: {"first_name", "last_name", "email", "password", "company_name"},
            RegistrationType.COMMON_SIGNUP: {"first_name", "last_name", "mobile_number", "dob"}
        }
        
        # Get allowed fields for the current user type
        allowed_fields = allowed_fields_by_type.get(user.type, set())
        
        # Identify any extra fields in the request that are not allowed for the user type
        extra_fields = [key for key in data.keys() if key not in allowed_fields]
        if extra_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid fields provided: {extra_fields}. Allowed fields: {list(allowed_fields)}"
            )
        
        # Fetch type-specific data
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
        
        # Update the fields in the user_data model
        for key, value in data.items():
            if hasattr(user_data, key):
                setattr(user_data, key, value)
        
        # Commit the changes and refresh the user data
        db.commit()
        db.refresh(user_data)
        
        return {"message": "User updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating user: {e}")

@router.delete("/delete_user/{user_id}/")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        # Retrieve the user record
        user = db.query(UserTable).filter(UserTable.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete type-specific data first
        if user.type == RegistrationType.SOCIAL_MEDIA:
            user_data = db.query(SocialMediaData).filter(SocialMediaData.id == user.social_media_id).first()
        elif user.type == RegistrationType.PROJECT_MANAGEMENT:
            user_data = db.query(PlatformRegistrationData).filter(PlatformRegistrationData.id == user.platform_registration_id).first()
        elif user.type == RegistrationType.COMMON_SIGNUP:
            user_data = db.query(BasicSignupData).filter(BasicSignupData.id == user.basic_signup_id).first()
        else:
            raise HTTPException(status_code=400, detail="Unsupported registration type")
        
        # Delete the type-specific data
        if user_data:
            db.delete(user_data)
        
        # Delete the main user entry
        db.delete(user)
        db.commit()
        
        return {"message": f"User with ID {user_id} has been deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deleting user: {e}")

@router.get("/get_user/{user_id}/")
def get_user(user_id: int, db: Session = Depends(get_db)):
    try:
        # Retrieve the user record
        user = db.query(UserTable).filter(UserTable.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Fetch type-specific data based on the user type
        if user.type == RegistrationType.SOCIAL_MEDIA:
            user_data = db.query(SocialMediaData).filter(SocialMediaData.id == user.social_media_id).first()
        elif user.type == RegistrationType.PROJECT_MANAGEMENT:
            user_data = db.query(PlatformRegistrationData).filter(PlatformRegistrationData.id == user.platform_registration_id).first()
        elif user.type == RegistrationType.COMMON_SIGNUP:
            user_data = db.query(BasicSignupData).filter(BasicSignupData.id == user.basic_signup_id).first()
        else:
            raise HTTPException(status_code=400, detail="Unsupported registration type")
        
        # If no user data is found, raise an error
        if not user_data:
            raise HTTPException(status_code=404, detail=f"No data found for user type {user.type}")
        
        # Prepare the response with the user and user-specific data
        response = {
            "id": user.id,
            "type": user.type,
            "user_data": user_data
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching user data: {e}")
