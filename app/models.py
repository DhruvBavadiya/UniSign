from sqlalchemy import Column, Integer, String, Enum, Date,UniqueConstraint
from app.database import Base
import enum

# Define an enum for registration types
class RegistrationType(enum.Enum):
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    PROJECT_MANAGEMENT = "project_management"
    COMMON_SIGNUP = "common_signup"

class Registration(Base):
    __tablename__ = "user_registration"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(RegistrationType), nullable=False)
    
    # Common fields across all form types
    mobile_number = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    password = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    hashtag = Column(String, nullable=True)
    miscellaneous = Column(String, nullable=True)

    # Unique constraints
    __table_args__ = (
        UniqueConstraint('mobile_number', 'type', name='uix_mobile_number_type'),
        UniqueConstraint('email', 'type', name='uix_email_type'),
        {"sqlite_autoincrement": True},
    )

    def __repr__(self):
        return f"<Registration(type={self.type}, first_name={self.first_name}, last_name={self.last_name})>"
