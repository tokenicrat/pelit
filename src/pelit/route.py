import re
from flask import Blueprint, request, Response, jsonify, send_file
from typing import Any
from pathlib import Path
from pelit.plib.log import p_logger
from pelit.plib.route_tool import *
from multiprocessing import Process

def create_route(cfg: dict[str, Any], lg: p_logger) -> Blueprint:
    """
    创建路径，使用 Flask Blueprint

    Args:
        cfg: 配置文件，同 TOML 加载的
    
    Returns:
        一个 Blueprint，包含所有路径定义
    """
    main_route = Blueprint("main_route", __name__)

    @main_route.route('/upload/<directory>', methods=['POST'])
    def _upload(directory: str) -> tuple[Response, int]:
        """
        上传接口，请求格式、响应、状态码列表参见 Pelit 文档

        Args:
            directory: 上传文件的保存目录
        
        Returns:
            上传结果，包括 JSON 格式的响应和状态码
        """
        info_head = f"{request.remote_addr} {request.method} {request.path}"

        if not authenticate(cfg):
            lg.warn(f"{info_head} 401: 认证失败")
            return jsonify({
                "success": False,
                "message": "认证失败"
            }), 401
        
        if is_attempting_traversal(directory):
            lg.warn(f"{info_head} 403 危险请求")
            return jsonify({
                "success": False,
                "message": "危险请求"
            }), 403

        # 请求需要包含文件上传
        if 'file' not in request.files:
            lg.warn(f"{info_head} 400: 未包含文件")
            return jsonify({
                    "success": False,
                    "message": "未包含文件"
                }), 400

        # 检查是否超过存储空间限制
        size_warn: int = enough_space(cfg)
        if size_warn == 2:
            lg.warn(f"{info_head} 502: 存储空间超限")
            return jsonify({
                "success": False,
                "message": "存储空间已超过限制"
            }), 502
        
        # 验证文件名不为空
        file = request.files['file']
        if file.filename == '':
            lg.warn(f"{info_head} 400: 无效的文件")
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
        # 保存目录
        storage_path = Path(cfg['storage']['path'])
        path = storage_path / directory
        # 文件名，无后缀
        name = generate_file_name(path, ext)

        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                lg.warn(f'{info_head} 502 创建目录失败: {path}')
                lg.warn(f'这是一个内部错误，请检查配置')
                lg.warn(str(e))
                return jsonify({
                    "success": False,
                    "message": "创建目录失败"
                }), 502

        # 尝试保存文件
        try:
            file_path = path / (name + ext)
            file.save(str(file_path))
            url_path = Path(directory) / (name + ext)
            resp: dict[str, Any] = {
                "success": True,
                "message": "保存成功",
                "url": join_url(cfg['network']['base_url'] if 'base_url' in cfg['network'] else '', 
                                 url_path.as_posix())
            }
            if size_warn == 1:
                resp["warning"] = "存储空间已达警告值"
                lg.warn(f"存储空间已达警告值")
            lg.info(f"{info_head} 200: 保存成功")
            lg.info(f"地址: {resp['url']}")
            return jsonify(resp), 200
        except Exception as e:
            lg.warn(f"{info_head} 502: 保存失败")
            lg.warn("这是一个服务端错误，请检查配置")
            lg.warn(str(e))
            return jsonify({
                "success": False,
                "message": "保存失败"
            }), 502

    @main_route.route('/delete/<directory>/<file>', methods=['DELETE'])
    def _delete(directory: str, file: str) -> tuple[Response, int]:
        """
        删除接口，请求格式、响应、状态码列表参见 Pelit 文档

        Args:
            directory: 删除的文件所在目录
            file: 删除的文件名
        
        Returns:
            删除结果，包含 JSON 格式的响应和状态码
        """
        info_head = f"{request.remote_addr} {request.method} {request.path}"

        if not authenticate(cfg):
            lg.warn(f"{info_head} 401: 认证失败")
            return jsonify({
                "success": False,
                "message": "认证失败"
            }), 401
        
        if is_attempting_traversal(directory):
            lg.warn(f"{info_head} 403 危险请求")
            return jsonify({
                "success": False,
                "message": "危险请求"
            }), 403
       
        path = Path(cfg['storage']['path']) / directory / file
        try:
            path.unlink()
            lg.info(f'{info_head} 200 删除成功')
            return jsonify({
                "success": True,
                "message": "删除成功"
            }), 200
        except FileNotFoundError:
            lg.info(f"{info_head} 404 未找到文件")
            return jsonify({
                "success": False,
                "message": "没有找到文件"
            }), 404
        except Exception as e:
            lg.warn(f'{info_head} 502 删除失败')
            lg.warn(f'这是一个内部错误，请检查配置')
            lg.warn(str(e))
            return jsonify({
                "success": False,
                "message": "创建目录失败"
            }), 502

    @main_route.route('/list', methods=['GET'])
    @main_route.route('/list/<directory>', methods=['GET'])
    def _list(directory: str = "/") -> tuple[Response, int]:
        """
        列出指定目录下所有目录

        Args:
            directory: 列举地址，未指定时默认为根目录

        Returns:
            JSON 格式的列表和响应码
        """
        info_head = f"{request.remote_addr} {request.method} {request.path}"

        if not authenticate(cfg):
            lg.warn(f"{info_head} 401: 认证失败")
            return jsonify({
                "success": False,
                "message": "认证失败"
            }), 401
        
        if is_attempting_traversal(directory):
            lg.warn(f"{info_head} 403 危险请求")
            return Response("禁止访问"), 403

        try:
            path = Path(cfg['storage']['path']) / directory
            resp: dict[str, Any] = {
                "success": True,
                "message": "",
                "list": list_dir(path)
            }
            lg.info(f'{info_head} 200 列举成功')
            return jsonify(resp), 200
        except FileNotFoundError:
            lg.info(f'{info_head} 404 未找到目录')
            return jsonify({
                "success": False,
                "message": "未找到目录"
            }), 404
        except Exception as e:
            lg.warn(f'{info_head} 502 列举失败')
            lg.warn('这是一个内部错误，请检查配置')
            lg.warn(f'{e}')
            return jsonify({
                "success": False,
                "message": "列举失败"
            }), 502

    @main_route.route('/<directory>/<file>', methods=['GET'])
    def _retrieve(directory: str, file: str) -> tuple[Response, int]:
        """
        获取指定文件，包括反盗链支持

        在生产环境中，此功能应当由服务器提供，Pelit 的服务仅供测试

        Args:
            directory: 文件所在目录
            file: 文件名
        
        Returns:
            获取的文件和状态码
        """
        info_head = f"{request.remote_addr} {request.method} {request.path}"

        if is_attempting_traversal(directory) or is_attempting_traversal(file):
            lg.warn(f"{info_head} 403 危险请求")
            return Response("禁止访问"), 403
        
        # 验证 Referer 请求头
        referer =  request.headers.get("Referer")
        if 'hotlink_block' in cfg['network']:
            if cfg['network']['hotlink_block']:
                if not referer or 'hotlink_whitelist' not in cfg['network']:
                    lg.info(f"{info_head} 403 反盗链阻止")
                    return Response("禁止外链"), 403
                match = False
                for rule in cfg['network']['hotlink_whitelist']:
                    assert isinstance(rule, str)
                    assert isinstance(referer, str)
                    # 也允许直接匹配（忽略 . 在 RegEx 中的作用）
                    if referer == rule:
                        match = True
                        break
                    if re.fullmatch(rule, referer):
                        match = True
                        break
                if not match:
                    lg.info(f"{info_head} 403 反盗链阻止")
                    return Response("禁止外链"), 403
        
        # 禁止访问隐藏的文件
        if directory.startswith('.') or file.startswith('.'):
            return Response("禁止访问"), 403

        # 返回文件
        f_path = Path(cfg['storage']['path']) / directory / file
        if not f_path.exists():
            return Response("未找到文件"), 404
        try:
            lg.info(f"{info_head} 200")
            return send_file(str(f_path)), 200
        except Exception as e:
            lg.warn(f"{info_head} 502 发送文件失败")
            lg.warn(f"这是一个内部错误，请检查配置")
            lg.warn(f"{e}")
            return Response("内部错误"), 502

    @main_route.route('/backup', methods=['GET'])
    @main_route.route('/backup/<directory>', methods=['GET'])
    def _backup(directory: str = '/') -> tuple[Response, int]:
        """
        创建一个备份任务，具体方式在配置文件中指定

        Returns:
            包含响应和状态码
        """
        info_head = f"{request.remote_addr} {request.method} {request.path}"

        bak_name = generate_file_name(cfg['storage']['path'], '.tar.gz')
        bak_path = Path(cfg['storage']['path']) / (bak_name + '.tar.gz')
        bak_url = join_url(cfg['network']['base_url'], bak_name + '.tar.gz')

        path = Path(cfg['storage']['path']) / directory

        # 创建新进程压缩备份
        # FIXME: 由于是多进程的，这个任务失败了也不会有表示
        p = Process(target=backup_to_file, args=(path, bak_path))
        p.start()

        lg.info(f"{info_head} 200 备份任务创建成功")
        return jsonify({
            "success": True,
            "url": bak_url,
            "message": "备份任务创建成功"
        }), 200

    return main_route
