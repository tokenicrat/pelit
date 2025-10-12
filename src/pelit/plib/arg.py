import os
from typing import TypedDict
from pelit.plib.result import Ok, Err, Result

# 命令行参数格式
class Commandline_params(TypedDict):
    check_only: bool
    config_path: str
    verbosity: int
    log_path: str | None

def parse_arguments(args: list[str]) -> Result[Commandline_params, str]:
    """
    读取命令行参数

    Args:
        args: 传入的命令行参数列表
    
    Returns:
        Result 类型的参数解析，若解析失败则返回 Err
    """
    cmd: Commandline_params = {
        "check_only": False,
        "config_path": "",
        "verbosity": 1,
        "log_path": None
    }

    if len(args) < 2:
        return Err("缺少参数")

    # 第一个参数是动词
    verb: str = args[1]
    if verb == "check":
        cmd["check_only"] = True
    elif verb == "run":
        cmd["check_only"] = False
    else:
        return Err(f"未知动词: {verb}")

    # 处理传入值的选项
    i = 2
    while i < len(args):
        option: str = args[i]
        if i + 1 > len(args) - 1:
            return Err(f"参数 {option} 缺少值")
        value: str = args[i + 1]

        match option:
            case "-c" | "--config":
                cmd["config_path"] = value
            case "-v" | "--verbose":
                try:
                    cmd["verbosity"] = int(value)
                except ValueError:
                    return Err(f"参数 {option} 应为正整数")
                if int(value) < 0 or int(value) > 2:
                    return Err(f"无效的级别: {value}")
            case "-l" | "--log":
                cmd["log_path"] = value
            case unknown_command:
                return Err(f"未知选项: {unknown_command}")
        i += 2

    if not cmd["config_path"]:
        return Err("必须指定 --config 或 -c")

    return Ok(cmd)

def parse_envvars() -> Result[Commandline_params, str]:
    """
    读取通过环境变量传入的配置

    Returns:
        Result 类型的参数解析，若解析失败则返回 Err
    """
    cmd: Commandline_params = {
        "check_only": False,
        "config_path": "",
        "verbosity": 1,
        "log_path": None
    }

    config_path = os.getenv('PELIT_CONFIG')
    if config_path:
        cmd["config_path"] = config_path
    else:
        return Err("无效的环境变量配置")
    
    verbosity = os.getenv('PELIT_VERBOSITY')
    if verbosity:
        try:
            cmd["verbosity"] = int(verbosity)
        except:
            return Err("无效的日志等级")
    
    log_path = os.getenv('PELIT_LOG')
    if log_path:
        cmd["log_path"] = log_path
    
    return Ok(cmd)
