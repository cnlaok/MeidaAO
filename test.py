import os
import time
import json
from api import TMDBApi
import colorama
import re
class LocalMediaRename:
    def __init__(self, tmdb_key: str, debug: bool = True):
        self.tmdb = TMDBApi(tmdb_key)
        self.debug = debug
        # ----Settings Start----
        # TMDB 搜索语言
        self.tmdb_language = "zh-CN"
        # 文件重命名格式
        self.tv_name_format = "{name}-S{season:0>2}E{episode:0>2}.{title}"
        # 是否重命名父文件夹名称
        self.media_folder_rename = False
        # 是否创建对应季文件夹，并将剧集文件移动到其中
        self.tv_season_dir = False
        # 季度文件夹命名格式
        self.tv_season_format = "Season {season}"
        # 需要识别的视频及字幕格式
        self.video_suffix_list = ['mp4', 'mkv', 'flv', 'avi', 'mpg', 'mpeg', 'mov']
        self.subtitle_suffix_list = ['srt', 'ass', 'stl']
        # ------Settings End------

    def rename_files(self, root_folder_path: str):
        for folder_name in os.listdir(root_folder_path):
            folder_path = os.path.join(root_folder_path, folder_name)
            if os.path.isdir(folder_path):
                match = re.search(r'(.*) \((\d{4})\) {tmdb-(\d+)}', folder_name)
                if match:
                    title, year, tmdb_id = match.groups()
                    print(f"Title: {title}, Year: {year}, TMDB ID: {tmdb_id}")
                    # 根据TMDB ID重命名文件
                    self.tv_rename_id(tmdb_id, folder_path)
                else:
                    # 根据标题重命名文件
                    self.tv_rename_keyword(title, folder_path)

    def tv_rename_id(self,
                     tv_id: str,
                     folder_path: str,
                     folder_password=None,
                     first_number: int = 1) -> dict:
        """
        根据TMDB剧集id获取剧集标题,并批量将指定文件夹中的视频文件及字幕文件重命名为剧集标题.

        :param tv_id: 剧集id
        :param folder_path: 文件夹路径, 结尾必须加'/', 如/abc/test/
        :param folder_password: 文件夹访问密码
        :param first_number: 从指定集数开始命名, 如first_name=5, 则从第5集开始按顺序重命名
        :return: 重命名请求结果
        """

        if folder_path[-1] != '/':
            folder_path += '/'

        notice_msg = colorama.Fore.YELLOW + '[Notice!]' + colorama.Fore.RESET

        # 设置返回数据
        result = dict(success=False,
                      args=dict(tv_id=tv_id,
                                folder_path=folder_path,
                                folder_password=folder_password,
                                first_number=first_number),
                      result=[])

        # 根据剧集id 查找TMDB剧集信息
        tv_info_result = self.tmdb.tv_info(tv_id, language=self.tmdb_language, silent=False)
        result['result'].append(tv_info_result)

        # 若查找失败则停止，并返回结果
        if tv_info_result['request_code'] != 200:
            return result

        # 若查找结果只有一项，则无需选择，直接进行下一步
        if len(tv_info_result['seasons']) == 1:
            # 获取剧集对应季每集标题
            season_number = tv_info_result['seasons'][0]['season_number']
            tv_season_info = self.tmdb.tv_season_info(
                tv_id,
                tv_info_result['seasons'][0]['season_number'],
                language=self.tmdb_language,
                silent=self.debug)
            result['result'].append(tv_info_result)
            # 若获取失败则停止， 并返回结果
            if tv_season_info['request_code'] != 200:
                failure_msg = colorama.Fore.RED + '\n[TvInfo●Failure]' + colorama.Fore.RESET
                print(f"{failure_msg} 剧集id: {tv_id}\t{tv_info_result['name']} 第 {season_number} 季\n{tv_season_info['status_message']}")
                return result
        else:
            # 获取到多项匹配结果，手动选择
            while True:
                season_number = input(f"{notice_msg} 该剧集有多季,请输入对应[序号], 输入[n]退出\t")
                # active_number = list(range(len(tv_info_result['seasons'])))
                # active_number = list(map(lambda x: str(x), active_number))
                if season_number == 'n':
                    result['result'].append("用户输入[n], 已主动退出选择剧集季数")
                    return result
                else:
                    season_number = int(season_number)
                    break
                # else:
                #     continue

            # 获取剧集对应季每集信息
            for season_number in range(1, len(tv_info_result['seasons']) + 1):
                tv_season_info = self.tmdb.tv_season_info(tv_id, season_number, language=self.tmdb_language, silent=self.debug)
                result['result'].append(tv_season_info)
                # 若获取失败则停止， 并返回结果
                if tv_season_info['request_code'] != 200:
                    failure_msg = colorama.Fore.RED + '\n[TvInfo●Failure]' + colorama.Fore.RESET
                    print(f"{failure_msg} 剧集id: {tv_id}\t{tv_info_result['name']} 第 {season_number} 季\n{tv_season_info['status_message']}")
                    return result

                # 保存剧集标题
                episodes = list(
                    map(
                        lambda x: self.tv_name_format.format(
                            name=tv_info_result['name'], season=tv_season_info['season_number'], episode=x[
                                'episode_number'], title=x['name']),
                        tv_season_info['episodes']))

                episodes = episodes[first_number - 1:]

        file_list = os.listdir(folder_path)
        video_list = list(
            filter(lambda x: x.split(".")[-1] in ['mp4', 'mkv', 'flv', 'avi', 'mpg', 'mpeg', 'mov'],
                   file_list))
        subtitle_list = list(
            filter(lambda x: x.split(".")[-1] in ['srt', 'ass', 'stl'],
                   file_list))
        video_rename_list = list(
            map(
                lambda x, y: dict(original_name=x,
                                  target_name=y + '.' + x.split(".")[-1]),
                video_list, episodes))
        subtitle_rename_list = list(
            map(
                lambda x, y: dict(original_name=x,
                                  target_name=y + '.' + x.split(".")[-1]),
                subtitle_list, episodes))

        print("The following video files will be renamed: ")
        for video in video_rename_list:
            print("{} -> {}".format(video['original_name'],
                                    video['target_name']))
        print("The following subtitle files will be renamed: ")
        for subtitle in subtitle_rename_list:
            print("{} -> {}".format(subtitle['original_name'],
                                    subtitle['target_name']))

        while True:
            signal = input("Are you sure you want to rename? [Enter] to confirm, [n] to cancel\t")
            if signal.lower() == '':
                break
            elif signal.lower() == 'n':
                return
            else:
                continue

        for file in video_rename_list + subtitle_rename_list:
            os.rename(folder_path + file['original_name'], folder_path + file['target_name'])
            if self.debug:
                print("Renaming: {} -> {}".format(file['original_name'], file['target_name']))
            time.sleep(1)

        print("File renaming operation completed")

    def tv_rename_keyword(self,
                          keyword: str,
                          folder_path: str,
                          folder_password=None,
                          first_number: int = 1) -> dict:
        """
        根据TMDB剧集关键词获取剧集标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为剧集标题.

        :param keyword: 剧集关键词
        :param folder_path: 文件夹路径, 结尾必须加'/', 如/abc/test/
        :param folder_password: 文件夹访问密码
        :param first_number: 从指定集数开始命名, 如first_name=5, 则从第5集开始按顺序重命名
        :return: 重命名请求结果
        """

        notice_msg = colorama.Fore.YELLOW + '[Notice!]' + colorama.Fore.RESET

        # 创建返回数据
        result = dict(success=False,
                      args=dict(keyword=keyword,
                                folder_path=folder_path,
                                first_number=first_number),
                      result=[])
        # 使用关键词查找剧集
        search_result = self.tmdb.search_tv(keyword, language=self.tmdb_language)
        result['result'].append(search_result)
        # 查找失败则停止, 并返回结果
        if search_result['request_code'] != 200 or len(
                search_result['results']) == 0:
            return result

        # 若查找结果只有一项, 则继续进行, 无需选择
        if len(search_result['results']) == 1:
            rename_result = self.tv_rename_id(
                search_result['results'][0]['id'], folder_path,
                folder_password, first_number)
            result['result'] += (rename_result['result'])
            return result

        # 若有多项, 则手动选择
        while True:
            tv_number = input(f"{notice_msg} 查找到多个结果, 请输入对应[序号], 输入[n]退出\t")
            active_number = list(range(len(search_result['results'])))
            active_number = list(map(lambda x: str(x), active_number))
            if tv_number == 'n':
                result['result'].append("用户输入[n], 已主动退出选择匹配剧集")
                return result
            elif tv_number in active_number:
                tv_id = search_result['results'][int(tv_number)]['id']
                break
            else:
                continue

        # 根据获取到的id进行重命名
        for season_number in range(1, len(search_result['results']) + 1):
            rename_result = self.tv_rename_id(search_result['results'][int(tv_number)]['id'], folder_path, first_number)
            result['result'] += (rename_result['result'])
        return result

if __name__ == '__main__':
    tmdb_key = 'e3c0a'
    root_folder_path = r'C:\Users\china\Desktop\备份\国剧\A'
    renamer = LocalMediaRename(tmdb_key)
    for folder_name in os.listdir(root_folder_path):
        folder_path = os.path.join(root_folder_path, folder_name)
        if os.path.isdir(folder_path):
            renamer.rename_files(folder_path)