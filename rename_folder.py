# -*- coding: utf-8 -*-
# @Time : 2023/11/21
# @File : rename_folder.py

from typing import Tuple, Union, List, Dict
from media_renamer import MediaRenamer
from config import ConfigManager
from api import TMDBApi, PlexApi

CONFIG_FILE = 'config.json'


def main() -> None:
    config_manager: ConfigManager = ConfigManager(CONFIG_FILE)
    server_info_and_key: dict = config_manager.get_server_info_and_key()
    tmdb_api: TMDBApi = TMDBApi(server_info_and_key['tmdb_api_key'])
    plex_api: PlexApi = PlexApi(server_info_and_key['plex_url'], server_info_and_key['plex_token'], execute_request=False)
    media_renamer: MediaRenamer = MediaRenamer(config_manager, tmdb_api, plex_api)
    print('Starting program')

    match_mode_index: int
    library_type_index: int
    naming_rule_index: int
    parent_folder_path: str
    match_mode_index, library_type_index, naming_rule_index, parent_folder_path = media_renamer.get_user_input()

    if match_mode_index not in [1, 2, 3, 4]:
        print("Invalid match mode. Please enter a number between 1 and 4.")
        return
    else:
        print("Invalid match mode. Please enter a number between 1 and 4.")
    if library_type_index not in [1, 2]:
        print("Invalid library type. Please enter either 1 or 2.")
        return

    if naming_rule_index not in [1, 2, 3]:
        print("Invalid naming rule. Please enter a number between 1 and 3.")
        return

    if match_mode_index == 4:
        media_renamer.match_mode_4(parent_folder_path)
        exit()

    if match_mode_index == 1:
        media_renamer.match_mode_1(parent_folder_path, library_type_index, naming_rule_index, config_manager)
    elif match_mode_index == 2:
        media_renamer.match_mode_2(parent_folder_path, library_type_index, naming_rule_index, config_manager)
    elif match_mode_index == 3:
        media_renamer.match_mode_3(parent_folder_path, naming_rule_index)


if __name__ == "__main__":
    main()
