# -*- coding: utf-8 -*-
# 这行代码定义了脚本的字符编码为UTF-8。

# @Time : 2023/10/30
# @File : main.py
# 这两行是注释，提供了文件创建的时间和文件名。

import os
from TMDBApi import TMDBApi
from MediaToolKit import MediaRenamer, Utils
from config_utils import ServerConfig  
# 这四行代码导入了所需的模块和类。

CONFIG_FILE = 'config.json' 
# 定义了一个常量，表示配置文件的名称。

def main():
    # 定义了主函数。

    server_config = ServerConfig(CONFIG_FILE)  
    # 创建了一个ServerConfig对象，用于读取配置文件。

    plex_url, plex_token, tmdb_api_key = server_config.get_server_info_and_key()  
    # 从配置文件中获取Plex服务器信息和TMDB API密钥。

    renamer = MediaRenamer(server_config)  
    # 创建了一个MediaRenamer对象，用于重命名媒体文件。

    print("\033[34m请选择匹配模式：\033[0m")
    print("\033[34m1. 先匹配Plex，后匹配TMDB\033[0m")
    print("\033[34m2. 直接匹配TMDB\033[0m")
    print("\033[34m3. 转换命名格式\033[0m")
    print("\033[34m4. 清理文件夹名\033[0m")
    # 打印出用户可以选择的匹配模式。

    match_mode_index = int(input("\033[32m请输入你选择的匹配模式编号（默认为1）:\033[0m ") or "1")
    # 获取用户输入的匹配模式编号。如果用户没有输入，则默认为1。

    if match_mode_index == 4:
        renamer.match_mode_4(parent_folder_path)
        exit()
    # 如果用户选择的是第4种匹配模式，则执行相应的函数并退出程序。

    print("\033[34m请选an择库的类型：\033[0m")
    print("\033[34m1. 电影\033[0m")
    print("\033[34m2. 剧集\033[0m")
    # 打印出用户可以选择的库类型。

    library_type_index = int(input("\033[32m请输入你选择的库的类型编号（默认为1）:\033[0m ") or "1")
    # 获取用户输入的库类型编号。如果用户没有输入，则默认为1。

    print("\033[34m请选择命名规则：\033[0m")
    print("\033[34m1. 中文名 (年份)\033[0m")
    print("\033[34m2. 中文名 (年份) {tmdb-id}\033[0m")
    print("\033[34m3. 中文名.(年份).{tmdb-id}\033[0m")
    # 打印出用户可以选择的命名规则。

    naming_rule_index = int(input("\033[32m请输入你选择的命名规则的编号（默认为1）:\033[0m ") or "1")
    # 获取用户输入的命名规则编号。如果用户没有输入，则默认为1。

    parent_folder_path = input("请输入父文件夹的路径：")
    # 获取用户输入的父文件夹路径。

    filename = renamer.get_filename_by_library_type(library_type_index)
    
    if filename is None:
        return
     # 根据库类型获取文件名。如果获取失败，则返回None并退出函数。

     renamer.processed_folders = renamer.load_processed_folders(filename)
     # 加载已处理过的文件夹列表。
     
     if match_mode_index == 1:
         renamer.match_mode_1(parent_folder_path, library_type_index, naming_rule_index)
     elif match_mode_index == 2:
         renamer.match_mode_2(parent_folder_path, library_type_index, naming_rule_index)
     elif match_mode_index == 3:
         renamer.match_mode_3(parent_folder_path, naming_rule_index)
     # 根据用户选择的匹配模式，执行相应的函数。
     
if __name__ == "__main__":
   main()
# 如果这个脚本是直接运行的，而不是被导入的，那么就执行main函数。

