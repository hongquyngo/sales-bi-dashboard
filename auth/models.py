"""
User model and authentication data structures
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User roles matching database values"""
    ADMIN = "admin"
    MANAGER = "manager"
    SALES = "sales"
    SUPPLY_CHAIN = "supply_chain"
    VIEWER = "viewer"


@dataclass
class User:
    """User model matching database schema"""
    id: int
    username: str
    email: str
    role: str
    employee_id: Optional[int] = None
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_date: Optional[datetime] = None
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN.value
    
    @property
    def is_manager(self) -> bool:
        """Check if user has manager role"""
        return self.role == UserRole.MANAGER.value
    
    @property
    def can_view_all_data(self) -> bool:
        """Check if user can view all data"""
        return self.role in [UserRole.ADMIN.value, UserRole.MANAGER.value]
    
    @property
    def can_export_data(self) -> bool:
        """Check if user can export data"""
        return self.role != UserRole.VIEWER.value
    
    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return self.role == role
    
    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles"""
        return self.role in roles
    
    def to_dict(self) -> dict:
        """Convert user to dictionary for session storage"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "employee_id": self.employee_id,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login and isinstance(self.last_login, datetime) else None,
            "created_date": self.created_date.isoformat() if self.created_date and isinstance(self.created_date, datetime) else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create user from dictionary"""
        # Handle last_login conversion
        if data.get("last_login"):
            if isinstance(data["last_login"], str):
                try:
                    data["last_login"] = datetime.fromisoformat(data["last_login"])
                except (ValueError, TypeError):
                    data["last_login"] = None
            elif not isinstance(data["last_login"], datetime):
                data["last_login"] = None
        
        # Remove any extra keys that aren't in the User class
        valid_fields = {'id', 'username', 'email', 'role', 'employee_id', 
                       'is_active', 'last_login', 'created_date'}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)


@dataclass 
class LoginAttempt:
    """Track login attempts for security"""
    username: str
    timestamp: datetime
    success: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None