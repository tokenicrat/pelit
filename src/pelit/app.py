import sys
from flask import Flask
from pelit.plib.result import Err
from pelit.plib.arg import parse_arguments
from pelit.plib.log import p_logger
from pelit.plib.config import parse_config
from pelit.route import create_route

# 准备配置文件
def create_app() -> Flask:
    # 处理参数
    cmd = parse_arguments(sys.argv)
    if isinstance(cmd, Err):
        print(cmd)
        exit(1)
    cmd = cmd.value

    # 创建日志组件
    lg = p_logger(cmd['verbosity'], path=cmd['log_path'])

    # 验证配置文件
    cfg = parse_config(cmd['config_path'])
    if isinstance(cfg, Err):
        lg.error(str(cfg))
        exit(1)
    cfg = cfg.value

    # 如果是验证配置文件，到这里就足够了
    if cmd['check_only']:
        lg.info("配置文件有效")
        exit(0)

    # 导入 route.py 定义的路径
    route = create_route(cfg, lg)

    # 创建 Flask 应用
    app = Flask(__name__)
    app.register_blueprint(route)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run()
