from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegister


class AuthService:
    def __init__(self):
        self.user_repository = UserRepository()

    async def register_user(self, user_data: UserRegister):
        """
        Register a new user.
        """

        # 1. Check whether email already exists
        existing_user = await self.user_repository.find_by_email(
            user_data.email
        )

        if existing_user:
            raise ValueError(
                "User with this email already exists"
            )

        # 2. Hash the password
        hashed_password = hash_password(
            user_data.password
        )

        # 3. Create MongoDB document
        user_document = {
            "name": user_data.name,
            "email": user_data.email,
            "password_hash": hashed_password,
            "role": "user",
            "is_active": True,
        }

        # 4. Save user
        created_user = await self.user_repository.create_user(
            user_document
        )

        # 5. Convert MongoDB document to API response
        return {
            "id": str(created_user["_id"]),
            "name": created_user["name"],
            "email": created_user["email"],
            "role": created_user["role"],
            "is_active": created_user["is_active"],
        }

    async def login_user(
        self,
        email: str,
        password: str,
    ) -> str:
        """
        Authenticate user and return JWT access token.
        """

        # 1. Find user
        user = await self.user_repository.find_by_email(
            email
        )

        if not user:
            raise ValueError(
                "Invalid email or password"
            )

        # 2. Check account status
        if not user.get("is_active", False):
            raise ValueError(
                "User account is inactive"
            )

        # 3. Verify password
        password_valid = verify_password(
            password,
            user["password_hash"]
        )

        if not password_valid:
            raise ValueError(
                "Invalid email or password"
            )

        # 4. Create JWT payload
        token_data = {
            "sub": str(user["_id"]),
            "email": user["email"],
            "role": user.get("role", "user"),
        }

        # 5. Generate JWT
        access_token = create_access_token(
            token_data
        )

        return access_token