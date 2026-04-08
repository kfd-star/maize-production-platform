from fastapi import APIRouter, HTTPException
from models.user import User
from schemas.user import UserCreate, UserLogin, UserOut, LoginResponse
from utils.auth import hash_password, verify_password
from utils.token import create_access_token

user_api = APIRouter()


@user_api.post("/register", response_model=UserOut)
async def register(user: UserCreate):
    existing = await User.get_or_none(
        username=user.username
    )  # 用于异步查询数据库中是否已存在相同用户名的用户。
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    new_user = await User.create(
        username=user.username,
        password=hash_password(user.password),
        nickname=user.nickname,
        email=user.email,
        user_pic=user.user_pic,
    )
    return new_user


@user_api.post("/login", response_model=LoginResponse)
async def login(user: UserLogin):
    db_user = await User.get_or_none(username=user.username)
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(data={"sub": db_user.username})
    return {
        "msg": "登录成功",
        "id": db_user.id,
        "username": db_user.username,
        "nickname": db_user.nickname,
        "email": db_user.email,
        "user_pic": db_user.user_pic,
        "token": token,
        "token_type": "bearer",
    }
