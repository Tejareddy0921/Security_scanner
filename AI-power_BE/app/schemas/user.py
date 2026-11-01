from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: str
    updated_at: str


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def require_an_update(self) -> "UserUpdateRequest":
        if not self.model_fields_set or all(getattr(self, name) is None for name in self.model_fields_set):
            raise ValueError("At least one non-empty field must be provided")
        return self
