import os
import importlib
import subprocess
from colorama import Fore, Style

def check_and_install_libraries(libraries):
    for library in libraries:
        try:
            # 尝试导入库，如果导入成功，则该库已经安装
            importlib.import_module(library)
        except ImportError:
            # 如果导入失败，则该库未安装
            print(f"库 '{library}' 未安装。")
            # 提示用户是否要安装该库
            install = input(f"你想要安装库 '{library}' 吗？按回车键确认，或者输入其他任何内容跳过：")
            if install == '':
                # 如果用户按下回车键，则安装该库
                subprocess.check_call(["python", "-m", "pip", "install", library])
                print(f"库 '{library}' 已经安装。")
            else:
                print(f"已跳过库 '{library}' 的安装。")

def run_script():
    libraries = ['os', 'json', 'typing', 'requests', 'colorama', 'api', 'config']
    check_and_install_libraries(libraries)

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
        # 在这里添加你的帮助信息
        print("0. 详细帮助说明请访问：https://github.com/cnlaok/MeidaAO 。")
        print("1. 目录结构必须是【你的目录/剧集或电影文件夹/媒体文件或其他子目录】")
        print("2. 执行重命名剧集或者电影文件前建议先重命名文件夹")
        print("3. 个别原文件夹或者文件本身命名信息错误的需要自己根据TMDB信息手动输入匹配")
    else:
        print("输入的序号无效。")

if __name__ == "__main__":
    run_script()
