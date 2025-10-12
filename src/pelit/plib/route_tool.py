import os
import secrets
import hashlib
from typing import Optional, Any
from pathlib import Path
from flask import request

__all__ = ['authenticate', 'generate_file_name', 'enough_space',
           'join_url', 'list_dir', 'is_attempting_traversal']

def authenticate(cfg: dict[str, Any]) -> bool:
    """
    [INTERNAL] 检查 Authorization 头中的密钥

    Returns:
        一个 bool 值，代表授权是否成功
    """
    token: Optional[str] = request.headers.get("Authorization")
    if not token:
        return False
    
    # 兼容 Bearer 格式
    if token.startswith("Bearer"):
        token = token[7:]
    
    # 验证密钥，可用 PELIT_AUTH 环境变量或配置文件
    if 'hashed' in cfg['auth'] and not 'from_env' in cfg['auth']:
        token_set: str = cfg['auth']['hashed']
        return token_set.upper() == \
            hashlib.sha256(token.encode('utf-8')).hexdigest().upper()
    elif 'PELIT_AUTH' in os.environ and 'from_env' in cfg['auth']:
        token_set: str = os.environ['PELIT_AUTH']
        return token_set.upper() == token.upper()
    else:
        return False

def generate_file_name(directory: Path, extension: str) -> str:
    """
    [INTERNAL] 随机生成一个有效的文件（路径）名

    Args:
        directory: 保存目录的 Path 对象
        extension: 保存的拓展名，可以是空字符串
    
    Returns:
        有效的 str 类型文件名，无后缀
    """
    while True:
        filename = secrets.token_hex(10)
        full_path = directory / (filename + extension)
        
        if not full_path.exists():
            return filename

def enough_space(cfg: dict[str, Any]) -> int:
    """
    [INTERNAL] 检查数据目录大小是否超过 warn 和 max 限制

    Returns:
        一个 int，0 = 未超限，1 = 超过 warn，2 = 超过 max
    """
    storage = Path(cfg['storage']['path'])
    size = sum(f.stat().st_size for f in storage.rglob('*') if f.is_file()) / 1024 / 1024
    
    if 'max' in cfg['storage']:
        if size > cfg['storage']['max'] and cfg['storage']['max'] != 0:
            return 2

    if 'warn' in cfg['storage']:
        if size > cfg['storage']['warn'] and cfg['storage']['warn'] != 0:
            return 1
    
    return 0

def join_url(a: str, b: str) -> str:
    """
    连接两个 URL

    Args:
        a, b: 需要连接的 URL
    
    Returns:
        连接后的 URL
    """
    a = a.rstrip('/')
    b = b.lstrip('/')
    return a + '/' + b

def list_dir(path: Path) -> list[str]:
    return [item.name for item in path.iterdir() if not item.name.startswith('.')]

def is_attempting_traversal(comp: str) -> bool:
    """
    防止路径攻击未授权访问

    Args:
        comp: 路径中的部分（非完整路径）
    
    Returns:
        True 表示是危险请求，False 表示安全
    """
    if '..' in comp or '/' in comp or '\\' in comp:
        return True
    return False
