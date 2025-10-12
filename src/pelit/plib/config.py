from typing import Any, Dict
from pelit.plib.result import Ok, Err, Result
import tomllib
from jsonschema import validate, ValidationError


# 定义用于 JSON Schema 的类型
JSONSchema = Dict[str, Any]

# 配置文件格式
config_schema: JSONSchema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["version", "network", "storage", "auth"],
    "properties": {
        "version": {
            "type": "string",
            "pattern": "^\\d+\\.\\d+\\.\\d+$"
        },
        "network": {
            "type": "object",
            "required": ["addr", "port"],
            "dependentRequired": {
                "api_addr": ["api_port"],
                "api_port": ["api_addr"]
            },
            "properties": {
                "base_url": {
                    "type": "string"
                },
                "addr": {
                    "type": "string",
                    "anyOf": [{"format": "ipv4"}, {"format": "ipv6"}]
                },
                "port": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 65535
                },
                "api_addr": {
                    "type": "string",
                    "anyOf": [{"format": "ipv4"}, {"format": "ipv6"}]
                },
                "api_port": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 65535
                },
                "hotlink_block": {
                    "type": "boolean"
                },
                "hotlink_whitelist": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "additionalProperties": False
        },
        "storage": {
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {
                    "type": "string"
                },
                "warn": {
                    "type": "number",
                    "minimum": 0
                },
                "max": {
                    "type": "number",
                    "minimum": 0
                }
            },
            "additionalProperties": False
        },
        "auth": {
            "type": "object",
            "properties": {
                "from_env": {
                    "type": "boolean"
                },
                "hashed": {
                    "type": "string",
                    "pattern": "^[A-Fa-f0-9]{64}$"
                }
            },
            "anyOf": [
                {"required": ["from_env"]},
                {"required": ["hashed"]}
            ],
            "additionalProperties": False
        }
    },
    "additionalProperties": False
}

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
