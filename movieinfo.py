import os
import csv

def get_movie_info(root_dir):
    movie_info = []
    media_extensions = ["mp4", "mkv", "flv", "avi", "mpg", "mpeg", "mov", "ts", "wmv", "rm", "rmvb", "3gp", "3g2", "webm", "mp4a", "f4v"]
    index = 1
    for root, dirs, files in os.walk(root_dir):
        for dir in dirs:
            info = dir.split(' ')
            if len(info) == 3:
                title, year, tmdb_id = info[0], info[1][1:-1], info[2][1:-1]
                media_files = [(file, os.path.getsize(os.path.join(root, dir, file)) / (1024 ** 3)) for file in os.listdir(os.path.join(root, dir)) if file.split('.')[-1] in media_extensions]
                movie_info.append((index, title, year, tmdb_id, media_files, os.path.join(root, dir)))
                index += 1
    return sorted(movie_info, key=lambda x: x[3])  # 根据tmdbid排序

root_dir = 'Y:\\阿里云盘\\盘3.188.JD\\分享\\电影普'  # 已将此路径替换为你的电影文件夹的实际路径
movie_info = get_movie_info(root_dir)

# 检查是否已经有对应的CSV文件
csv_file = 'movie_info.csv'
existing_info = []
if os.path.exists(csv_file):
    # 如果有，则读取CSV文件
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        existing_info = list(reader)
else:
    # 如果没有，则创建一个新的CSV文件，并写入表头
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['序号', '标题', '年份', 'TMDB ID', '媒体文件', '容量', '电影文件夹地址'])

# 将电影信息追加到CSV文件
with open(csv_file, 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    for info in movie_info:
        for file_info in info[4]:
            row = [info[0], info[1], info[2], info[3], file_info[0], f'{file_info[1]:.2f} GB', info[5]]
            # 检查CSV文件中是否已经有相同的电影信息
            if not any(row[1:4] == existing_row[1:4] and row[5] == existing_row[5] for existing_row in existing_info):
                writer.writerow(row)
            else:
                print(f'已经存在相同大小的文件: {row[4]} ({row[5]} GB) 在电影: {row[1]}')
