import tomllib
from pelit.p_types.results import Result, Ok, Err
from typing import Any
from jsonschema import validate, ValidationError
from pelit.p_types.schemas import config_schema, Commandline_params
import sys


def parse_arguments() -> Result[Commandline_params, str]:
    """
    读取并检查命令行参数

    Returns:
        若读取、检查成功，返回 Commandline_params 类型的配置；否则，返回 str 类型的报错
    """
    cmd: Commandline_params = {
        "check_only": False,
        "config_path": None,
        "verbosity": 1
    }

    # 至少有动词和路径
    if len(sys.argv) < 4:
        return Err("参数不足")
    
    verb: str = sys.argv[1]
    if verb == "run":
        cmd["check_only"] = False
    elif verb == "check":
        cmd["check_only"] = True
    else:
        return Err(f"未知动词: {verb}")
    
    # 读取参数
    i = 2
    while i < len(sys.argv):
        option = sys.argv[i]
        if i + 1 > len(sys.argv) - 1:
            return Err(f"需要值: {option}")
        value = sys.argv[i + 1]
        if option == '--path' or option == '-p':
            cmd["config_path"] = value
        elif option == '--verbose' or option == '-v':
            try:
                cmd["verbosity"] = int(value)
            except ValueError:
                return Err(f"值应当为整数: {option}")
        else:
            return Err(f"未知选项: {option}")
        
        i += 2
    
    # 必须有路径
    if not cmd["config_path"]:
        return Err(f"未设置配置文件")
    
    return Ok(cmd)

def parse_config(path: str) -> Result[dict[str, Any], str]:
    """
    读取并检查配置
    
    Args:
        path: 配置文件的路径
    
    Returns:
        若读取、检查成功，返回 dict 类型的配置；否则，返回 str 类型的报错
    """
    # 尝试读取文件
    try:
        cfg_file = open(path, 'rb')
    except FileNotFoundError:
        return Err(f"{path}: 文件不存在")
    except PermissionError:
        return Err(f"{path}: 权限错误")
    except IsADirectoryError:
        return Err(f"{path}: 是目录")
    except IOError as e:
        return Err(f"{path}: 读取错误: {e}")

    # 解析 TOML
    try:
        cfg = tomllib.load(cfg_file)
    except tomllib.TOMLDecodeError:
        return Err(f"{path}: 无效的 TOML 文件")
    
    # 验证配置文件格式
    try:
        validate(cfg, config_schema)
    except ValidationError as e:
        return Err(f"{path}: 无效的配置；详细信息如下\n{e}")

    return Ok(cfg)
    

def create_app():
    pass
