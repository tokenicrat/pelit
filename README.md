> [!NOTE]
> ~~本项目作者想偷懒然后去写 R2 版~~，README 由 AI 生成（代码 0% AI 生成！），只做了最基本的检查，有问题请直接看代码，里面有详细的注释。

# Pelit

小而美的私有图床服务

## 简介

Pelit 是一个轻量级的私有图床解决方案，基于 Flask 和 Gunicorn 构建。提供 API 接口，支持简易的文件上传、删除、列表和备份等功能，适合个人低负载使用。

### 特性

- 用 Python 和 Flask 开发，代码简明，手动 hack 适应需求很简单
- 提供简易的防盗链、认证和备份功能
- 支持（并推荐）容器化部署

## 快速开始

### 开发环境部署

#### 1. 克隆仓库

```bash
git clone https://github.com/tokenicrat/pelit.git
cd pelit
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置文件

复制示例配置文件并修改：

```bash
cp examples/pelit.toml pelit.toml
```

编辑 `pelit.toml`，至少需要配置：

```toml
version = "0.1.0"

[network]
base_url = "http://localhost:8000"  # 你的服务地址

[storage]
path = "./data"  # 存储路径

[auth]
from_env = true  # 从环境变量读取密钥
```

#### 4. 设置环境变量

```bash
export PELIT_AUTH="your-secret-key"
export PELIT_CONFIG="./pelit.toml"
```

#### 5. 启动服务

使用内置工具启动：

```bash
python -m pelit.app
```

或使用 Gunicorn（推荐）：

```bash
gunicorn --config examples/gunicorn.conf.py wsgi:app
```

### 生产环境部署（Podman）

#### 1. 准备配置文件和数据目录

```bash
mkdir -p ./data
cp examples/pelit.toml ./config.toml
# 编辑 config.toml 配置你的设置
```

#### 2. 使用 Podman Compose

复制并修改 `examples/compose.yml`：

```bash
cp examples/compose.yml docker-compose.yml
# 可以在 compose.yml 中提供密钥环境变量
```

启动：

```bash
podman compose up -d
```

#### 4. Nginx 反向代理（可选）

参考 `examples/pelit.conf` 配置 Nginx：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert;
    ssl_certificate_key /path/to/key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 配置说明

### 配置文件结构

```toml
version = "0.1.0"

[network]
# 下载地址的 URL 前缀，用于生成完整的文件访问地址
base_url = "https://your-domain.com"

# 反盗链功能（验证 Referer 请求头）
hotlink_block = false
# 白名单域名，支持 * 通配符
hotlink_whitelist = ["example-a.com", "*.example-b.com"]

[storage]
# 文件存储路径
path = "/data"

# 存储空间警告阈值（MB），设为 0 禁用
warn = 1000
# 存储空间最大限制（MB），超过后上传失败，设为 0 禁用
max = 2000

[auth]
# 从环境变量 PELIT_AUTH 读取密钥
from_env = true

# 或使用 SHA256 哈希后的密钥（16 进制格式）
# hashed = "9EBF8C8F69731148C2DD14C93EB021E58D2CDD253580576C92F6102EF4F0610C"
```

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `PELIT_CONFIG` | 配置文件路径 | 是 |
| `PELIT_AUTH` | 认证密钥（当 `auth.from_env=true` 时） | 条件必需 |
| `PELIT_VERBOSITY` | 日志级别：0=INFO, 1=WARN, 2=ERROR | 否 |
| `PELIT_LOG` | 日志文件路径 | 否 |

## API 接口

### 认证

所有需要认证的接口都需要在请求头中包含：

```
Authorization: your-secret-key
```

或使用 Bearer 格式：

```
Authorization: Bearer your-secret-key
```

### 上传文件

**请求**

```http
POST /upload/<directory>
Content-Type: multipart/form-data
Authorization: your-secret-key

file: <binary-file>
```

**响应**

```json
{
  "success": true,
  "message": "保存成功",
  "url": "https://your-domain.com/directory/filename.ext",
  "warning": "存储空间已达警告值"  // 可选字段
}
```

**状态码**

- `200` - 上传成功
- `400` - 请求格式错误
- `401` - 认证失败
- `403` - 危险请求（路径遍历攻击）
- `502` - 服务器错误

### 删除文件

**请求**

```http
DELETE /delete/<directory>/<filename>
Authorization: your-secret-key
```

**响应**

```json
{
  "success": true,
  "message": "删除成功"
}
```

**状态码**

- `200` - 删除成功
- `401` - 认证失败
- `403` - 危险请求
- `404` - 文件不存在
- `502` - 服务器错误

### 列出文件/目录

**请求**

```http
GET /list
GET /list/<directory>
Authorization: your-secret-key
```

**响应**

```json
{
  "success": true,
  "message": "",
  "list": ["file1.jpg", "file2.png", "subdirectory"]
}
```

**状态码**

- `200` - 列举成功
- `401` - 认证失败
- `403` - 危险请求
- `404` - 目录不存在
- `502` - 服务器错误

### 获取文件

**请求**

```http
GET /<directory>/<filename>
```

此接口会验证反盗链设置（如果启用）。

**状态码**

- `200` - 返回文件内容
- `403` - 反盗链阻止或禁止访问
- `404` - 文件不存在
- `502` - 服务器错误

### 创建备份

**请求**

```http
GET /backup
GET /backup/<directory>
Authorization: your-secret-key
```

**响应**

```json
{
  "success": true,
  "url": "https://your-domain.com/backup-file.tar.gz",
  "message": "备份任务创建成功"
}
```

备份任务会在后台异步执行，完成后可通过返回的 URL 下载。

**状态码**

- `200` - 备份任务创建成功
- `401` - 认证失败

## 命令行工具

Pelit 提供了命令行工具进行管理操作。

**检查配置**

```bash
python -m pelit.app check -c /path/to/config.toml
```

**运行服务**

```bash
python -m pelit.app run -c /path/to/config.toml -v 0 -l /path/to/log
```

**参数说明**

- `-c, --config` - 配置文件路径（必需）
- `-v, --verbose` - 日志级别：0=INFO, 1=WARN, 2=ERROR
- `-l, --log` - 日志文件路径

### pelit 上传脚本

`src/tools/pelit` 是一个 Bash 脚本，用于简化文件上传操作。

**配置脚本**

编辑脚本中的配置：

```bash
API_URL="https://your-domain.com"
AUTH="your-secret-key"
```

**使用方法**

```bash
# 上传本地文件
./pelit upload /path/to/file.jpg my-directory

# 上传远程文件（通过 URL）
./pelit upload https://example.com/image.png my-directory

# 删除文件
./pelit delete my-directory/file.jpg

# 列出目录
./pelit list my-directory
./pelit list /  # 列出根目录
```

## 安全建议

1. **使用强密钥**：生成随机的强密钥用于认证
   ```bash
   openssl rand -hex 32
   ```

2. **使用哈希密钥**：在生产环境建议使用 SHA256 哈希后的密钥
   ```bash
   echo -n "your-secret-key" | sha256sum
   ```

3. **启用 HTTPS**：使用 Nginx 等反向代理提供 SSL/TLS 加密

4. **配置防盗链**：在配置文件中启用 `hotlink_block` 并设置白名单

5. **限制存储空间**：设置 `storage.max` 防止磁盘被占满

6. **定期备份**：使用 `/backup` 接口定期备份数据

## 开发指南

### 项目结构

```
pelit/
├── src/
│   ├── pelit/
│   │   ├── __init__.py
│   │   ├── app.py           # Flask 应用创建
│   │   ├── route.py         # 路由定义
│   │   └── plib/            # 工具库
│   │       ├── arg.py       # 参数解析
│   │       ├── config.py    # 配置文件解析
│   │       ├── log.py       # 日志模块
│   │       ├── result.py    # Result 类型（Rust 风格）
│   │       └── route_tool.py # 路由工具函数
│   ├── tools/               # 命令行工具
│   └── wsgi.py              # WSGI 入口
├── examples/                # 示例配置
├── Containerfile            # 容器镜像定义
└── pyproject.toml           # 项目元数据
```

### 代码风格

- 使用 Python 3.13 类型注解
- 遵循 PEP 8 代码风格
- 使用 Rust 风格的 Result 类型处理错误

### 运行测试

```bash
# TODO: 添加测试用例
```

## 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 贡献

欢迎提交 Issue 和 Pull Request！

- 仓库：https://github.com/tokenicrat/pelit
- 问题反馈：https://github.com/tokenicrat/pelit/issues
