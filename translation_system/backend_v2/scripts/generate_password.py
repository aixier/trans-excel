"""生成bcrypt密码hash的脚本"""
import bcrypt

# 演示账号密码
passwords = {
    "admin": "admin123",
    "demo": "demo123"
}

print("=== 生成密码Hash ===\n")

for username, password in passwords.items():
    # 生成salt和hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

    print(f"用户名: {username}")
    print(f"明文密码: {password}")
    print(f"Hash: {hashed.decode('utf-8')}")
    print(f"验证: {bcrypt.checkpw(password.encode('utf-8'), hashed)}")
    print("-" * 60)
