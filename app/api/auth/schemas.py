"""
Pydantic schemas for authentication API endpoints
"""
# pylint: disable=no-self-argument,no-member,import-error,no-name-in-module
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import enum

from app.models.user import User, UserRoleEnum, UserStatusEnum, LanguageEnum


class AdminLoginRequest(BaseModel):
    """Admin login request schema"""
    email: EmailStr = Field(..., description="Admin email address")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "info.pydart@gmail.com"
            }
        }


class AdminLoginResponse(BaseModel):
    """Admin login response schema"""
    message: str = Field(..., description="Response message")
    email: str = Field(..., description="Email address")
    expires_in_minutes: int = Field(..., description="OTP expiration time in minutes")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "OTP sent to your email address",
                "email": "info.pydart@gmail.com",
                "expires_in_minutes": 5
            }
        }


class OTPVerificationRequest(BaseModel):
    """OTP verification request schema"""
    email: EmailStr = Field(..., description="Email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")
    
    @validator('otp')
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "info.pydart@gmail.com",
                "otp": "123456"
            }
        }


class EngineerRegistrationRequest(BaseModel):
    """Engineer registration request schema"""
    # Basic information
    email: EmailStr = Field(..., description="Email address")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    password: Optional[str] = Field(None, min_length=8, description="Password (optional)")
    
    # Professional information
    company_name: str = Field(..., min_length=2, max_length=255, description="Company name")
    job_title: str = Field(..., min_length=2, max_length=255, description="Job title")
    department: Optional[str] = Field(None, max_length=255, description="Department")
    experience_years: int = Field(..., ge=0, le=50, description="Years of experience")
    
    # Skills and certifications
    certifications: Optional[List[str]] = Field(None, description="Professional certifications")
    expertise_areas: Optional[List[str]] = Field(None, description="Areas of expertise")
    
    # Company details
    employee_id: Optional[str] = Field(None, max_length=100, description="Employee ID")
    manager_email: Optional[EmailStr] = Field(None, description="Manager's email")
    
    # Additional information
    additional_info: Optional[str] = Field(None, max_length=1000, description="Additional information")
    
    @validator('certifications', 'expertise_areas')
    def validate_lists(cls, v):
        if v is not None and len(v) > 10:
            raise ValueError('Maximum 10 items allowed')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "engineer@company.com",
                "full_name": "John Engineer",
                "phone_number": "+1234567890",
                "password": "securepassword123",
                "company_name": "Tech Solutions Inc",
                "job_title": "Senior Maintenance Engineer",
                "department": "Operations",
                "experience_years": 5,
                "certifications": ["Certified Maintenance Professional", "Six Sigma Green Belt"],
                "expertise_areas": ["Industrial Machinery", "Preventive Maintenance", "Troubleshooting"],
                "employee_id": "EMP001",
                "manager_email": "manager@company.com",
                "additional_info": "Specialized in heavy machinery maintenance"
            }
        }


class EngineerRegistrationResponse(BaseModel):
    """Engineer registration response schema"""
    message: str = Field(..., description="Response message")
    user_id: int = Field(..., description="Generated user ID")
    email: str = Field(..., description="Email address")
    status: str = Field(..., description="Registration status")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Registration submitted successfully. Your account is pending approval.",
                "user_id": 123,
                "email": "engineer@company.com",
                "status": "pending"
            }
        }


class UserLoginRequest(BaseModel):
    """User login request schema"""
    email: EmailStr = Field(..., description="Email address")
    password: Optional[str] = Field(None, description="Password (required for password-based auth)")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class UserProfileResponse(BaseModel):
    """User profile response schema"""
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    phone_number: Optional[str] = Field(None, description="Phone number")
    role: str = Field(..., description="User role")
    status: str = Field(..., description="User status")
    is_active: bool = Field(..., description="Is user active")
    is_verified: bool = Field(..., description="Is user verified")
    preferred_language: str = Field(..., description="Preferred language")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    bio: Optional[str] = Field(None, description="Bio")
    
    # Professional fields (for engineers)
    company_name: Optional[str] = Field(None, description="Company name")
    job_title: Optional[str] = Field(None, description="Job title")
    department: Optional[str] = Field(None, description="Department")
    experience_years: Optional[int] = Field(None, description="Years of experience")
    certifications: Optional[List[str]] = Field(None, description="Certifications")
    expertise_areas: Optional[List[str]] = Field(None, description="Expertise areas")
    
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Account creation date")
    last_login_at: Optional[datetime] = Field(None, description="Last login date")
    
    @classmethod
    def from_user(cls, user: User) -> "UserProfileResponse":
        """Create UserProfileResponse from User model"""
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone_number=user.phone_number,
            role=user.role.value if user.role else "customer",
            status=user.status.value if user.status else "active",
            is_active=user.is_active,
            is_verified=user.is_verified,
            preferred_language=user.preferred_language.value if user.preferred_language else "en",
            avatar_url=user.avatar_url,
            bio=user.bio,
            company_name=user.company_name,
            job_title=user.job_title,
            department=user.department,
            experience_years=user.experience_years,
            certifications=user.certifications,
            expertise_areas=user.expertise_areas,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
    
    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "email": "user@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "role": "engineer",
                "status": "approved",
                "is_active": True,
                "is_verified": True,
                "preferred_language": "en",
                "avatar_url": "https://example.com/avatar.jpg",
                "bio": "Experienced maintenance engineer",
                "company_name": "Tech Solutions Inc",
                "job_title": "Senior Engineer",
                "department": "Operations",
                "experience_years": 5,
                "certifications": ["CMP", "Six Sigma"],
                "expertise_areas": ["Industrial Machinery"],
                "created_at": "2024-01-01T00:00:00Z",
                "last_login_at": "2024-01-15T10:30:00Z"
            }
        }


class UserLoginResponse(BaseModel):
    """User login response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserProfileResponse = Field(..., description="User profile information")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": 123,
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "role": "engineer"
                }
            }
        }


class TokenRefreshRequest(BaseModel):
    """Token refresh request schema"""
    refresh_token: str = Field(..., description="JWT refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class TokenRefreshResponse(BaseModel):
    """Token refresh response schema"""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class LogoutRequest(BaseModel):
    """Logout request schema"""
    access_token: str = Field(..., description="JWT access token to invalidate")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class PasswordChangeRequest(BaseModel):
    """Password change request schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newpassword456",
                "confirm_password": "newpassword456"
            }
        }


class ProfileUpdateRequest(BaseModel):
    """Profile update request schema"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=1000)
    preferred_language: Optional[str] = Field(None, pattern="^(en|hi)$")
    
    # Professional fields (for engineers)
    job_title: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=255)
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    certifications: Optional[List[str]] = Field(None)
    expertise_areas: Optional[List[str]] = Field(None)
    
    @validator('certifications', 'expertise_areas')
    def validate_lists(cls, v):
        if v is not None and len(v) > 10:
            raise ValueError('Maximum 10 items allowed')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "John Doe Updated",
                "phone_number": "+9876543210",
                "bio": "Updated bio information",
                "preferred_language": "hi",
                "job_title": "Lead Engineer",
                "department": "Advanced Operations",
                "experience_years": 7,
                "certifications": ["Advanced CMP", "Six Sigma Black Belt"],
                "expertise_areas": ["Predictive Maintenance", "IoT Systems"]
            }
        }


class EngineerApprovalRequest(BaseModel):
    """Engineer approval request schema (Admin only)"""
    user_id: int = Field(..., description="Engineer user ID")
    action: str = Field(..., pattern="^(approve|reject)$", description="Approval action")
    notes: Optional[str] = Field(None, max_length=1000, description="Approval notes")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "action": "approve",
                "notes": "Credentials verified and approved"
            }
        }


class EngineerApprovalResponse(BaseModel):
    """Engineer approval response schema"""
    message: str = Field(..., description="Response message")
    user_id: int = Field(..., description="Engineer user ID")
    action: str = Field(..., description="Action taken")
    email_sent: bool = Field(..., description="Whether notification email was sent")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Engineer approved successfully",
                "user_id": 123,
                "action": "approve",
                "email_sent": True
            }
        }
