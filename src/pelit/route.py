from flask import Blueprint, request, Response, jsonify
from typing import Any, Optional, Tuple
import os
import secrets
from pathlib import Path
import hashlib
from pelit.plib.log import p_logger

def create_route(cfg: dict[str, Any], logger: p_logger) -> Blueprint:
    """
    创建路径，使用 Flask Blueprint

    Args:
        cfg: 配置文件，同 TOML 加载的
    
    Returns:
        一个 Blueprint，包含所有路径定义
    """
    main_route = Blueprint("main_route", __name__)

    def _authenticate() -> bool:
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

    def _generate_file_name(directory: str, extension: str) -> str:
        """
        [INTERNAL] 随机生成一个有效的文件（路径）名

        Args:
            directory: 保存目录的名字，可以是空字符串
            extension: 保存的拓展名，可以是空字符串
        
        Returns:
            有效的 str 类型文件名，无后缀
        """
        while True:
            filename = secrets.token_hex(10)
            full_path: Path = Path(directory) / (filename + extension)
            
            if not full_path.exists():
                return filename

    def _enough_space() -> int:
        """
        [INTERNAL] 检查数据目录大小是否超过 warn 和 max 限制

        Returns:
            一个 int，0 = 未超限，1 = 超过 warn，2 = 超过 max
        """
        storage = Path(cfg['storage']['path'])
        size = sum(f.stat().st_size for f in storage.rglob('*') if f.is_file()) / 1024 / 1024
        
        if 'max' in cfg['storage']:
            if size > cfg['storage']['max']:
                return 2

        if 'warn' in cfg['storage']:
            if size > cfg['storage']['warn']:
                return 1
        
        return 0

    def _join_url(a: str, b: str) -> str:
        """
        连接两个 URL

        Args:
            a, b: 需要连接的 URL
        
        Returns:
            连接后的 URL
        """
        if a.endswith('/'):
            a.rstrip('/')
        if b.startswith('/'):
            b.lstrip('/')
        return a + '/' + b

    # 上传接口
    @main_route.route('/upload/<directory>', methods=['POST'])
    def upload(directory: str) -> Tuple[Response, int]:
        info_head = f"{request.remote_addr} {request.method} {request.path}"
        if not _authenticate():
            logger.warn(f"{info_head} 401: 认证失败")
            return jsonify({
                "success": False,
                "message": "认证失败"
            }), 401
        
        # 请求需要包含文件上传
        if 'file' not in request.files:
            logger.warn(f"{info_head} 400: 未包含文件")
            return jsonify({
                    "success": False,
                    "message": "未包含文件"
                }), 400

        # 检查是否超过存储空间限制
        size_warn: int = _enough_space()
        if size_warn == 2:
            logger.warn(f"{info_head} 502: 存储空间超限")
            return jsonify({
                "success": False,
                "message": "存储空间已超过限制"
            }), 502
        
        # 验证文件名不为空
        file = request.files['file']
        if file.filename == '':
            logger.warn(f"{info_head} 400: 无效的文件")
            return jsonify({
                "success": False,
                "message": "无效的文件"
            }), 400
        
        # 构建后缀、文件名和路径
        assert file.filename is not None
        # 源文件后缀名
        ext = Path(file.filename).suffix.lstrip('.')
        if not ext == '':
            ext = '.' + ext
        # 文件名，无后缀
        name = _generate_file_name(str(Path(cfg['storage']['path']) / directory), ext)
        # 保存目录
        path = Path(cfg['storage']['path']) / directory

        if not path.exists():
            try:
                os.mkdir(str(path))
            except Exception as e:
                logger.warn(f'{info_head} 502 创建目录失败: {str(path)}')
                logger.warn(f'这是一个内部错误，请检查配置')
                logger.warn(str(e))
                return jsonify({
                    "success": False,
                    "message": "创建目录失败"
                }), 502

        # 尝试保存文件
        try:
            file.save(str(path / (name + ext)))
            resp: dict[str, Any] = {
                "success": True,
                "message": "保存成功",
                "url": _join_url(cfg['network']['base_url'] if 'bare_url' in cfg['network'] else '', \
                                 str(Path(directory) / (name + ext)))
            }
            if size_warn == 1:
                resp["warning"] = "存储空间已达警告值"
                logger.warn(f"存储空间已达警告值")
            logger.info(f"{info_head} 200: 保存成功")
            logger.info(f"地址: {resp['url']}")
            return jsonify(resp), 200
        except Exception as e:
            logger.warn(f"{info_head} 502: 保存失败")
            logger.warn("这是一个服务端错误，请检查配置")
            logger.warn(str(e))
            return jsonify({
                "success": False,
                "message": "保存失败"
            }), 502

    @main_route.route('/delete/<directory>/<file>', methods=['DELETE'])
    def delete(directory: str, file: str) -> Tuple[Response, int]:
        info_head = f"{request.remote_addr} {request.method} {request.path}"
        path = Path(cfg['storage']['path']) / directory / file
        try:
            os.remove(str(path))
            logger.info(f'{info_head} 200 删除成功')
            return jsonify({
                "success": True,
                "message": "删除成功"
            }), 200
        except Exception as e:
            logger.warn(f'{info_head} 502 删除失败')
            logger.warn(f'这是一个内部错误，请检查配置')
            logger.warn(str(e))
            return jsonify({
                "success": False,
                "message": "创建目录失败"
            }), 502

    return main_route
