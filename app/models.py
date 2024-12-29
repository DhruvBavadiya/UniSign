import re
from sqlalchemy import Column, Integer, String, Enum, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base
import enum
from sqlalchemy.orm import validates



# Define an enum for registration types
class RegistrationType(enum.Enum):
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    PROJECT_MANAGEMENT = "PROJECT_MANAGEMENT"
    COMMON_SIGNUP = "COMMON_SIGNUP"

class UserTable(Base):
    __tablename__ = 'user_table'

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(RegistrationType), nullable=False)  # Use Enum here
    
    social_media_id = Column(Integer, ForeignKey('social_media_data.id', ondelete='CASCADE'))
    platform_registration_id = Column(Integer, ForeignKey('platform_registration_data.id', ondelete='CASCADE'))
    basic_signup_id = Column(Integer, ForeignKey('basic_signup_data.id', ondelete='CASCADE'))

    # Define relationships
    social_media_data = relationship("SocialMediaData", back_populates="user", uselist=False, cascade="all, delete")
    platform_registration_data = relationship("PlatformRegistrationData", back_populates="user", uselist=False, cascade="all, delete")
    basic_signup_data = relationship("BasicSignupData", back_populates="user", uselist=False, cascade="all, delete")

    @property
    def user_specific_data(self):
        # Conditionally return the related data based on the user type
        if self.type == RegistrationType.SOCIAL_MEDIA:
            return self.social_media_data
        elif self.type == RegistrationType.PROJECT_MANAGEMENT:
            return self.platform_registration_data
        elif self.type == RegistrationType.COMMON_SIGNUP:
            return self.basic_signup_data
        return None


class SocialMediaData(Base):
    __tablename__ = "social_media_data"
    id = Column(Integer, primary_key=True, index=True)
    mobile_number = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashtag = Column(String, nullable=True)

    # Relationship back to UserTable
    user = relationship("UserTable", back_populates="social_media_data")

    __table_args__ = (
        UniqueConstraint('mobile_number', name='uix_mobile_number_type'),
    )
    @validates('mobile_number')
    def validate_mobile_number(self, key, value):
        if len(value) != 10:
            raise ValueError('Invalid mobile number length')
        return value



class PlatformRegistrationData(Base):
        __tablename__ = "platform_registration_data"

        id = Column(Integer, primary_key=True, index=True)
        first_name = Column(String, nullable=False)
        last_name = Column(String, nullable=False)
        email = Column(String, nullable=False)
        password = Column(String, nullable=False)
        company_name = Column(String, nullable=True)

        # Relationship back to UserTable
        user = relationship("UserTable", back_populates="platform_registration_data")
        __table_args__ = (
            UniqueConstraint('email', name='uix_email_type'),
        )
        @validates('email')
        def validate_email(self, key, value):
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
                raise ValueError('Invalid email format')
            return value


class BasicSignupData(Base):
    __tablename__ = "basic_signup_data"

    id = Column(Integer, primary_key=True, index=True)
    mobile_number = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    dob = Column(Date, nullable=True)

    # Relationship back to UserTable
    user = relationship("UserTable", back_populates="basic_signup_data")
    __table_args__ = (
        UniqueConstraint('mobile_number', name='uix_basic_mobile_number_type'),
    )

    @validates('mobile_number')
    def validate_mobile_number(self, key, value):
        if len(value) != 10:
            raise ValueError('Invalid mobile number length')
        return value
