# -*- coding: utf-8 -*-
# @Time : 2023/11/03
# @File : config.py

import os
import json
from typing import Dict


class ConfigManager:
    def __init__(self, config_file: str):
        self.config_file: str = config_file
        self.config: Dict[str, str] = {}
        self.plex_url: str = None
        self.plex_token: str = None
        self.tmdb_api_key: str = None
        self.load_config()

    def load_config(self) -> None:
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        self.check_config()

    def check_config(self) -> None:
        keys = ['PLEX_URL', 'PLEX_TOKEN', 'TMDB_API_KEY']
        for key in keys:
            if key not in self.config or not self.config[key]:
                self.config[key] = input(f"请输入{key}：")
            if key == 'PLEX_URL':
                self.plex_url = self.config[key]
            elif key == 'PLEX_TOKEN':
                self.plex_token = self.config[key]
            elif key == 'TMDB_API_KEY':
                self.tmdb_api_key = self.config[key]
        self.save_config()

    def save_config(self) -> None:
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def get_server_info_and_key(self) -> Dict[str, str]:
        return {
            'plex_url': self.plex_url,
            'plex_token': self.plex_token,
            'tmdb_api_key': self.tmdb_api_key
        }
