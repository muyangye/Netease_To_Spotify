<p align="center"><img src="cover.png" /></p>

# 网易云音乐歌单迁移至Spotify

## 测试成功率: 593/595, 用时: 一分钟左右，已知所有的迁移库中最快成功率最高，保留原歌单顺序，全过程不产生费用

## 运行
1. 命令行输入`pip install -r requirements.txt`
2. [创建Spotify app(如没有)](https://developer.spotify.com/documentation/web-api/concepts/apps)
3. 替换`config.yml`里的所有值，说明如下:
    - `client_id`: Spotify app的Client ID
    - `client_id`: Spotify app的Client secret
    - `redirect_uri`: Spotify app的Redirect URIs中任意一个
    - `spotify_playlist_name`: 迁移过后在Spotify里的歌单名，如填已存在的歌单则把所有歌曲插入到歌单最前，否则先创建歌单再迁移
    - `cover_image_path`: 新歌单封面图路径(图像大小必须小于256 KB)，如歌单已存在则不适用，默认值为repo里的"netease.png"
    - `netease_playlist_id`: 想要迁移的网易云音乐歌单id，可通过分享歌单的链接拿到，比如分享链接为https://music.163.com/playlist?id=123456789&userid=xxxxxxxx<span>，歌单id就是123456789</span>
4. 命令行输入`python cli.py`
5. 浏览器弹窗提示登录Spotify
6. 等待运行即可，Spotify无版权的歌曲会在命令行提示

## 鸣谢
- [pyncm](https://github.com/mos9527/pyncm): 感谢老哥的网易云音乐API，真不理解为啥网易云音乐只开放API给合作方
- [spotipy](https://github.com/spotipy-dev/spotipy): 本来研究了挺久OAuth 2.0写好所有raw requests的基类了，然后发现了这个。。。
- [这个issue](https://github.com/Binaryify/NeteaseCloudMusicApi/issues/1121#issuecomment-774438040)