import sys
from pelit.plib.result import Ok, Err, Result
import pelit.plib.arg as arg
import pelit.plib.log as log
import pelit.plib.config as config

# TODO: 重构主要逻辑
def create_app():
    # 处理参数
    cmd = arg.parse_arguments(sys.argv)
    if isinstance(cmd, Err):
        print(cmd)
        exit(1)
    cmd = cmd.value

    # 创建日志组件
    lg = log.p_logger(cmd['verbosity'], path=cmd['log_path'])

    # 验证配置文件
    cfg = config.parse_config(cmd['config_path'])
    if isinstance(cfg, Err):
        lg.error(str(cfg))
        exit(1)
    cfg = cfg.value

    # 如果是验证配置文件，到这里就足够了
    if cmd['check_only']:
        lg.info("配置文件有效")
        exit(0)
    
    # TODO: Flask 启动！

if __name__ == "__main__":
    create_app()
