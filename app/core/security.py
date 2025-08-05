"""
Security utilities for POORNASREE AI Platform
Handles authentication, authorization, and security operations
"""
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import secrets
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from app.core.config import settings, UserRole

# Configure logging
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """Handles all security-related operations"""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against its hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash a password
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            raise
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        
        Args:
            data: Token payload data
            expires_delta: Token expiration time delta
            
        Returns:
            str: JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token
        
        Args:
            data: Token payload data
            
        Returns:
            str: JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Refresh token creation error: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Dict[str, Any]: Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def generate_otp(self, length: int = 6) -> str:
        """
        Generate numeric OTP
        
        Args:
            length: OTP length
            
        Returns:
            str: Generated OTP
        """
        return ''.join(random.choices(string.digits, k=length))
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate cryptographically secure token
        
        Args:
            length: Token length
            
        Returns:
            str: Generated token
        """
        return secrets.token_urlsafe(length)


class OTPManager:
    """Handles OTP generation, storage, and verification"""
    
    def __init__(self):
        self.otp_storage = {}  # In production, use Redis or database
        self.otp_expire_minutes = settings.admin_otp_expire_minutes
    
    def generate_otp(self, identifier: str) -> str:
        """
        Generate and store OTP for identifier
        
        Args:
            identifier: User identifier (email, phone, etc.)
            
        Returns:
            str: Generated OTP
        """
        otp = SecurityManager().generate_otp()
        expire_time = datetime.utcnow() + timedelta(minutes=self.otp_expire_minutes)
        
        self.otp_storage[identifier] = {
            "otp": otp,
            "expires_at": expire_time,
            "attempts": 0
        }
        
        logger.info(f"OTP generated for {identifier}")
        return otp
    
    def verify_otp(self, identifier: str, otp: str) -> bool:
        """
        Verify OTP for identifier
        
        Args:
            identifier: User identifier
            otp: OTP to verify
            
        Returns:
            bool: True if OTP is valid, False otherwise
        """
        stored_otp_data = self.otp_storage.get(identifier)
        
        if not stored_otp_data:
            logger.warning(f"No OTP found for {identifier}")
            return False
        
        # Check if OTP has expired
        if datetime.utcnow() > stored_otp_data["expires_at"]:
            logger.warning(f"OTP expired for {identifier}")
            del self.otp_storage[identifier]
            return False
        
        # Check attempt limit
        if stored_otp_data["attempts"] >= 3:
            logger.warning(f"Too many OTP attempts for {identifier}")
            del self.otp_storage[identifier]
            return False
        
        # Verify OTP
        if stored_otp_data["otp"] == otp:
            logger.info(f"OTP verified successfully for {identifier}")
            del self.otp_storage[identifier]
            return True
        else:
            stored_otp_data["attempts"] += 1
            logger.warning(f"Invalid OTP attempt for {identifier}")
            return False
    
    def cleanup_expired_otps(self):
        """Remove expired OTPs from storage"""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, data in self.otp_storage.items()
            if current_time > data["expires_at"]
        ]
        
        for key in expired_keys:
            del self.otp_storage[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired OTPs")


class EmailService:
    """Handles email sending for OTP and notifications"""
    
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.smtp_use_tls = settings.smtp_use_tls
    
    def send_otp_email(self, recipient_email: str, otp: str) -> bool:
        """
        Send OTP via email
        
        Args:
            recipient_email: Recipient's email address
            otp: OTP to send
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = recipient_email
            msg['Subject'] = f"{settings.platform_name} - Your OTP Code"
            
            # Email body
            body = f"""
            <html>
            <body>
                <h2>{settings.platform_name}</h2>
                <p>Your One-Time Password (OTP) is: <strong>{otp}</strong></p>
                <p>This OTP will expire in {settings.admin_otp_expire_minutes} minutes.</p>
                <p>If you didn't request this OTP, please ignore this email.</p>
                <br>
                <p>Best regards,<br>{settings.platform_name} Team</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"OTP email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP email to {recipient_email}: {e}")
            return False
    
    def send_engineer_approval_email(self, recipient_email: str, engineer_name: str, status: str) -> bool:
        """
        Send engineer approval status email
        
        Args:
            recipient_email: Engineer's email
            engineer_name: Engineer's name
            status: Approval status (approved/rejected)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = recipient_email
            msg['Subject'] = f"{settings.platform_name} - Registration {status.title()}"
            
            # Email body based on status
            if status.lower() == "approved":
                body = f"""
                <html>
                <body>
                    <h2>{settings.platform_name}</h2>
                    <p>Dear {engineer_name},</p>
                    <p>Congratulations! Your engineer registration has been <strong>approved</strong>.</p>
                    <p>You can now access the {settings.platform_name} platform with your registered credentials.</p>
                    <p>Please log in to complete your profile and start using the platform.</p>
                    <br>
                    <p>Best regards,<br>{settings.platform_name} Team</p>
                </body>
                </html>
                """
            else:
                body = f"""
                <html>
                <body>
                    <h2>{settings.platform_name}</h2>
                    <p>Dear {engineer_name},</p>
                    <p>We regret to inform you that your engineer registration has been <strong>rejected</strong>.</p>
                    <p>Please contact our support team for more information or to resubmit your application.</p>
                    <br>
                    <p>Best regards,<br>{settings.platform_name} Team</p>
                </body>
                </html>
                """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Approval email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send approval email to {recipient_email}: {e}")
            return False


# Global instances
security_manager = SecurityManager()
otp_manager = OTPManager()
email_service = EmailService()


def check_admin_access(email: str) -> bool:
    """
    Check if email has admin access
    
    Args:
        email: Email to check
        
    Returns:
        bool: True if admin email, False otherwise
    """
    admin_email: str = str(settings.admin_email)  # Type hint for Pylint
    return email.lower() == admin_email.lower()


def get_user_role(email: str, is_engineer_approved: bool = False) -> str:
    """
    Determine user role based on email and approval status
    
    Args:
        email: User email
        is_engineer_approved: Whether engineer is approved
        
    Returns:
        str: User role (admin, engineer, customer)
    """
    if check_admin_access(email):
        return UserRole.ADMIN
    elif is_engineer_approved:
        return UserRole.ENGINEER
    else:
        return UserRole.CUSTOMER
