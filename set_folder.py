import os
import shutil
import re

class MediaFileHandler:
    def __init__(self, config):
        self.video_suffix_list = config['video_suffix_list'].split(',')
        self.source_dir = config['source_dir']
        self.target_dir = config['target_dir']

    def get_media_files(self):
        media_files = []
        for root, dirs, files in os.walk(self.source_dir):
            for file in files:
                if any(file.endswith(suffix) for suffix in self.video_suffix_list):
                    media_files.append(os.path.join(root, file))
        return media_files

    def get_empty_folders(self):
        empty_folders = []
        for root, dirs, _ in os.walk(self.target_dir):
            if not dirs and not os.listdir(root):
                empty_folders.append(root)
        return empty_folders

    def move_files(self, media_files, empty_folders):
        for media_file in media_files:
            if not empty_folders:
                break
            folder = empty_folders.pop(0)
            new_folder_name = self.get_new_folder_name(media_file)
            new_folder_path = os.path.join(self.source_dir, new_folder_name)
            if os.path.exists(new_folder_path):
                i = 1
                while os.path.exists(f"{new_folder_path}_{i}"):
                    i += 1
                new_folder_path = f"{new_folder_path}_{i}"
            shutil.move(folder, new_folder_path)  # 将空文件夹移动到源目录并重命名
            shutil.move(media_file, os.path.join(new_folder_path, os.path.basename(media_file)))  # 将媒体文件移动到已移动的空文件夹中
            print(f"Moved {media_file} to {os.path.join(new_folder_path, os.path.basename(media_file))}")



    def get_new_folder_name(self, media_file):
        elements = self.get_file_info(media_file)
        return f"{elements['chinese_title']} ({elements['year']})"

    def get_file_info(self, file_path: str) -> dict:
        file_name_no_ext, _ = os.path.splitext(os.path.basename(file_path))
        file_name_no_ext = file_name_no_ext.replace('.', ' ')
        file_name_no_ext = file_name_no_ext.upper()

        elements = {'chinese_title': None, 'year': None}
        chinese_title = re.search(r'《.*?》', file_name_no_ext)
        if chinese_title:
            elements['chinese_title'] = chinese_title.group(0)[1:-1]
            file_name_no_ext = file_name_no_ext.replace(chinese_title.group(0), '')
        else:
            chinese_title = re.search(r'[\u4e00-\u9fff0-9a-zA-Z：，·-]+', file_name_no_ext)
            if chinese_title:
                if re.search(r'[\u4e00-\u9fff]', chinese_title.group(0)):
                    elements['chinese_title'] = chinese_title.group(0)
                    file_name_no_ext = file_name_no_ext.replace(chinese_title.group(0), '')
                else:
                    elements['chinese_title'] = None
            else:
                elements['chinese_title'] = None

        year = re.search(r'\b\d{4}\b', file_name_no_ext)
        if year:
            elements['year'] = year.group(0)

        return elements

config = {
    'video_suffix_list': '.mp4,.mkv,.flv,.avi,.mpg,.mpeg,.mov,.ts,.wmv,.rm,.rmvb,.3gp,.3g2,.webm,.mp4a,.f4v',
    'source_dir': 'Y:\\阿里云盘\\盘3.188.JD\\整理中\\1\\喜羊羊与灰太狼之喜气羊羊过蛇年 (2013) {tmdb-248080}',
    'target_dir': 'Y:\\阿里云盘\\盘3.188.JD\\整理中\\空文件夹'
}

handler = MediaFileHandler(config)
media_files = handler.get_media_files()
empty_folders = handler.get_empty_folders()
handler.move_files(media_files, empty_folders)
