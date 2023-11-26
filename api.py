# -*- coding: utf-8 -*-
# @Time : 2023/11/21
# @File : api.py

import json
import requests
from typing import Union, List, Dict, Optional
from tqdm import tqdm
from config import ConfigManager
import time
from colorama import Fore, Style

class PlexApi:
    def __init__(self, plex_url: str, plex_token: str, execute_request: bool = True):
        self.plex_url = plex_url
        self.plex_token = plex_token
        self.headers = {
            "X-Plex-Token": self.plex_token,
            "Accept": "application/json",
        }
        if execute_request:
            response = requests.get(self.plex_url, headers=self.headers)
            if response.status_code == 200:
                print(Fore.GREEN + "成功连接PLEX服务器." + Style.RESET_ALL)
            else:
                print(Fore.RED + "连接PLEX服务器失败." + Style.RESET_ALL)
        self.class_name = type(self).__name__

    def send_request(self, search_url: str) -> Optional[requests.Response]:
        """
        向指定的URL发送GET请求，并返回响应。
        如果请求失败，返回None。
        如果无法将响应内容解析为JSON，返回None。
        """
        max_attempts = 4
        for attempt in range(max_attempts):
            try:
                response = requests.get(search_url, headers=self.headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(Fore.RED + f"请求失败，错误信息：{e}" + Style.RESET_ALL)
                if attempt < max_attempts - 1:
                    wait_time = 2 ** attempt
                    print(f"等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
            else:
                break
        else:
            print(Fore.RED + "所有尝试都失败，跳过请求。" + Style.RESET_ALL)
            return None

        try:
            response_json = response.json()
        except ValueError:
            print(Fore.RED + "无法解析响应内容为JSON" + Style.RESET_ALL)
            return None

        return response

    def search_tv(self, title: str, year: Union[str, None] = None) -> Optional[Dict[str, str]]:
        """
        在PLEX服务器上搜索指定标题和年份的电视剧。
        如果标题为空，抛出ValueError。
        如果年份不是数字，抛出ValueError。
        如果找不到电视剧，返回None。
        """
        if not title:
            raise ValueError("标题不能为空")
        if year and not year.isdigit():
            raise ValueError("年份必须为数字")

        search_endpoint = f"/search?query={title}"
        search_url = self.plex_url + search_endpoint
        response = self.send_request(search_url)
        if response is None:
            return None

        shows = response.json()
        if 'Metadata' in shows['MediaContainer']:
            for show in shows['MediaContainer']['Metadata']:
                if year:
                    if show.get('title') == title and show.get('year') == int(year):
                        show_details = self.tv_info(show)
                        return show_details
                elif show.get('title') == title:
                    show_details = self.tv_info(show)
                    return show_details
        print(Fore.RED + "未发现媒体" + Style.RESET_ALL)
        return None

    def tv_info(self, show: str,  silent: bool = False) -> dict:
        """
        获取指定电视剧的详细信息。
        返回一个包含标题、年份和TMDB ID的字典。
        如果无法获取信息，返回None。
        """
        plex_endpoint = "/library/metadata/" + show['ratingKey']
        search_url = self.plex_url + plex_endpoint
        response = self.send_request(search_url)
        if response is None:
            return None

        response_json = response.json()
        show_details = {'title': None, 'year': None, 'tmdbid': None}
        for child in response_json['MediaContainer']['Metadata']:
            show_details['title'] = child.get('title')
            show_details['year'] = child.get('year')
            for guid_dict in child.get('Guid', []):
                id_value = guid_dict.get('id')
                if id_value and id_value.startswith('tmdb://'):
                    show_details['tmdbid'] = id_value.split('://')[1]
        return show_details

    def search_movie(self, title: str, year: Union[str, None] = None) -> Optional[Dict[str, str]]:
        """
        在PLEX服务器上搜索指定标题和年份的电影。
        如果标题为空，抛出ValueError。
        如果年份不是数字，抛出ValueError。
        如果找不到电影，返回None。
        """
        if not title:
            raise ValueError("标题不能为空")
        if year and not year.isdigit():
            raise ValueError("年份必须为数字")

        search_endpoint = f"/search?query={title}"
        search_url = self.plex_url + search_endpoint
        response = self.send_request(search_url)
        if response is None:
            return None

        movies = response.json()
        if 'Metadata' in movies['MediaContainer']:
            for movie in movies['MediaContainer']['Metadata']:
                if year:
                    if movie.get('title') == title and movie.get('year') == int(year):
                        details = self.movie_info(movie)
                        return details
                elif movie.get('title') == title:
                    movie_details = self.movie_info(movie)
                    return movie_details
        print(Fore.RED + "未发现媒体" + Style.RESET_ALL)
        return None

    def movie_info(self, movie: str) -> dict:
        """
        获取指定电影的详细信息。
        返回一个包含标题、年份和TMDB ID的字典。
        如果无法获取信息，返回None。
        """
        plex_endpoint = movie['key']
        search_url = self.plex_url + plex_endpoint
        response = self.send_request(search_url)
        if response is None:
            return None

        response_json = response.json()
        media_details = {}
        for child in response_json['MediaContainer']['Metadata']:
            for key, value in child.items():
                if key == 'Guid':
                    for guid_dict in value:
                        id_value = guid_dict.get('id')
                        if id_value and id_value.startswith('tmdb://'):
                            media_details['tmdbid'] = id_value.split('://')[1]
                else:
                    media_details[key] = value
        return media_details


class TMDBApi:
    def __init__(self, key: str):
        self.key = key
        self.api_url = "https://api.themoviedb.org/3"

    def send_request(self, url: str, params: Dict[str, str]) -> Optional[requests.Response]:
        """
        向指定的URL发送GET请求，并返回响应。
        如果请求失败，返回None。
        如果无法将响应内容解析为JSON，返回None。
        """
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(Fore.RED + f"请求失败，错误信息：{e}" + Style.RESET_ALL)
                if attempt < max_attempts - 1:
                    wait_time = 2 ** attempt
                    print(f"等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
            else:
                break
        else:
            print(Fore.RED + "所有尝试都失败，跳过请求。" + Style.RESET_ALL)
            return None

        try:
            response_json = response.json()
        except ValueError:
            print(Fore.RED + "无法解析响应内容为JSON" + Style.RESET_ALL)
            return None

        return response

    def search_tv(self, title: str, year: str = None, language: str = 'zh-CN', silent: bool = False) -> dict:
        """
        在TMDB上搜索指定标题和年份的电视剧。
        如果标题为空，抛出ValueError。
        如果年份不是数字，抛出ValueError。
        如果找不到电视剧，返回None。
        """
        if not title:
            raise ValueError("标题不能为空")
        if year and not year.isdigit():
            raise ValueError("年份必须为数字")

        post_url = "{0}/search/tv".format(self.api_url)
        post_params = dict(api_key=self.key, query=title, language=language)
        response = self.send_request(post_url, post_params)
        if response is None:
            return None

        return_data = response.json()
        return_data['request_code'] = response.status_code
        if silent:
            return return_data

        failure_msg = Fore.RED + '\n[剧集搜索●失败]' + Style.RESET_ALL
        success_msg = Fore.GREEN + '\n[剧集搜索●成功]' + Style.RESET_ALL
        if response.status_code != 200:
            print(f"{failure_msg} title: {title}\n{return_data['status_message']}")
            return return_data

        if len(return_data['results']) == 0:
            print(f"{failure_msg} 关键词[{title}]查找不到任何相关剧集")
            return return_data

        print(f"{success_msg} 关键词[{title}]查找结果如下: ")
        print("{:<11}{:<8}{:<10}{}".format("首播时间", "序号", "TMDB-ID", "剧 名"))
        print("{:<15}{:<10}{:<10}{}".format("----------", "-----", "-------", "----------------"))
        for i, result in enumerate(return_data['results']):
            print("{:<15}{:<10}{:<10}{}".format(result['first_air_date'], str(i + 1), result['id'], result['name']))
            if year and result['first_air_date'][:4] != year:
                continue
            return return_data

        return None

    def tv_info(self, tv_id: str, language: str = 'zh-CN', silent: bool = False) -> dict:
        """
        获取指定电视剧的详细信息。
        返回一个包含首播年份和剧名的字典。
        如果无法获取信息，返回None。
        """
        post_url = "{0}/tv/{1}".format(self.api_url, tv_id)
        post_params = dict(api_key=self.key, language=language)
        response = self.send_request(post_url, post_params)
        if response is None:
            return None

        return_data = response.json()
        return_data['request_code'] = response.status_code
        if silent:
            return return_data

        failure_msg = Fore.RED + '\n[Tv_info●失败]' + Style.RESET_ALL
        success_msg = Fore.GREEN + '\n[Tv_info●成功]' + Style.RESET_ALL
        if response.status_code != 200:
            print(f"{failure_msg} tv_id: {tv_id}\n{return_data['status_message']}")
            return return_data

        first_air_year = return_data['first_air_date'][:4]
        name = return_data['name']
        dir_name = f"{name} ({first_air_year})"
        print(f"{success_msg} {dir_name}")

        return return_data

    def tv_season_info(self,
                    tv_id: str,
                    season_number: int,
                    language: str = 'zh-CN',
                    silent: bool = False) -> dict:
        """
        获取指定电视剧季度的详细信息。
        如果无法获取信息，返回None。
        """
        post_url = "{0}/tv/{1}/season/{2}".format(self.api_url, tv_id,
                                                season_number)
        post_params = dict(api_key=self.key, language=language)
        response = self.send_request(post_url, post_params)
        if response is None:
            return None

        return_data = response.json()
        return_data['request_code'] = response.status_code
        if silent:
            return return_data

        failure_msg = Fore.RED + '\n[TvSeason●失败]' + Style.RESET_ALL
        success_msg = Fore.GREEN + '\n[TvSeason●成功]' + Style.RESET_ALL
        if response.status_code != 200:
            print(f"{failure_msg} 剧集id: {tv_id}\t第 {season_number} 季\n{return_data['status_message']}")
            return return_data

        return return_data

    def movie_info(self, movie_id: str, language: str = 'zh-CN', silent: bool = False) -> dict:
        """
        获取指定电影的详细信息。
        返回一个包含上映年份和电影标题的字典。
        如果无法获取信息，返回None。
        """
        post_url = "{0}/movie/{1}".format(self.api_url, movie_id)
        post_params = dict(api_key=self.key, language=language)
        response = self.send_request(post_url, post_params)
        if response is None:
            return None

        return_data = response.json()
        return_data['request_code'] = response.status_code
        if silent:
            return return_data

        failure_msg = Fore.RED + '\n[MovieInfo●失败]' + Style.RESET_ALL
        success_msg = Fore.GREEN + '\n[MovieInfo●成功]' + Style.RESET_ALL
        if response.status_code != 200:
            print(f"{failure_msg} movie_id: {movie_id}\n{return_data['status_message']}")
            return return_data

        release_year = return_data['release_date'][:4]
        name = return_data['title']
        dir_name = f"{name} ({release_year})"
        print(f"{success_msg} {dir_name}")

        return return_data

    def search_movie(self, title: str, year: str = None, language: str = 'zh-CN', silent: bool = False) -> dict:
        """
        在TMDB上搜索指定标题和年份的电影。
        如果标题为空，抛出ValueError。
        如果年份不是数字，抛出ValueError。
        如果找不到电影，返回None。
        """
        if not title:
            raise ValueError("标题不能为空")
        if year and not year.isdigit():
            raise ValueError("年份必须为数字")

        post_url = "{0}/search/movie".format(self.api_url)
        post_params = dict(api_key=self.key, query=title, language=language)
        response = self.send_request(post_url, post_params)
        if response is None:
            return None

        return_data = response.json()
        return_data['request_code'] = response.status_code
        if silent:
            return return_data

        failure_msg = Fore.RED + '\n[MovieSearch●失败]' + Style.RESET_ALL
        success_msg = Fore.GREEN + '\n[MovieSearch●成功]' + Style.RESET_ALL
        if response.status_code != 200:
            print(f"{failure_msg} title: {title}\n{return_data['status_message']}")
            return return_data

        if len(return_data['results']) == 0:
            print(f"{failure_msg} 关键词[{title}]查找不到任何相关电影")
            return return_data

        filtered_results = [result for result in return_data['results'] if result['release_date'][:4] == year]
        if len(filtered_results) == 0:
            print(f"{failure_msg} 关键词[{title}]查找不到任何相关电影")
            return return_data

        print(f"{success_msg} 关键词[{title}]查找结果如下: ")
        print("{:<11}{:<8}{:<10}{}".format("首播时间", "序号", "TMDB-ID", "电影标题"))
        for i, result in enumerate(filtered_results):
            print("{:<15}{:<10}{:<10}{}".format(result['release_date'], str(i + 1), str(result['id']), result['title']))

        return_data['results'] = filtered_results
        return return_data


