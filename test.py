

```python
import os
import re
import json
from api import PlexApi
from config import ConfigManager
import requests
CONFIG_FILE = 'config.json' 

def get_file_info(file_path):
    filename = os.path.basename(file_path).replace('.', ' ')
    file_name_no_ext, file_ext = os.path.splitext(filename)

    elements_regex = {
        "year": r'\b(19[0-9]{2}|20[0-5][0-9])\b',
        "resolution": r'(\d{3}P|\dK)',

        "source": r'\b(REMUX|BDREMUX|BD-REMUX|BLURAY|BD|BLU-RAY|BD1080P|BDRIP|WEB|WEB-DL|WEBDL|WEBRIP|HR-HDTV|HRHDTV|HDTV|HDRIP|DVDRIP|DVDSCR|DVD|HDTC|TC|HQCAM|HQ-CAM|CAM|TS)\b',
        "codec": r'\b(X264|X265|H\.264|H\.265|HEVC|VP8|VP9|AV1|VC1|MPEG1|MPEG2|MPEG-4|Theora|ProRes)\b',
        "bit_depth": r'\b\d{1,2}BIT\b',
        "hdr_info": r'\b(SDR|HDR|HDR10|DOLBY VISION|HDR10+|HLG|DISPLAYHDR)\b',
        "audio_format": r'\b(MP3|AAC|WAV|FLAC|ALAC|APE|LPCM)\b',
        "audio_standard": r'\b(DTS-HD MA|DTS-HD HR|DTS:X|AC-3 EX|E-AC-3|TRUEHD|ATMOS|DTS|DD\+|AC3|DD|EX|DDL|7 1|5 1|DTS-HD\.MA\.TrueHD\.7\.1\.Atmos)\b',
        "edit_version": r'\b(PROPER|REPACK|LIMITED|DUPE|IMAX|UNRATE|R-RATE|SE|DC|WITH EXTRAS|RERIP|SUBBED|DIRECTOR\'S CUT|THEATRICAL CUT|ANNIVERSARY EDITION|CEE|EUR|US|NODIC|UK|FRA|GRE|HK|TW|JPN|KR|REMASTERED|OPEN MATTE)\b'
    }
    }

    elements = {key: None for key in elements_regex.keys()}

    for key, regex in elements_regex.items():
        matches = re.findall(regex, filename, re.IGNORECASE)
        if matches:
            elements[key] = ' '.join(matches)
            for match in matches:
                filename = filename.replace(match, '')

    chinese_title = re.search(r'《([^》]+)》', filename)
    if chinese_title:
        elements['title'] = chinese_title.group(1)
        filename = filename.replace(chinese_title.group(0), '')
    else:
        chinese_title = re.search(r'[\u4e00-\u9fff]+', filename)
        english_title = re.search(r'[a-zA-Z]+(\s[a-zA-Z]+)*', filename)
        elements['title'] = chinese_title.group(0) if chinese_title else english_title.group(0) if english_title else None

    if elements['title'] is None:
        parent_folder_name = os.path.basename(os.path.dirname(file_path))
        chinese_title = re.search(r'[\u4e00-\u9fff]+', parent_folder_name)
        english_title = re.search(r'[a-zA-Z0-9_]+', parent_folder_name)
        elements['title'] = chinese_title.group(0) if chinese_title else english_title.group(0) if english_title else None

    return elements

def search_movie(plex_api, title, year=None):
    search_endpoint = f"/search?query={title}"
    search_url = plex_api.plex_url + search_endpoint
    response = requests.get(search_url, headers=plex_api.headers)
    movies = response.json()

    if 'Metadata' in movies['MediaContainer']:
        for media in movies['MediaContainer']['Metadata']:
            extracted_info = {}
            extracted_info['title'] = media.get('title')
            extracted_info['year'] = media.get('year')
            resolution = media.get('Media')[0].get('videoResolution')
            extracted_info['resolution'] = resolution + 'P' if resolution != '4K' else resolution
            bitrate_mbps = media.get('Media')[0].get('bitrate') / 8
            if bitrate_mbps <= 5:
                extracted_info['source'] = 'TS'
            elif 5 < bitrate_mbps <= 10:
                extracted_info['source'] = 'DVD'
            elif 10 < bitrate_mbps <= 20:
                extracted_info['source'] = 'HDTV'
            elif 20 < bitrate_mbps <= 60:
                extracted_info['source'] = 'BLURAY'
            elif 60 < bitrate_mbps <= 80:
                extracted_info['source'] = 'REMUX'
            else:
                extracted_info['source'] = 'BLURAY.REMUX'
            extracted_info['codec'] = media.get('Media')[0].get('videoCodec')
            extracted_info['audio_format'] = media.get('Media')[0].get('audioCodec')
            extracted_info['edit_version'] = None
            return extracted_info

    return None

def get_plex_info(filenames, plex_api):
    plex_info_dict = {}
    for filename in filenames:
        title, *year = filename.rsplit(' ', 1)
        year = year[0] if year else None
        plex_info = search_movie(plex_api, title, year)
        if plex_info:
            plex_info_dict[filename] = plex_info
    return plex_info_dict

def collect_files_info(parent_folder_path):
    files_info = {}
    all_filenames = []

    for root, dirs, files in os.walk(parent_folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            file_info = get_file_info(file_path)
            if file_info:
                files_info[file_path] = file_info
                all_filenames.append(filename)
    return files_info, all_filenames

def process_files_info(files_info, plex_info, plex_api):
    rename_dict = {}
    for file_path, elements_from_file in files_info.items():
        final_elements = elements_from_file.copy()

        if file_path in plex_info:
            for key, value in plex_info[file_path].items():
                if not final_elements.get(key):
                    final_elements[key] = value

        new_filename = f"{final_elements['title']}.{final_elements['year']}.{final_elements['resolution']}.{final_elements['source']}.{final_elements['codec']}.{final_elements['bit_depth']}.{final_elements['hdr_info']}.{final_elements['audio_format']}.{final_elements['audio_standard']}.{final_elements['edit_version']}.{file_ext}"
        rename_dict[file_path] = os.path.join(os.path.dirname(file_path), new_filename)
    return rename_dict

def rename_files(rename_dict):
    for i, (old_name, new_name) in enumerate(rename_dict.items()):
        choices = input("请输入你不想修改的文件序号，如果全部修改，请直接按回车：")
        if choices:
            choices = map(int, choices.split())
            for choice in choices:
                del rename_dict[list(rename_dict.keys())[choice]]

        for old_name, new_name in rename_dict.items():
            os.rename(old_name, new_name)

def main():
    config_manager = ConfigManager(CONFIG_FILE)
    server_info_and_key = config_manager.get_server_info_and_key()
    plex_api = PlexApi(server_info_and_key['plex_url'], server_info_and_key['plex_token'])

    parent_folder_path = input("请输入父文件夹的路径：")
    files_info, all_filenames = collect_files_info(parent_folder_path)

    plex_info = get_plex_info(all_filenames, plex_api)

    rename_dict = process_files_info(files_info, plex_info, plex_api)

    rename_files(rename_dict)

if __name__ == "__main__":
   main()
```