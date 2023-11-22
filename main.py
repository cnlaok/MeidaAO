import os

def run_script():
    scripts = ['rename_folder.py', 'rename_movie.py', 'rename_show.py']
    print("请选择你想要运行的脚本：")
    print("1. rename_folder,重命名文件夹")
    print("2. rename_movie, 重命名电影文件")
    print("3. rename_show,  重命名剧集文件")
    print("4. 脚本功能帮助")

    choice = input("请输入你想要运行的脚本的序号：")
    if choice.isdigit() and 1 <= int(choice) <= len(scripts):
        os.system(f"python {scripts[int(choice)-1]}")
    elif choice == '4':
        # 在这里添加你的帮助信息
        print("这是一个简单的脚本选择器。你可以通过输入相应的序号来选择你想要运行的脚本。")
        print("1. 重命名文件夹：这个脚本会重命名当前目录下的所有文件夹。")
        print("2. 重命名电影文件：这个脚本会重命名当前目录下的所有电影文件。")
        print("3. 重命名电视剧文件：这个脚本会重命名当前目录下的所有电视剧文件。")
    else:
        print("输入的序号无效。")

if __name__ == "__main__":
    run_script()
