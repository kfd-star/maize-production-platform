from passlib.context import CryptContext

# 创建密码加密上下文，使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 加密密码函数
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# 校验密码函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
