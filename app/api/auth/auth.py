"""
Authentication API endpoints for POORNASREE AI Platform
"""
# pylint: disable=import-error
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.core.database import get_db
from app.core.security import (
    security_manager, 
    otp_manager, 
    email_service, 
    check_admin_access,
    get_user_role
)
from app.core.config import settings, UserRole
from app.models.user import User, UserSession, UserRoleEnum, UserStatusEnum
from app.api.auth.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    OTPVerificationRequest,
    EngineerRegistrationRequest,
    EngineerRegistrationResponse,
    UserLoginRequest,
    UserLoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    LogoutRequest,
    UserProfileResponse
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    token = credentials.credentials
    payload = security_manager.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure current user is an admin
    """
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_engineer_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure current user is an engineer or admin
    """
    if current_user.role not in [UserRoleEnum.ENGINEER, UserRoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer or admin access required"
        )
    return current_user


@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(
    request: AdminLoginRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Admin login endpoint - Step 1: Verify email and send OTP
    """
    try:
        # Verify admin email
        if not check_admin_access(request.email):
            logger.warning(f"Unauthorized admin login attempt: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized admin access"
            )
        
        # Generate and send OTP
        otp = otp_manager.generate_otp(request.email)
        
        # Send OTP via email
        email_sent = email_service.send_otp_email(request.email, otp)
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email"
            )
        
        # Find or create admin user
        admin_user = db.query(User).filter(User.email == request.email).first()
        if not admin_user:
            admin_user = User(
                email=request.email,
                full_name="System Administrator",
                role=UserRoleEnum.ADMIN,
                status=UserStatusEnum.ACTIVE,
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
        
        logger.info(f"OTP sent to admin: {request.email}")
        
        return AdminLoginResponse(
            message="OTP sent to your email address",
            email=request.email,
            expires_in_minutes=settings.admin_otp_expire_minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/admin/verify-otp", response_model=UserLoginResponse)
async def verify_admin_otp(
    request: OTPVerificationRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Admin login endpoint - Step 2: Verify OTP and return tokens
    """
    try:
        # Verify OTP
        if not otp_manager.verify_otp(request.email, request.otp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP"
            )
        
        # Get admin user
        admin_user = db.query(User).filter(User.email == request.email).first()
        if not admin_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin user not found"
            )
        
        # Update last login
        admin_user.last_login_at = datetime.utcnow()
        db.commit()
        
        # Create tokens
        token_data = {"sub": admin_user.email, "role": admin_user.role.value}
        access_token = security_manager.create_access_token(token_data)
        refresh_token = security_manager.create_refresh_token(token_data)
        
        # Create session
        session = UserSession(
            user_id=admin_user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent"),
            expires_at=datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        )
        db.add(session)
        db.commit()
        
        logger.info(f"Admin login successful: {request.email}")
        
        return UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserProfileResponse.from_user(admin_user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin OTP verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/engineer/register", response_model=EngineerRegistrationResponse)
async def register_engineer(
    request: EngineerRegistrationRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Engineer registration endpoint
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists with this email"
            )
        
        # Hash password if provided
        hashed_password = None
        if request.password:
            hashed_password = security_manager.get_password_hash(request.password)
        
        # Create engineer user with pending status
        engineer = User(
            email=request.email,
            full_name=request.full_name,
            phone_number=request.phone_number,
            role=UserRoleEnum.ENGINEER,
            status=UserStatusEnum.PENDING,
            hashed_password=hashed_password,
            is_active=False,  # Inactive until approved
            is_verified=False,
            company_name=request.company_name,
            job_title=request.job_title,
            department=request.department,
            experience_years=request.experience_years,
            certifications=request.certifications,
            expertise_areas=request.expertise_areas,
            employee_id=request.employee_id,
            manager_email=request.manager_email,
            registration_data={
                "ip_address": req.client.host if req.client else None,
                "user_agent": req.headers.get("user-agent"),
                "registration_source": "web",
                "additional_info": request.additional_info
            }
        )
        
        db.add(engineer)
        db.commit()
        db.refresh(engineer)
        
        logger.info(f"Engineer registration submitted: {request.email}")
        
        return EngineerRegistrationResponse(
            message="Registration submitted successfully. Your account is pending approval.",
            user_id=engineer.id,
            email=engineer.email,
            status="pending"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Engineer registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/login", response_model=UserLoginResponse)
async def user_login(
    request: UserLoginRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    General user login endpoint (for customers and approved engineers)
    """
    try:
        # Find user
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password (if user has one)
        if user.hashed_password:
            if not request.password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Password required"
                )
            
            if not security_manager.verify_password(request.password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
        
        # Check user status
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        if user.role == UserRoleEnum.ENGINEER and user.status != UserStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Engineer account is not approved yet"
            )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        # Create tokens
        token_data = {"sub": user.email, "role": user.role.value}
        access_token = security_manager.create_access_token(token_data)
        refresh_token = security_manager.create_refresh_token(token_data)
        
        # Create session
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent"),
            expires_at=datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        )
        db.add(session)
        db.commit()
        
        logger.info(f"User login successful: {request.email}")
        
        return UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserProfileResponse.from_user(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    try:
        # Verify refresh token
        payload = security_manager.verify_token(request.refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Find session with refresh token
        session = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.refresh_token == request.refresh_token,
            UserSession.is_active == True
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )
        
        # Create new access token
        token_data = {"sub": user.email, "role": user.role.value}
        new_access_token = security_manager.create_access_token(token_data)
        
        # Update session
        session.session_token = new_access_token
        session.expires_at = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        session.last_activity_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Token refreshed for user: {email}")
        
        return TokenRefreshResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user and invalidate session
    """
    try:
        # Find and deactivate session
        session = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.session_token == request.access_token,
            UserSession.is_active == True
        ).first()
        
        if session:
            session.is_active = False
            session.logged_out_at = datetime.utcnow()
            db.commit()
        
        logger.info(f"User logged out: {current_user.email}")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile
    """
    return UserProfileResponse.from_user(current_user)


@router.get("/validate-token")
async def validate_token(
    current_user: User = Depends(get_current_user)
):
    """
    Validate JWT token
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value
    }
