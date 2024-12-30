# FastAPI User Registration API

## Overview
This API provides an interface for user registration through three different registration types: **Social Media**, **Platform Registration**, and **Basic Signup**. It uses SQLAlchemy to interact with a PostgreSQL database, and FastAPI to handle the HTTP requests.

## API Routes

### 1. **Create User**

- **Endpoint:** `POST /add_user`
- **Description:** This endpoint creates a user based on the data provided in the request body. 

#### Request Body:
The request body must contain the registration type and the user-specific data based on the type. It will accept one of the following models:

1. **Social Media Registration**
   ```json
   {
     "first_name": "string",
     "last_name": "string",
     "mobile_number": "string",
     "hashtag": "string"
   }
2. **PlatformRegistration Registration**
   ```json
    {
      "first_name": "string",
      "last_name": "string",
      "email": "string",
      "password": "string",
      "company_name": "string"
    }

3. **BasicRegistraion Registration**
   ```json
   {
    "mobile_number": "string",
    "first_name": "string",
    "last_name": "string",
    "dob": "YYYY-MM-DD"
   }

#### Responce:
The response will accept one of the following models:

1. **Social Media Registration**
   ```json
   {
    "id": 1,
    "type": "SOCIAL_MEDIA",
    "user_data": {
        "first_name": "string",
        "last_name": "string",
        "mobile_number": "string",
        "hashtag": "string"
    }
   }
2. **PlatformRegistration Registration**
   ```json
    {
    "id": 2,
    "type": "PROJECT_MANAGEMENT",
    "user_data": {
        "first_name": "string",
        "last_name": "string",
        "email": "string",
        "password": "string",
        "company_name": "string"
        }
    }

3. **BasicRegistraion Registration**
   ```json
   {
    "id": 3,
    "type": "COMMON_SIGNUP",
    "user_data": {
        "mobile_number": "string",
        "first_name": "string",
        "last_name": "string",
        "dob": "YYYY-MM-DD"
        }
   }
   
### 2. **Get User**

- **Endpoint:** `GET /get_user/{user_id}`
- **Description:** This endpoint get a user based on the user id provided in the params.

### 3. **Update User**

- **Endpoint:** `PUT /update_user/{user_id}`
- **Description:** This endpoint updates a user based on data provided in the request body and user_id.
 
### 3. **Delete User**

- **Endpoint:** `DELETE /delete_user/{user_id}`
- **Description:** This endpoint deletes a user based on the user id provided in the params.
