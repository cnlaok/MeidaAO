# 导入requests库，用于发送HTTP请求
import requests

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
