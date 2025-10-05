import sys
from datetime import datetime

class p_logger:
    """
    简单的日志模块，支持文件输出和分级日志

    Attributes:
        _level: [INTERNAL] 日志等级（0 = INFO, 1 = WARN, 2 = ERROR）
        _time_format: [INTERNAL] 时间格式
        _fileio: [INTERNAL] 输出
    """
    def __init__(self,
                 log_level: int,
                 time_format: str = "%Y/%m/%d %H:%M:%S",
                 path: str | None = None):
        """
        指定日志级别、时间格式、是否写入到文件

        Args:
            log_level: 日志级别
            time_format: 时间格式，默认为 %Y/%m/%d %H:%M:%S
            path: 输出路径，默认为 None（输出到 stderr）
        """
        if log_level < 0 or log_level > 2:
            raise ValueError
        else:
            self._level = log_level
        self._time_format = time_format
        if path:
            self._fileio = open(path, "a")
        else:
            self._fileio = sys.stderr
    
    def _format_msg_head(self, type: int) -> str:
        """
        [INTERNAL] 格式化消息头

        Args:
            type: 消息类型，即重要级别
        
        Returns:
            包含时间和有颜色的类别名的消息头
        """
        time_r = datetime.now().strftime(self._time_format)
        if type == 0:
            type_r = "\x1b[34mINFO\x1b[0m "
        elif type == 1:
            type_r = "\x1b[33mWARN\x1b[0m "
        else:
            type_r = "\x1b[31mERROR\x1b[0m"
        return time_r + " " + type_r + " "

    def info(self, message: str):
        """
        输出调试信息，最低的重要性

        Args:
            message: 信息内容
        """
        if self._level > 0:
            return
        else:
            self._fileio.write(self._format_msg_head(0) + message + '\n')
    
    def warn(self, message: str):
        """
        输出警告信息，中等重要性

        Args:
            message: 信息内容
        """
        if self._level > 1:
            return
        else:
            self._fileio.write(self._format_msg_head(0) + message + '\n')
    
    def error(self, message: str):
        """
        输出错误信息，最高重要性，无视 level

        Args:
            message: 信息内容
        """
        self._fileio.write(self._format_msg_head(0) + message + '\n')
