from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    password = fields.CharField(max_length=128, description="加密密码")
    nickname = fields.CharField(max_length=50, null=True, description="昵称")
    email = fields.CharField(max_length=100, null=True, description="邮箱")
    user_pic = fields.CharField(max_length=255, null=True, description="头像 URL")

    class Meta:
        table = "users"  # 表名为 users 这个代码的作用是在执行generate_schemas=True自动建表， 会创建名为users的表
