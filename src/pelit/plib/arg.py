from typing import TypedDict
from pelit.plib.result import Ok, Err, Result


# 命令行参数格式
# TODO: 添加日志格式指定支持
class Commandline_params(TypedDict):
    check_only: bool
    config_path: str
    verbosity: int
    log_path: str | None

def parse_arguments(args: list[str]) -> Result[Commandline_params, str]:
    cmd: Commandline_params = {
        "check_only": False,
        "config_path": "",
        "verbosity": 1,
        "log_path": None
    }
    
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
