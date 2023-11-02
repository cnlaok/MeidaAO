
# -*- coding: utf-8 -*-

# @Time : 2023/10/30
# @File : config_utils.py



import os
import json

class ServerConfig:
    def __init__(self, config_file):
        self.config = self.read_config_file(config_file)
        self.check_and_create_file('matched_tv_folders.json')
        self.check_and_create_file('matched_movie_folders.json')
    def check_and_create_file(self, filename):
        # 检查文件是否存在，如果不存在则创建
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump([], f)
    def read_config_file(self, file_name):
        if not os.path.exists(file_name):
            config = {
                'DEFAULT': {
                    'PLEX_URL': os.getenv('PLEX_URL', '你的服务器地址'),
                    'PLEX_TOKEN': os.getenv('PLEX_TOKEN', '你的PLEX TOKEN'),
                    'TMDB_API_KEY': os.getenv('TMDB_API_KEY', '你的TMDB KEY')
                },
                # 其他配置...
            }
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(config, f)
        else:
            with open(file_name, 'r', encoding='utf-8') as f:
                config = json.load(f)
        return config

    def save_to_config(self, file_name, section, option, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][option] = value
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(self.config, f)

    def get_server_info_and_key(self):
        plex_url = self.config['DEFAULT'].get('PLEX_URL')
        plex_token = self.config['DEFAULT'].get('PLEX_TOKEN')
        tmdb_api_key = self.config['DEFAULT'].get('TMDB_API_KEY')
        return plex_url, plex_token, tmdb_api_key
