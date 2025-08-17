"""Tests for Protocol-based interfaces."""

from __future__ import annotations

import pytest
from typing import List, Optional

from src.backend.domain.interfaces import UserRepository, AuthService, OAuthService
from src.backend.models.user import User
from src.backend.auth.models import JWTPayload, TokenResponse, OAuthToken, GoogleUserInfo


class MockUserRepository:
    """Mock implementation of UserRepository Protocol."""
    
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    async def create_user(self, user: User) -> User:
        user.id = str(self.next_id)
        self.users[user.id] = user
        self.next_id += 1
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        for user in self.users.values():
            if user.google_id == google_id:
                return user
        return None
    
    async def update_user(self, user_id: str, updates: dict) -> Optional[User]:
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        for key, value in updates.items():
            setattr(user, key, value)
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
    
    async def add_scan_to_user(self, user_id: str, scan_id: str) -> bool:
        if user_id not in self.users:
            return False
        
        user = self.users[user_id]
        if scan_id not in user.scan_ids:
            user.scan_ids.append(scan_id)
        return True
    
    async def update_user_points(self, user_id: str, points: int) -> Optional[User]:
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        user.points += points
        return user
    
    async def get_users_by_points_range(self, min_points: int, max_points: int) -> List[User]:
        return [
            user for user in self.users.values()
            if min_points <= user.points <= max_points
        ]


class MockAuthService:
    """Mock implementation of AuthService Protocol."""
    
    def create_access_token(self, user_id: str, email: str) -> str:
        return f"access_token_{user_id}_{email}"
    
    def create_refresh_token(self, user_id: str, email: str) -> str:
        return f"refresh_token_{user_id}_{email}"
    
    def create_token_pair(self, user_id: str, email: str) -> TokenResponse:
        return TokenResponse(
            access_token=self.create_access_token(user_id, email),
            refresh_token=self.create_refresh_token(user_id, email),
            expires_in=3600,
            user_id=user_id,
            email=email
        )
    
    def verify_token(self, token: str, token_type: str = "access") -> JWTPayload:
        return JWTPayload(
            sub="user123",
            email="test@example.com",
            exp=9999999999,
            iat=1234567890,
            token_type=token_type
        )
    
    def refresh_access_token(self, refresh_token: str) -> str:
        return f"new_access_token_{refresh_token}"
    
    def extract_user_from_token(self, token: str) -> Optional[str]:
        return "user123" if token else None
    
    def is_token_expired(self, token: str) -> bool:
        return False


class MockOAuthService:
    """Mock implementation of OAuthService Protocol."""
    
    def generate_authorization_url(self) -> tuple[str, str]:
        return "https://oauth.example.com/auth", "state123"
    
    async def exchange_code_for_tokens(self, code: str, state: str) -> OAuthToken:
        return OAuthToken(
            access_token=f"access_{code}",
            refresh_token=f"refresh_{code}",
            expires_in=3600,
            scope="openid email profile"
        )
    
    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        return GoogleUserInfo(
            sub="google123",
            email="test@example.com",
            email_verified=True,
            name="Test User"
        )
    
    def validate_state_parameter(self, received_state: str, expected_state: str) -> bool:
        return received_state == expected_state


class TestProtocolInterfaces:
    """Test cases for Protocol-based interfaces."""
    
    def test_user_repository_protocol_compliance(self):
        """Test that MockUserRepository complies with UserRepository Protocol."""
        # This should not raise any type errors if the Protocol is correctly implemented
        repository: UserRepository = MockUserRepository()
        assert repository is not None
    
    def test_auth_service_protocol_compliance(self):
        """Test that MockAuthService complies with AuthService Protocol."""
        # This should not raise any type errors if the Protocol is correctly implemented
        auth_service: AuthService = MockAuthService()
        assert auth_service is not None
    
    def test_oauth_service_protocol_compliance(self):
        """Test that MockOAuthService complies with OAuthService Protocol."""
        # This should not raise any type errors if the Protocol is correctly implemented
        oauth_service: OAuthService = MockOAuthService()
        assert oauth_service is not None
    
    def test_protocol_method_signatures(self):
        """Test that Protocol methods have the correct signatures."""
        # Test UserRepository Protocol
        repository: UserRepository = MockUserRepository()
        
        # These should not raise type errors
        assert hasattr(repository, 'create_user')
        assert hasattr(repository, 'get_user_by_id')
        assert hasattr(repository, 'get_user_by_email')
        assert hasattr(repository, 'get_user_by_google_id')
        assert hasattr(repository, 'update_user')
        assert hasattr(repository, 'delete_user')
        assert hasattr(repository, 'add_scan_to_user')
        assert hasattr(repository, 'update_user_points')
        assert hasattr(repository, 'get_users_by_points_range')
        
        # Test AuthService Protocol
        auth_service: AuthService = MockAuthService()
        
        assert hasattr(auth_service, 'create_access_token')
        assert hasattr(auth_service, 'create_refresh_token')
        assert hasattr(auth_service, 'create_token_pair')
        assert hasattr(auth_service, 'verify_token')
        assert hasattr(auth_service, 'refresh_access_token')
        assert hasattr(auth_service, 'extract_user_from_token')
        assert hasattr(auth_service, 'is_token_expired')
        
        # Test OAuthService Protocol
        oauth_service: OAuthService = MockOAuthService()
        
        assert hasattr(oauth_service, 'generate_authorization_url')
        assert hasattr(oauth_service, 'exchange_code_for_tokens')
        assert hasattr(oauth_service, 'get_user_info')
        assert hasattr(oauth_service, 'validate_state_parameter')
    
    def test_protocol_usage_in_service_factory(self):
        """Test that Protocol interfaces can be used in service factory."""
        from src.backend.services.service_factory import ServiceFactory
        
        factory = ServiceFactory()
        
        # These should work without type errors
        user_repo: UserRepository = factory.user_repository
        auth_service: AuthService = factory.auth_service
        oauth_service: OAuthService = factory.oauth_service
        
        assert user_repo is not None
        assert auth_service is not None
        assert oauth_service is not None
