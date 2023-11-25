# MediaAO 1.0.6 

## 功能概述
MediaAO是一个强大的媒体文件管理和重命名工具。它的主要目标是帮助您整理和管理您的电影和电视剧集，使它们更易于搜索和访问。

## 运行环境
- Python 3.6 或更高版本
- 需要安装的Python库：`requests`, `os`, `re`, `logging`
- 需要有访问TMDB API和Plex API的权限

## 使用指南
1. 首先，您需要在`config.json`文件中设置您的Plex服务器信息和TMDB API密钥。
2. 然后，您可以运行`main.py`来启动程序。
3. 程序会提示您选择匹配模式、库类型、命名规则和父文件夹路径。
4. 根据您的选择，程序会开始处理文件夹，并根据匹配的媒体信息重命名文件夹。

## 注意事项
- 请确保您有权限修改文件夹的名称。
- 在使用此工具之前，请备份您的文件，以防万一出现错误。
- 请确保您的API密钥是正确的，否则程序将无法获取媒体信息。

## 已实现的功能
1. Plex匹配模式：根据Plex库中的媒体信息重命名文件夹。
2. Tmdb匹配模式：根据TMDB中的媒体信息重命名文件夹。
3. 格式转换模式：根据用户选择的命名规则重命名文件夹。
4. 清理命名模式：删除文件夹名称中的非法字符。
5. 批量改电影文件名：通过执行rename_movie.py实现
6. 批量改剧集文件名：通过执行rename_show.py实现

## 免责声明
此工具仅供个人使用，作者不对任何由此工具引起的数据丢失或损坏负责。在使用此工具之前，请确保您已经备份了所有重要的文件。

我们希望这个介绍能帮助您更好地理解和使用MediaAO。如果您有任何问题或建议，欢迎随时提出。祝您使用愉快！
# MediaAO

## Feature Overview
MediaAO is a robust tool for managing and renaming media files. Its primary goal is to help you organize your movie and TV show collections, making them more searchable and accessible.

## System Requirements
- Python 3.6 or higher
- Required Python libraries: `requests`, `os`, `re`, `logging`
- Access to TMDB API and Plex API

## How to Use
1. First, you need to set up your Plex server information and TMDB API key in the `config.json` file.
2. Then, you can run `main.py` to start the program.
3. The program will prompt you to choose the match mode, library type, naming rule, and parent folder path.
4. Based on your choices, the program will start processing folders and rename them according to the matched media information.

## Precautions
- Please ensure that you have the necessary permissions to rename folders.
- Please back up your files before using this tool to prevent any accidental loss or damage.
- Ensure that your API keys are correct; otherwise, the program will not be able to retrieve media information.

## Implemented Features
1. Plex Match Mode: Renames folders based on media information in the Plex library.
2. TMDB Match Mode: Renames folders based on media information in TMDB.
3. Format Conversion Mode: Renames folders according to the user-selected naming rule.
4. Clean Naming Mode: Removes illegal characters from folder names.

## Disclaimer
This tool is for personal use only. The author is not responsible for any data loss or damage caused by this tool. Please ensure that you have backed up all important files before using this tool.

We hope this introduction helps you understand and use MediaAO better. If you have any questions or suggestions, feel free to raise them at any time. Enjoy using MediaAO!
