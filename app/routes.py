from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Registration, RegistrationType
from app.schema import RegistrationResponse, SocialMediaSignup, PlatformRegistration, BasicSignup
from pydantic import ValidationError

router = APIRouter()

@router.post("/add_user")
async def register(data: dict, db: Session = Depends(get_db)):
    reg_type = None
    valid_data = None

    try:
        # Try matching with SocialMediaSignup
        valid_data = SocialMediaSignup(**data)
        reg_type = RegistrationType.SOCIAL_MEDIA
    except ValidationError:
        pass  # If it fails, continue to the next schema

    if not reg_type:  # Only try the next schema if no match was found yet
        try:
            # Try matching with PlatformRegistration
            valid_data = PlatformRegistration(**data)
            reg_type = RegistrationType.PROJECT_MANAGEMENT
        except ValidationError:
            pass  # If it fails, continue to the next schema

    if not reg_type:  # Only try the next schema if no match was found yet
        try:
            # Try matching with BasicSignup
            valid_data = BasicSignup(**data)
            reg_type = RegistrationType.COMMON_SIGNUP
        except ValidationError:
            pass  # If it fails, we can't match the data with any schema

    if not reg_type:
        # If no match was found, raise an error
        raise HTTPException(status_code=400, detail="Invalid data format for registration")

    # Step 2: Prepare registration data for DB insertion
    registration_data = {
        "type": reg_type,
        "mobile_number": valid_data.mobile_number if reg_type in [RegistrationType.SOCIAL_MEDIA, RegistrationType.COMMON_SIGNUP] else None,
        "first_name": valid_data.first_name,
        "last_name": valid_data.last_name,
        "email": valid_data.email if reg_type == RegistrationType.PROJECT_MANAGEMENT else None,
        "password": valid_data.password if reg_type == RegistrationType.PROJECT_MANAGEMENT else None,
        "company_name": valid_data.company_name if reg_type == RegistrationType.PROJECT_MANAGEMENT else None,
        "dob": valid_data.dob if reg_type == RegistrationType.COMMON_SIGNUP else None,
        "hashtag": valid_data.hashtag if reg_type == RegistrationType.SOCIAL_MEDIA else None,
    }

    print(reg_type)

    # Step 3: Create a registration instance in DB
# Start a transaction
    try:
        # Begin a new transaction
        with db.begin():  # This automatically handles commit and rollback
            db_registration = Registration(**registration_data)
            print("1")
            db.add(db_registration)
            print("2")

            db.commit()  # Commit the transaction
            print("3")
            # db.refresh(db_registration)  # Refresh the instance after commit
            # print("4")


        if reg_type == RegistrationType.SOCIAL_MEDIA:
            # return {
            # "id": db_registration.id,
            # "first_name": db_registration.first_name,
            # "last_name": db_registration.last_name,
            # "email": db_registration.email,
            # "hashtag": db_registration.hashtag,
            # }
            return SocialMediaSignup(
                id=db_registration.id,
                first_name=db_registration.first_name,
                last_name=db_registration.last_name,
                mobile_number=db_registration.mobile_number,
                hashtag=db_registration.hashtag
            )
        elif reg_type == RegistrationType.PROJECT_MANAGEMENT:
             return PlatformRegistration(
                            # id=db_registration.id,
                            first_name=db_registration.first_name,
                            last_name=db_registration.last_name,
                            email=db_registration.email,
                            company_name=db_registration.company_name,
                            password=db_registration.password
                        )
        elif reg_type == RegistrationType.COMMON_SIGNUP:

                return BasicSignup(
                    # id=db_registration.id,
                    first_name=db_registration.first_name,
                    last_name=db_registration.last_name,
                    mobile_number=db_registration.mobile_number,
                    dob=db_registration.dob.strftime('%Y-%m-%d') if db_registration.dob else None
                )
    except Exception as e:
        # If any exception occurs, it will rollback automatically due to db.begin()
        raise HTTPException(status_code=500, detail=f'Error processing registration : ${e}')

@router.get("/get_user/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):        
    user = db.query(Registration).filter(Registration.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    excluded_fields = {'type', 'password'}
    response = {
        column: getattr(user, column) 
        for column in user.__table__.columns.keys()
        if getattr(user, column) is not None and column not in excluded_fields
    }
    
    return response

@router.put("/update_user/{user_id}")
async def update_user(user_id: int, data: dict, db: Session = Depends(get_db)):
    try:
        # Fetch the user by ID
        user = db.query(Registration).filter(Registration.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Define allowed fields for each registration type
        allowed_fields_by_type = {
            RegistrationType.SOCIAL_MEDIA: {"first_name", "last_name", "mobile_number", "hashtag"},
            RegistrationType.PROJECT_MANAGEMENT: {"first_name", "last_name", "email", "password", "company_name"},
            RegistrationType.COMMON_SIGNUP: {"first_name", "last_name", "mobile_number", "dob"}
        }

        # Get allowed fields for the user's type
        allowed_fields = allowed_fields_by_type.get(user.type, set())

        extra_fields = [key for key in data.keys() if key not in allowed_fields]
        if extra_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid fields provided: {extra_fields}. Allowed fields: {allowed_fields}"
            )


        # Filter incoming data for allowed fields
        update_data = {key: value for key, value in data.items() if key in allowed_fields}

        # If no valid fields are provided, raise an error
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail=f"No valid fields to update for type {user.type}."
            )

        # Update the user with valid fields
        for key, value in update_data.items():
            setattr(user, key, value)

        # Commit the changes to the database
        db.commit()
        db.refresh(user)

        return {
            "message": "User updated successfully",
            "updated_fields": update_data
        }
    except Exception as e:
        return {
            "message": "An error occurred while updating the user",
            "error": str(e)
        }
    
    
@router.delete("/delete_user/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        # Fetch the user by ID
        user = db.query(Registration).filter(Registration.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete the user
        db.delete(user)
        db.commit()
        
        return {"message": f"User with ID {user_id} has been deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
