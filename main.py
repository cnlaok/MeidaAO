import os
import importlib
import subprocess
from typing import List
from colorama import Fore, Style
from config import ConfigManager  # 导入配置管理类


def check_and_install_libraries(libraries: List[str]) -> None:
    """
    检查并安装所需的库。

    参数:
        libraries (List[str]): 需要检查的库的列表。
    """
    for library in libraries:
        try:
            importlib.import_module(library)
        except ImportError:
            print(f"库 '{library}' 未安装。")
            install = input(f"你想要安装库 '{library}' 吗？按回车键确认，或者输入其他任何内容跳过：")
            if install == '':
                subprocess.check_call(["python", "-m", "pip", "install", library])
                print(f"库 '{library}' 已经安装。")
            else:
                print(f"已跳过库 '{library}' 的安装。")


def run_script() -> None:
    """
    运行脚本的主函数。
    """
    libraries = ['colorama']
    check_and_install_libraries(libraries)

    # 创建配置管理对象，并加载配置
    config_manager = ConfigManager('config.json')
    config = config_manager.load_config()

    # 检查配置是否完整
    if config_manager.check_config():
        print("配置文件检查完毕，所有配置都已完整。")
    else:
        config_manager.save_config()
        print("配置文件已补充完整。")

    scripts = ['rename_folder.py', 'rename_movie.py', 'rename_show.py']
    print(Fore.RED + '0. 开始程序，请选择你想要运行的脚本：' + Style.RESET_ALL)
    print(Fore.GREEN + '1. 整理媒体文件夹' + Style.RESET_ALL)
    print(Fore.GREEN + '2. 重命名电影文件' + Style.RESET_ALL)
    print(Fore.GREEN + '3. 重命名剧集文件' + Style.RESET_ALL)
    print(Fore.GREEN + '4. 脚本功能的说明' + Style.RESET_ALL)
    print(Fore.GREEN + '5. 详细帮助说明请访问：https://github.com/cnlaok/MeidaAO' + Style.RESET_ALL)
    choice = input(Fore.RED + '6.请输入你想要运行的脚本的序号：' + Style.RESET_ALL)
    if choice.isdigit() and 1 <= int(choice) <= len(scripts):
        os.system(f"python {scripts[int(choice)-1]}")
    elif choice == '4':
        print("0. 详细帮助说明请访问：https://github.com/cnlaok/MeidaAO 。")
        print("1. 目录结构必须是【你的目录/剧集或电影文件夹/媒体文件或其他子目录】")
        print("2. 执行重命名剧集或者电影文件前建议先重命名文件夹")
        print("3. 个别原文件夹或者文件本身命名信息错误的需要自己根据TMDB信息手动输入匹配")
    else:
        print("输入的序号无效。")


if __name__ == "__main__":
    run_script()
