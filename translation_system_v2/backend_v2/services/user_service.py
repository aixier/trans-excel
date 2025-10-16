"""用户服务 - 管理用户认证"""
import json
import bcrypt
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserService:
    """用户服务类"""

    def __init__(self):
        """初始化用户服务"""
        # 用户数据文件路径
        self.users_file = Path(__file__).parent.parent / 'data' / 'users.json'
        logger.info(f"User service initialized with file: {self.users_file}")

    def _load_users(self) -> Dict:
        """加载用户数据"""
        try:
            if not self.users_file.exists():
                logger.error(f"Users file not found: {self.users_file}")
                return {"users": []}

            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Loaded {len(data.get('users', []))} users")
                return data
        except Exception as e:
            logger.error(f"Failed to load users: {e}")
            return {"users": []}

    def _save_users(self, data: Dict) -> bool:
        """保存用户数据"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug("Users data saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
            return False

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        验证用户登录

        Args:
            username: 用户名
            password: 密码（明文）

        Returns:
            用户信息（不含密码）或None
        """
        try:
            data = self._load_users()

            # 查找用户
            user = next(
                (u for u in data['users']
                 if u['username'] == username and u['status'] == 'active'),
                None
            )

            if not user:
                logger.warning(f"User not found or inactive: {username}")
                return None

            # 验证密码
            password_bytes = password.encode('utf-8')
            hashed_bytes = user['password'].encode('utf-8')

            if not bcrypt.checkpw(password_bytes, hashed_bytes):
                logger.warning(f"Invalid password for user: {username}")
                return None

            # 更新最后登录时间
            user['lastLogin'] = datetime.now().isoformat()
            self._save_users(data)

            # 返回用户信息（排除密码）
            user_info = {k: v for k, v in user.items() if k != 'password'}
            logger.info(f"User authenticated successfully: {username}")
            return user_info

        except Exception as e:
            logger.error(f"Authentication error for {username}: {e}")
            return None

    def find_user_by_token(self, token: str) -> Optional[Dict]:
        """
        根据token查找用户

        Args:
            token: 用户token

        Returns:
            用户信息（不含密码）或None
        """
        try:
            data = self._load_users()

            user = next(
                (u for u in data['users']
                 if u['token'] == token and u['status'] == 'active'),
                None
            )

            if user:
                user_info = {k: v for k, v in user.items() if k != 'password'}
                return user_info

            return None

        except Exception as e:
            logger.error(f"Error finding user by token: {e}")
            return None

    def find_user_by_username(self, username: str) -> Optional[Dict]:
        """
        根据用户名查找用户

        Args:
            username: 用户名

        Returns:
            用户信息（不含密码）或None
        """
        try:
            data = self._load_users()

            user = next(
                (u for u in data['users'] if u['username'] == username),
                None
            )

            if user:
                user_info = {k: v for k, v in user.items() if k != 'password'}
                return user_info

            return None

        except Exception as e:
            logger.error(f"Error finding user by username: {e}")
            return None

    def get_all_users(self) -> list:
        """
        获取所有用户列表（用于管理）

        Returns:
            用户列表（不含密码）
        """
        try:
            data = self._load_users()
            return [
                {k: v for k, v in user.items() if k != 'password'}
                for user in data['users']
            ]
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []


# 单例
user_service = UserService()
