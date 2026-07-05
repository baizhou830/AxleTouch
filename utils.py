import sys
import os


def get_base_path():
    """获取资源文件路径（打包后取 _MEIPASS，源码运行取脚本目录）"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_data_path():
    """获取用户数据文件路径（exe 所在目录或脚本目录）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))
