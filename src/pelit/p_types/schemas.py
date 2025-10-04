from typing import Any, Dict, TypedDict


# 定义用于 JSON Schema 的类型，防止类型检查器报错
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
            "properties": {
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
                "storage_warn": {
                    "type": "boolean"
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
                    "type": "integer",
                    "minimum": 0
                },
                "max": {
                    "type": "integer",
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
            "oneOf": [
                {"required": ["from_env"]},
                {"required": ["hashed"]}
            ],
            "additionalProperties": False
        }
    },
    "additionalProperties": False
}

# 命令行参数格式
class Commandline_params(TypedDict):
    check_only: bool
    config_path: str | None
    verbosity: int
