from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if value.isdigit() or value.isalpha():
            raise ValueError("Password must contain both letters and numbers.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
