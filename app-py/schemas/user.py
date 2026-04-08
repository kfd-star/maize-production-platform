from pydantic import BaseModel, EmailStr
from typing import Optional


# UserCreate（用于注册接口）
class UserCreate(BaseModel):
    username: str
    password: str
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    user_pic: Optional[str] = None


# 登录时请求的字段
class UserLogin(BaseModel):
    username: str
    password: str


# 返回给前端的用户信息（不包含密码）
class UserOut(BaseModel):
    id: int
    username: str
    nickname: Optional[str]
    email: Optional[EmailStr]
    user_pic: Optional[str]

    class Config:
        from_attributes = True  # 允许从 ORM 模型转换为 Pydantic 模型


#  登录时返回给前端的用户信息
class LoginResponse(BaseModel):
    msg: str
    id: int
    username: str
    nickname: Optional[str]
    email: Optional[str]
    user_pic: Optional[str]
    token: str
    token_type: str

    class Config:
        from_attributes = True
