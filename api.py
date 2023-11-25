# -*- coding: utf-8 -*-
# @Time : 2023/11/21
# @File : api.py

import json
import requests
from typing import Union, List, Dict
from tqdm import tqdm
from config import ConfigManager
import time

# 定义PlexApi类
class PlexApi:
    # 初始化方法
    def __init__(self, plex_url: str, plex_token: str, execute_request: bool = True):
        self.plex_url = plex_url  # Plex服务器的URL
        self.plex_token = plex_token  # 用于访问Plex服务器的令牌
        self.headers = {  # 请求头信息
            "X-Plex-Token": self.plex_token,
            "Accept": "application/json",
        }
        if execute_request:  # 如果execute_request为True，则尝试连接到Plex服务器
            response = requests.get(self.plex_url, headers=self.headers)
            if response.status_code == 200:
                print("成功连接PLEX服务器.")
            else:
                print("连接PLEX服务器失败.")
        self.class_name = type(self).__name__  # 获取当前类的名称

    def send_request(self, search_url: str) -> Union[requests.Response, None]:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = requests.get(search_url, headers=self.headers)
                # 如果状态码不是200，将引发一个异常
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"请求失败，错误信息：{e}")
                if attempt < max_attempts - 1:  # 如果不是最后一次尝试，等待一段时间再重试
                    wait_time = 2 ** attempt  # 指数退避策略
                    print(f"等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
            else:
                break  # 如果请求成功，跳出循环
        else:
            print("所有尝试都失败，跳过请求。")
            return None

        return response

    # 搜索节目的方法
    def search_tv(self, title: str, year: Union[str, None] = None) -> Union[Dict[str, str], None]:
        search_endpoint = f"/search?query={title}"
        search_url = self.plex_url + search_endpoint
        response = self.send_request(search_url)
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
        print("\033[91m未发现媒体\033[0m")
        return None

    # 获取节目详情的方法
    def tv_info(self, show: str,  silent: bool = False) -> dict:
        plex_endpoint = "/library/metadata/" + show['ratingKey']  # 构造端点
        search_url = self.plex_url + plex_endpoint  # 构造URL
        response = self.send_request(search_url)  # 发送GET请求
        response_json = response.json()  # 获取JSON响应
        show_details = {'title': None, 'year': None, 'tmdbid': None}  # 初始化节目详情字典
        for child in response_json['MediaContainer']['Metadata']:  # 遍历'Metadata'
            show_details['title'] = child.get('title')  # 获取并设置标题
            show_details['year'] = child.get('year')  # 获取并设置年份
            for guid_dict in child.get('Guid', []):  # 遍历'Guid'
                id_value = guid_dict.get('id')  # 获取id值
                if id_value and id_value.startswith('tmdb://'):  # 如果id值存在且以'tmdb://'开头
                    show_details['tmdbid'] = id_value.split('://')[1]  # 获取并设置tmdbid
        return show_details  # 返回节目详情

    # 搜索电影的方法
    def search_movie(self, title: str, year: Union[str, None] = None) -> Union[Dict[str, str], None]:
        search_endpoint = f"/search?query={title}"  # 构造搜索端点
        search_url = self.plex_url + search_endpoint  # 构造搜索URL
        response = self.send_request(search_url)  # 发送GET请求
        movies = response.json()  # 获取JSON响应
        if 'Metadata' in movies['MediaContainer']:  # 如果'Metadata'在'MediaContainer'中
            for movie in movies['MediaContainer']['Metadata']:  # 遍历'Metadata'
                if year:  # 如果提供了年份
                    if movie.get('title') == title and movie.get('year') == int(year):  # 如果标题和年份匹配
                        details = self.movie_info(movie)  # 获取电影详情
                        return details  # 返回电影详情
                elif movie.get('title') == title:  # 如果只提供了标题
                    movie_details = self.movie_info(movie)  # 获取电影详情
                    return movie_details  # 返回电影详情
        print("\033[91m未发现媒体\033[0m")  # 如果没有找到匹配的电影，打印消息
        return None  # 返回None

    # 获取电影详情的方法
    def movie_info(self, movie: str) -> dict:
        plex_endpoint = movie['key']  # 构造端点
        search_url = self.plex_url + plex_endpoint  # 构造URL
        response = self.send_request(search_url)  # 发送GET请求
        response_json = response.json()  # 获取JSON响应
        media_details = {}  # 初始化媒体详情字典
        for child in response_json['MediaContainer']['Metadata']:  # 遍历'Metadata'
            for key, value in child.items():  # 遍历子项
                if key == 'Guid':  # 如果键是'Guid'
                    for guid_dict in value:  # 遍历'Guid'
                        id_value = guid_dict.get('id')  # 获取id值
                        if id_value and id_value.startswith('tmdb://'):  # 如果id值存在且以'tmdb://'开头
                            media_details['tmdbid'] = id_value.split('://')[1]  # 获取并设置tmdbid
                else:
                    media_details[key] = value  # 获取并设置其他键值
        return media_details  # 返回媒体详情


# 定义TMDBApi类
class TMDBApi:
    """
    调用TMDB api获取剧集相关信息
    \nTMDB api官方说明文档(https://developers.themoviedb.org/3)
    """

    # 初始化方法，设置API密钥和URL
    def __init__(self, key: str):
        """
        初始化参数

        :param key: TMDB Api Key(V3)
        """
        self.key = key  # TMDB Api Key(V3)
        self.api_url = "https://api.themoviedb.org/3"  # TMDB API的URL

    # 发送请求并处理重试
    def send_request(self, url: str, params: Dict[str, str]) -> Union[requests.Response, None]:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, params=params)
                # 如果状态码不是200，将引发一个异常
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"请求失败，错误信息：{e}")
                if attempt < max_attempts - 1:  # 如果不是最后一次尝试，等待一段时间再重试
                    wait_time = 2 ** attempt  # 指数退避策略
                    print(f"等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
            else:
                break  # 如果请求成功，跳出循环
        else:
            print("所有尝试都失败，跳过请求。")
            return None

        return response

    # 根据关键字匹配剧集, 获取相关信息
    def search_tv(self, title: str, year: str = None, language: str = 'zh-CN', silent: bool = False) -> dict:
        # 构造请求URL和参数
        post_url = "{0}/search/tv".format(self.api_url)  # 构造请求URL
        post_params = dict(api_key=self.key, query=title, language=language)  # 构造请求参数

        # 使用send_request方法发送GET请求并获取响应
        response = self.send_request(post_url, post_params)

        if response is None:
            print("所有尝试都失败，跳过请求。")
            return None

        # 将响应转换为JSON格式，并添加状态码到返回数据中
        return_data = response.json()  # 获取JSON格式的响应
        return_data['request_code'] = response.status_code  # 添加状态码到返回数据中

        # 如果silent为True，则直接返回数据，否则打印请求结果
        if silent:
            return return_data

        # 设置成功和失败消息的颜色
        failure_msg = '\033[31m' + '\n[TvSearch●Failure]' + '\033[0m'
        success_msg = '\033[32m' + '\n[TvSearch●Success]' + '\033[0m'

        # 如果请求失败，则打印失败消息并返回数据
        if response.status_code != 200:
            print(f"{failure_msg} title: {title}\n{return_data['status_message']}")
            return return_data

        # 如果没有搜索结果，则打印失败消息并返回数据
        if len(return_data['results']) == 0:
            print(f"{failure_msg} 关键词[{title}]查找不到任何相关剧集")
            return return_data

        # 格式化并打印搜索结果
        print(f"{success_msg} 关键词[{title}]查找结果如下: ")
        print("{:<11}{:<8}{:<10}{}".format("首播时间", "序号", "TMDB-ID", "剧 名"))
        print("{:<15}{:<10}{:<10}{}".format("----------", "-----", "-------", "----------------"))

        # 在返回结果中查找匹配的电视剧
        for i, result in enumerate(return_data['results']):
            print("{:<15}{:<10}{:<10}{}".format(result['first_air_date'], i, result['id'], result['name']))
            # 如果提供了年份，检查年份是否匹配
            if year and result['first_air_date'][:4] != year:
                continue
            # 如果标题匹配（并且如果提供了年份，年份也匹配），则返回结果
            return return_data

        # 如果没有找到匹配的结果，返回None
        return None


    # 根据提供的id获取剧集信息
    def tv_info(self, tv_id: str, language: str = 'zh-CN', silent: bool = False) -> dict:
        """
        根据提供的id获取剧集信息.
        :param tv_id: 剧集id
        :param language: TMDB搜索语言
        :param silent: 静默返回请求结果, 不输出内容
        :return: 请求状态码与剧集信息请求结果
        """
        # 构造请求URL和参数
        post_url = "{0}/tv/{1}".format(self.api_url, tv_id)  # 构造请求URL
        post_params = dict(api_key=self.key, language=language)  # 构造请求参数

        # 使用send_request方法发送GET请求并获取响应
        response = self.send_request(post_url, post_params)

        if response is None:
            print("所有尝试都失败，跳过请求。")
            return None

        # 将响应转换为JSON格式，并添加状态码到返回数据中
        return_data = response.json()  # 获取JSON格式的响应
        return_data['request_code'] = response.status_code  # 添加状态码到返回数据中

        # 如果silent为True，则直接返回数据，否则打印请求结果
        if silent:
            return return_data

        # 设置成功和失败消息的颜色
        failure_msg = '\033[31m' + '\n[TvInfo●Failure]' + '\033[0m'
        success_msg = '\033[32m' + '\n[TvInfo●Success]' + '\033[0m'

        # 如果请求失败，则打印失败消息并返回数据
        if response.status_code != 200:
            print(f"{failure_msg} tv_id: {tv_id}\n{return_data['status_message']}")
            return return_data

        # 格式化并打印请求结果
        first_air_year = return_data['first_air_date'][:4]
        name = return_data['name']
        dir_name = f"{name} ({first_air_year})"
        print(f"{success_msg} {dir_name}")

        # 返回请求结果
        return return_data


    # 获取指定季度剧集信息
    def tv_season_info(self,
                    tv_id: str,
                    season_number: int,
                    language: str = 'zh-CN',
                    silent: bool = False) -> dict:
        """
        获取指定季度剧集信息.
        :param tv_id: 剧集id
        :param season_number: 指定第几季
        :param language: TMDB搜索语言
        :param silent: 静默返回请求结果,不输出内容
        :return: 返回获取指定季度剧集信息结果
        """
        # 构造请求URL和参数
        post_url = "{0}/tv/{1}/season/{2}".format(self.api_url, tv_id,
                                                season_number)  # 构造请求URL
        post_params = dict(api_key=self.key, language=language)  # 构造请求参数

        # 使用send_request方法发送GET请求并获取响应
        response = self.send_request(post_url, post_params)

        if response is None:
            print("所有尝试都失败，跳过请求。")
            return None

        # 将响应转换为JSON格式，并添加状态码到返回数据中
        return_data = response.json()  # 获取JSON格式的响应
        return_data['request_code'] = response.status_code  # 添加状态码到返回数据中

        # 如果silent为True，则直接返回数据，否则打印请求结果
        if silent:
            return return_data

        # 设置成功和失败消息的颜色
        failure_msg = '\033[31m' + '\n[TvSeason●Failure]' + '\033[0m'
        success_msg = '\033[32m' + '\n[TvSeason●Success]' + '\033[0m'

        # 如果请求失败，则打印失败消息并返回数据
        if response.status_code != 200:
            print(f"{failure_msg} 剧集id: {tv_id}\t第 {season_number} 季\n{return_data['status_message']}")
            return return_data

        # 返回请求结果
        return return_data

        
    # 根据提供的id获取电影信息
    def movie_info(self, movie_id: str, language: str = 'zh-CN', silent: bool = False) -> dict:
        """
        根据提供的id获取电影信息.
        :param movie_id: 电影id
        :param language: TMDB搜索语言
        :param silent: 静默返回请求结果, 不输出内容
        :return: 请求状态码与电影信息请求结果
        """
        # 构造请求URL和参数
        post_url = "{0}/movie/{1}".format(self.api_url, movie_id)  # 构造请求URL
        post_params = dict(api_key=self.key, language=language)  # 构造请求参数

        # 使用send_request方法发送GET请求并获取响应
        response = self.send_request(post_url, post_params)

        if response is None:
            print("所有尝试都失败，跳过请求。")
            return None

        # 将响应转换为JSON格式，并添加状态码到返回数据中
        return_data = response.json()  # 获取JSON格式的响应
        return_data['request_code'] = response.status_code  # 添加状态码到返回数据中

        # 如果silent为True，则直接返回数据，否则打印请求结果
        if silent:
            return return_data

        # 设置成功和失败消息的颜色
        failure_msg = '\033[31m' + '\n[MovieInfo●Failure]' + '\033[0m'
        success_msg = '\033[32m' + '\n[MovieInfo●Success]' + '\033[0m'

        # 如果请求失败，则打印失败消息并返回数据
        if response.status_code != 200:
            print(f"{failure_msg} movie_id: {movie_id}\n{return_data['status_message']}")
            return return_data

        # 格式化并打印请求结果
        release_year = return_data['release_date'][:4]
        name = return_data['title']
        dir_name = f"{name} ({release_year})"
        print(f"{success_msg} {dir_name}")

        # 返回请求结果
        return return_data


    # 根据关键字匹配电影, 获取相关信息
    def search_movie(self, title: str, year: str = None, language: str = 'zh-CN', silent: bool = False) -> dict:
        # 构造请求URL和参数
        post_url = "{0}/search/movie".format(self.api_url)  # 构造请求URL
        post_params = dict(api_key=self.key, query=title, language=language)  # 构造请求参数

        # 使用send_request方法发送GET请求并获取响应
        response = self.send_request(post_url, post_params)

        if response is None:
            print("所有尝试都失败，跳过请求。")
            return None

        # 将响应转换为JSON格式，并添加状态码到返回数据中
        return_data = response.json()  # 获取JSON格式的响应
        return_data['request_code'] = response.status_code  # 添加状态码到返回数据中

        if silent:
            return return_data

        # 设置成功和失败消息的颜色
        failure_msg = '\033[31m' + '\n[MovieSearch●Failure]' + '\033[0m'
        success_msg = '\033[32m' + '\n[MovieSearch●Success]' + '\033[0m'

        if response.status_code != 200:
            print(f"{failure_msg} title: {title}\n{return_data['status_message']}")
            return return_data

        if len(return_data['results']) == 0:
            print(f"{failure_msg} 关键词[{title}]查找不到任何相关电影")
            return return_data

        print(f"{success_msg} 关键词[{title}]查找结果如下: ")
        print("{:<11}{:<8}{:<10}{}".format("首播时间", "序号", "TMDB-ID", "电影标题"))
        
        # 在返回结果中查找匹配的电影
        for i, result in enumerate(return_data['results']):
            print("{:<15}{:<10}{:<10}{}".format(result['release_date'], str(i + 1), str(result['id']), result['title']))
            # 如果提供了年份，检查年份是否匹配
            if year and result['release_date'][:4] != year:
                continue
            # 如果年份匹配，则返回结果
            return return_data

        # 如果没有找到匹配的结果，返回None
        return None


