# -*- coding: utf-8 -*-
# @Time : 2023/11/03
# @File : api.py

import requests
from xml.etree import ElementTree
from typing import List, Dict
from tqdm import tqdm
from logger import LoggerManager
from config import ConfigManager

logger_manager = LoggerManager()
logger = logger_manager.logger   
handler_to_remove = logger.handlers[0] 
logger.removeHandler(handler_to_remove)

class PlexApi:
    def __init__(self, plex_url, plex_token, execute_request=True):  # 添加一个新的参数
        self.plex_url = plex_url  
        self.plex_token = {"X-Plex-Token": plex_token}  
        if execute_request:  # 检查是否需要执行请求
            response = requests.get(self.plex_url, headers=self.plex_token)
            if response.status_code == 200:
                logger.info("Successfully connected to the Plex server.")
            else:
                logger.info("Failed to connect to the Plex server.")
        self.class_name = type(self).__name__
        logger.info(f"{self.class_name} initialised")

        """
        初始化PlexApi类的实例。
        :param plex_url: Plex服务器的URL。
        :param plex_token: 用于访问Plex服务器的令牌。
        :param execute_request: 是否在初始化时执行请求以测试连接。
        """
   
    def get_keys_from_plex_api(self, plex_endpoint: str) -> List[Dict]:
        """
        从Plex API获取关键信息。
        :param plex_endpoint: Plex API的端点。
        :return: 包含所有提取信息的列表。
        """
        api_url = self.plex_url + plex_endpoint
        response = requests.get(url=api_url, params=self.plex_token)
        plex_keys = self.extract_keys_from_xml(response_content=response.content)
        return plex_keys
    
    @staticmethod
    def extract_keys_from_xml(response_content: bytes) -> List[Dict]:
        """
        从XML响应内容中提取关键信息。
        :param response_content: XML响应内容，为字节字符串。
        :return: 包含所有提取信息的列表。
        """
        all_contents = []
        response_xml_root = ElementTree.fromstring(response_content)
        for child in response_xml_root:
            content_details = {}
            for attr, value in child.attrib.items():
                content_details[attr] = value
            all_contents.append(content_details)
        return all_contents
        
    def search_movie(self, title):
        """
        搜索电影。
        :param title: 电影的标题。
        :return: 如果找到匹配的电影，则返回电影的详细信息，否则返回None。
        """    
        # 构造搜索电影的API请求
        search_endpoint = f"/search?query={title}"
        search_url = self.plex_url + search_endpoint

        # 发送请求并获取响应
        response = requests.get(search_url, headers=self.plex_token)
        movies = self.extract_keys_from_xml(response.content)

        # 在响应中查找与提供的年份匹配的电影
        for movie in movies:
            # 打印出每个电影的键
            details = self.get_movie_details(movie)
            # 打印详细信息
            logger.debug("此处获取的信息是：", details)
            return details

        # 如果没有找到匹配的电影，返回None
        return None


    def search_show(self, title, year=None):
        """
        搜索电视节目。
        :param title: 电视节目的标题。
        :param year: 电视节目的年份。如果没有提供，将只根据标题来匹配电视节目。
        :return: 如果找到匹配的电视节目，则返回电视节目的详细信息，否则返回None。
        """
        # 构造搜索电视节目的API请求
        search_endpoint = f"/search?query={title}"
        search_url = self.plex_url + search_endpoint

        # 发送请求并获取响应
        response = requests.get(search_url, headers=self.plex_token)
        shows = self.extract_keys_from_xml(response.content)

        # 在响应中查找与提供的标题和年份（如果有）匹配的电视节目
        for show in shows:
            if year is None or ('year' in show and show['year'] == year):
                # 获取该电视节目的key
                # 打印该电视节目的标题和年份
                logger.debug(f"Found show: {show['title']} ({show['year']})")
                # 调用get_show_details函数根据key获取电视节目的详细信息
                show_details = self.get_show_details(show)
                # 返回电视节目的详细信息
                return show_details

        # 如果没有找到匹配的电视节目，返回None
        return None


    def get_show_details(self, show: str) -> Dict:
        """
        获取特定剧集的详细信息。
        :param show_key: API的端点。
        :return: 包含特定剧集详细信息的字典。
        """
        # 构造获取特定剧集的API请求的URL
        plex_endpoint = "/library/metadata/" + show['ratingKey']
        api_url = self.plex_url + plex_endpoint
        logger.debug(f"Constructed URL: {api_url}")  # 打印构造的链接
        
        # 发送请求并获取响应
        response = requests.get(url=api_url, params=self.plex_token)
        
        # 解析XML响应内容
        response_xml_root = ElementTree.fromstring(response.content)
        
        # 初始化一个空字典来存储电视节目的详细信息
        show_details = {'title': None, 'year': None, 'tmdbid': None}
        # 从XML响应内容中提取电视节目的标题，年份，tmdbid和key
        for child in response_xml_root.iter('Directory'):
            show_details['title'] = child.attrib.get('title')
            show_details['year'] = child.attrib.get('year')

        for guid in response_xml_root.iter('Guid'):
            id_value = guid.attrib.get('id')
            if id_value and id_value.startswith('tmdb://'):
                show_details['tmdbid'] = id_value.split('://')[1]

        # 打印获取到的电视节目的详细信息
        logger.debug(f"Got show details: {show_details}")  # 打印输出
        # 返回电视节目的详细信息
        return show_details



    def get_movie_details(self, movie):
        """
        获取电影的详细信息。
        :param movie: 电影对象。
        :return: 包含电影详细信息的字典。
        """
        plex_endpoint = movie['key']
        api_url = self.plex_url + plex_endpoint
        response = requests.get(url=api_url, params=self.plex_token)
        logger.debug(f"Constructed URL: {api_url}")  # 打印构造的链接
        response_xml_root = ElementTree.fromstring(response.content)
        
        media_details = {}
        for child in response_xml_root:
            for attr, value in child.attrib.items():
                media_details[attr] = value
        
        # 提取tmdbid中的数字部分
        for guid in response_xml_root.iter('Guid'):
            id_value = guid.attrib.get('id')
            if id_value and id_value.startswith('tmdb://'):
                media_details['tmdbid'] = id_value.split('://')[1]

        # 打印获取到的所有信息
        logger.debug("此处获取的所有信息是：", media_details)
        
        return media_details
    
    def get_all_episode_details(self, endpoint: str) -> List[Dict]:
        """
        获取所有剧集的详细信息。
        :param endpoint: API的端点。
        :return: 包含所有剧集详细信息的列表。
        """

        print(f"Getting all episode details for endpoint: {endpoint}")  # 打印输入
        api_url = self.plex_url + endpoint
        response = requests.get(url=api_url, params=self.plex_token)
        
        response_xml_root = ElementTree.fromstring(response.content)
        
        all_episodes = []
        for child in response_xml_root:
            if child.attrib.get("type") == "episode":

                episode_details = {
                    "title"    : child.attrib.get("title"),
                    "type"     : child.attrib.get("type"),
                    "updatedAt": child.attrib.get("updatedAt"),
                    "addedAt"  : child.attrib.get("addedAt"),
                    "year"     : child.attrib.get("year"),
                    "key"      : child.attrib.get("key")
                }

                # 提取tmdbid中的数字部分
                tmdbids = []
                for guid_child in child.iter("Guid"):
                    guid_id = guid_child.attrib.get("id")
                    if 'tmdb://' in guid_id:
                        tmdbid = guid_id.split('://')[1]
                        tmdbids.append(tmdbid)
                episode_details["tmdbids"] = tmdbids

                all_episodes.append(episode_details)
        print(f"Got all episode details: {all_episodes}")  # 打印输出
        return all_episodes


    
    def update_all_library_sections(self) -> bool:
        """
        刷新Plex服务器上的所有库区域。
        :return: 如果刷新成功，则返回True，否则返回False。
        """
        # Sections
        logger.info("Getting library sections")
        library_sections = self.get_keys_from_plex_api(plex_endpoint="/library/sections")
        for section in library_sections:
            section_endpoint = f"/library/sections/{section['key']}/refresh"
            api_uri = self.plex_url + section_endpoint
            response = requests.get(api_uri, params=self.plex_token)
            if response.status_code == 200:
                logger.success(f"Successfully started refresh for {section['title']}")
            else:
                raise ConnectionError(f"Refresh failed for {section['title']}")
        return True
    
    def get_all_show_details(self, show_endpoint: str) -> Dict:
        """
        获取所有电视节目的详细信息。
        :param show_endpoint: API的端点。
        :return: 包含所有电视节目详细信息的字典。
        """
        api_url = self.plex_url + show_endpoint
        response = requests.get(url=api_url, params=self.plex_token)
        print(f"Constructed URL: {api_url}")  # 打印构造的链接
        response_xml_root = ElementTree.fromstring(response.content)
        show_details = {
            "show_summary": response_xml_root.attrib.get("summary"),
            "show_title1" : response_xml_root.attrib.get("title2"),
            "show_title2" : response_xml_root.attrib.get("title1"),
            "year"        : response_xml_root.attrib.get("parentYear"),
            "key"         : show_endpoint
        }
        all_season_details = []
        all_episode_details = []
        for child in response_xml_root:
            if child.attrib.get("type") == "season":

                season_details = {
                    "title"    : child.attrib.get("title"),
                    "type"     : child.attrib.get("type"),
                    "updatedAt": child.attrib.get("updatedAt"),
                    "addedAt"  : child.attrib.get("addedAt"),
                    "key"      : child.attrib.get("key")
                }

                all_season_details.append(season_details)

                episodes_endpoint = child.attrib.get("key")
                all_episode_details.append(self.get_all_episode_details(endpoint=episodes_endpoint))
            # 新增一个功能，从XML响应内容中提取电视节目的tmdbid
            if child.attrib.get("type") == "show":
                for guid in child.iter("Guid"):
                    id_value = guid.attrib.get("id")
                    if id_value and id_value.startswith("tmdb://"):
                        show_details["tmdbid"] = id_value.split("://")[1]
        show_details["season_details"] = all_season_details
        show_details["episode_details"] = all_episode_details
        return show_details

    def get_section_contents(self, content: Dict) -> Dict:
        """
        获取库区域的内容。
        :param content: 内容对象。
        :return: 包含库区域内容的字典。
        """
        content_key = content.get("key")
        content_type = content.get("type")
        if content_type == "movie":
            return self.get_movie_details(content_key)
        elif content_type == "show":
            return self.get_all_show_details(content_key)

    def get_plex_section_content(self, library_section_name: str):
        """
        获取Plex库区域的内容。
        :param library_section_name: 库区域的名称。
        :return: 包含库区域内容的字典。
        """
        library_section = [section for section in self.get_keys_from_plex_api(plex_endpoint="/library/sections") if
                           section['title'] == library_section_name]

        if len(library_section) > 0:
            section_details = library_section[0]
        else:
            logger.error(f"No results found for section {library_section_name}")
            return

        section_endpoint = f"/library/sections/{section_details['key']}/all"
        section_contents = self.get_keys_from_plex_api(section_endpoint)

        return [self.get_section_contents(section_contents[i]) for i in tqdm(range(len(section_contents)))]

    def get_movie_info(self):
        """
        获取电影信息。
        :return: 包含电影信息的字典。
        """
        logger.info("Getting movie info")
        return self.get_plex_section_content("Movies")

    def get_show_info(self):
        """
        获取电视节目信息。
        :return: 包含电视节目信息的字典。
        """
        logger.info("Getting show info")
        return self.get_plex_section_content("TV Shows")

    def get_all_plex_info(self) -> (Dict):
        """
        获取所有Plex信息。
        :return: 包含所有Plex信息的字典。
        """
        
        # Sections
        
        logger.info("Getting library sections")

        all_data = {}

        all_data["movies"] = self.get_movie_info()
        all_data["shows"] = self.get_show_info()

        return all_data

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
        self.key = key
        self.api_url = "https://api.themoviedb.org/3"

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
        post_url = "{0}/tv/{1}".format(self.api_url, tv_id)
        post_params = dict(api_key=self.key, language=language)

        # 发送GET请求并获取响应
        r = requests.get(post_url, params=post_params)

        # 将响应转换为JSON格式，并添加状态码到返回数据中
        return_data = r.json()
        return_data['request_code'] = r.status_code

        # 如果silent为True，则直接返回数据，否则打印请求结果
        if silent:
            return return_data

        # 设置成功和失败消息的颜色
        failure_msg = '\033[31m' + '\n[TvInfo●Failure]' + '\033[0m'
        success_msg = '\033[32m' + '\n[TvInfo●Success]' + '\033[0m'

        # 如果请求失败，则打印失败消息并返回数据
        if r.status_code != 200:
            print(f"{failure_msg} tv_id: {tv_id}\n{return_data['status_message']}")
            return return_data

        # 格式化并打印请求结果
        first_air_year = return_data['first_air_date'][:4]
        name = return_data['name']
        dir_name = f"{name} ({first_air_year})"
        print(f"{success_msg} {dir_name}")

        # 返回请求结果
        return return_data

    # 根据关键字匹配剧集, 获取相关信息
    def search_tv(self, keyword: str, language: str = 'zh-CN', silent: bool = False) -> dict:
            """
            根据关键字匹配剧集, 获取相关信息.

            :param keyword: 剧集搜索关键词
            :param language:
            :param silent: 静默返回请求结果,不输出内容
            :return: 匹配剧集信息请求结果
            """
            # 构造请求URL和参数
            post_url = "{0}/search/tv".format(self.api_url)
            post_params = dict(api_key=self.key, query=keyword, language=language)

            # 发送GET请求并获取响应
            r = requests.get(post_url, params=post_params)

            # 将响应转换为JSON格式，并添加状态码到返回数据中
            return_data = r.json()
            return_data['request_code'] = r.status_code

            # 如果silent为True，则直接返回数据，否则打印请求结果
            if silent:
                return return_data

            # 设置成功和失败消息的颜色
            failure_msg = '\033[31m' + '\n[TvSearch●Failure]' + '\033[0m'
            success_msg = '\033[32m' + '\n[TvSearch●Success]' + '\033[0m'

            # 如果请求失败，则打印失败消息并返回数据
            if r.status_code != 200:
                print(f"{failure_msg} Keyword: {keyword}\n{return_data['status_message']}")
                return return_data

            # 如果没有搜索结果，则打印失败消息并返回数据
            if len(return_data['results']) == 0:
                print(f"{failure_msg} 关键词[{keyword}]查找不到任何相关剧集")
                return return_data

            # 格式化并打印搜索结果
            print(f"{success_msg} 关键词[{keyword}]查找结果如下: ")
            print("{:<8}{:^14}{}".format(" 首播时间 ", "序号", "剧 名"))
            print("{:<12}{:^16}{}".format("----------", "-----", "----------------"))

            for i, result in enumerate(return_data['results']):
                print("{:<12}{:^16}{}".format(result['first_air_date'], i, result['name']))

            # 返回搜索结果
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
                                                  season_number)
        post_params = dict(api_key=self.key, language=language)

        # 发送GET请求并获取响应
        r = requests.get(post_url, params=post_params)

        # 将响应转换为JSON格式，并添加状态码到返回数据中
        return_data = r.json()
        return_data['request_code'] = r.status_code

        # 如果silent为True，则直接返回数据，否则打印请求结果
        if silent:
            return return_data

        # 设置成功和失败消息的颜色
        failure_msg = '\033[31m' + '\n[TvSeason●Failure]' + '\033[0m'
        success_msg = '\033[32m' + '\n[TvSeason●Success]' + '\033[0m'

        # 如果请求失败，则打印失败消息并返回数据
        if r.status_code != 200:
            print(f"{failure_msg} 剧集id: {tv_id}\t第 {season_number} 季\n{return_data['status_message']}")
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
        post_url = "{0}/movie/{1}".format(self.api_url, movie_id)
        post_params = dict(api_key=self.key, language=language)

        # 发送GET请求并获取响应
        r = requests.get(post_url, params=post_params)

        # 将响应转换为JSON格式，并添加状态码到返回数据中
        return_data = r.json()
        return_data['request_code'] = r.status_code

        # 如果silent为True，则直接返回数据，否则打印请求结果
        if silent:
            return return_data

        # 设置成功和失败消息的颜色
        failure_msg = '\033[31m' + '\n[MovieInfo●Failure]' + '\033[0m'
        success_msg = '\033[32m' + '\n[MovieInfo●Success]' + '\033[0m'

        # 如果请求失败，则打印失败消息并返回数据
        if r.status_code != 200:
             print(f"{failure_msg} movie_id: {movie_id}\n{return_data['status_message']}")
             return return_data

        # 格式化并打印请求结果
        release_year = return_data['release_date'][:4]
        name = return_data['title']
        dir_name = f"{name} ({release_year})"
        print(f"{success_msg} {dir_name}")

        # 返回请求结果
        return return_data

    # 根据关键字匹配电影, 获取相关信息.
    def search_movie(self, keyword: str, language: str = 'zh-CN', silent: bool = False) -> dict:
        """
        根据关键字匹配电影, 获取相关信息.

        :param keyword: 电影搜索关键词
        :param language: TMDB搜索语言
        :param silent: 静默返回请求结果,不输出内容
        :return: 匹配电影信息请求结果
        """
        # 构造请求URL和参数
        post_url = "{0}/search/movie".format(self.api_url)
        post_params = dict(api_key=self.key, query=keyword, language=language)

        # 发送GET请求并获取响应
        r = requests.get(post_url, params=post_params)

        # 将响应转换为JSON格式，并添加状态码到返回数据中
        return_data = r.json()
        return_data['request_code'] = r.status_code

        # 如果silent为True，则直接返回数据，否则打印请求结果
        if silent:
            return return_data

        # 设置成功和失败消息的颜色
        failure_msg = '\033[31m' + '\n[MovieSearch●Failure]' + '\033[0m'
        success_msg = '\033[32m' + '\n[MovieSearch●Success]' + '\033[0m'

        # 如果请求失败，则打印失败消息并返回数据
        if r.status_code != 200:
            print(f"{failure_msg} Keyword: {keyword}\n{return_data['status_message']}")
            return return_data

        # 如果没有搜索结果，则打印失败消息并返回数据
        if len(return_data['results']) == 0:
            print(f"{failure_msg} 关键词[{keyword}]查找不到任何相关电影")
            return return_data

        # 格式化并打印搜索结果
        print(f"{success_msg} 关键词[{keyword}]查找结果如下: ")
        print("{:<8}{:^14}{}".format(" 首播时间 ", "序号", "电影标题"))
        print("{:<12}{:^16}{}".format("----------", "-----", "----------------"))

        for i, result in enumerate(return_data['results']):
            print("{:<12}{:^16}{}".format(result['release_date'], i, result['title']))

        # 返回搜索结果
        return return_data