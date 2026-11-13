from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class AdminSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    signup_key: str = Field(min_length=1, max_length=256)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool