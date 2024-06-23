import json
import os
import subprocess
import requests
from tqdm import tqdm

header = {}

def init_app():
    os.makedirs('outputs', exist_ok=True)
    with open('./settings.json','r') as f:
        settings_str = f.read()
        settings = json.loads(settings_str)
        headers : dict = settings.get('headers')
        keys = headers.keys()
        for key in keys:
            value = headers.get(key)
            header[key] = value
        bv_num = settings.get('bv_num')
        return bv_num

"""
获取视频cid以及视频名称
param:bv_num
return:cid,video_name
"""
def get_cid(bv_num):
    params={
        'bvid':bv_num
    }
    try:
        print('尝试获取cid')
        if bv_num == '':
            raise Exception('bv为空!')
        response = requests.get('https://api.bilibili.com/x/player/pagelist',params=params,headers=header)
        #print(response.text)
        data = json.loads(response.text)
        cid = data['data'][0]['cid']
        video_name = data['data'][0]['part']
        print('cid获取成功,您所请求的视频名称为',video_name)
        return cid,video_name
    except Exception as e:
        print('cid 获取失败',e)

"""
获取视频链接
param: bv_num ,cid
return: video_url,audio_url,flac_url(如果flac不存在则返回空字符串)
"""
def get_video_url(bv_num,cid):
    params = {
        'bvid':bv_num,
        'cid':cid,
        'fnval':16|64,
        'fourk':1,
    }
    try:
        print('尝试获取视频&音频链接')
        if bv_num == '' and cid == '':
            raise Exception("get_video_url 的参数为空")
        response = requests.get('https://api.bilibili.com/x/player/wbi/playurl',headers=header,params=params)
        json_data = json.loads(response.text)
        video_url = json_data['data']['dash']['video'][0]['baseUrl']
        audio_url = json_data['data']['dash']['audio'][0]['baseUrl']
        flac_url = json_data['data']['dash']['flac']
        if flac_url == None:
            flac_url = ''
        else:
            flac_url = json_data['data']['dash']['flac']['audio']['baseUrl']
        print('链接获取成功')
        return video_url,audio_url,flac_url
    except Exception as e:
        print('视频or音频地址获取失败',e)

#下载文件
def download_files(url,file_name):
    print("下载文件",file_name)
    try:
        response = requests.get(url,headers=header,stream=True)
        total_length = int(response.headers.get('content-length', 0))
        block_size = 1024
        progress_bar = tqdm(total=total_length, unit='iB', unit_scale=True)
        with open('outputs/'+file_name,'wb') as f:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                f.write(data)
        progress_bar.close()
        print('下载完毕',file_name)
    except Exception as e:
        print('下载错误',e)

"""
通过FFmepg将视频和音频压缩
"""
def compress_vedio(file_name):
    print('压缩视频中')
    COMMAND = ''
    if os.path.exists('./outputs/'+file_name+'.flac'):
        COMMAND = f'.\\ffmpeg\\bin\\ffmpeg -i outputs\\{file_name}.mp4 -i outputs\\{file_name}.flac -c:v copy -c:a flac -strict experimental outputs\\{file_name}_out.mp4'
    else:
        COMMAND = f'.\\ffmpeg\\bin\\ffmpeg -i outputs\\{file_name}.mp4 -i outputs\\{file_name}.mp3 -c:v copy -c:a aac -strict experimental outputs\\{file_name}_out.mp4'
    subprocess.run(COMMAND, shell=True)
    if os.path.exists('./outputs/'+file_name+'.flac'): 
        os.remove(f'outputs\\{file_name}.flac')
    else:
        os.remove(f'outputs\\{file_name}.mp3')
    os.remove(f'outputs\\{file_name}.mp4') 
    os.rename(f'outputs\\{file_name}_out.mp4',f'outputs\\{file_name}.mp4')
    full_path = os.path.realpath(f'outputs\\{file_name}.mp4')
    print('压缩完毕，视频保存在：',full_path)

"""
将整个流程封装为主函数,想通过bv号下载视频,只需要调用这个函数就行了
param: bv
"""
def get_video():
    try:
        bv = init_app()
        print('==============================程序启动===================================')
        cid,video_name = get_cid(bv)
        video_name = video_name.replace(' ','')
        video_url,audio_url,flac_url = get_video_url(bv,cid=cid)
        download_files(video_url,video_name+'.mp4')
        if flac_url == '':
            download_files(audio_url,video_name+'.mp3')
        else:
            download_files(flac_url,video_name+'.flac')
        compress_vedio(video_name)
        print('---------------------------------程序结束---------------------------------------')
    except Exception as e:
        print('运行错误:',e)



if __name__ == '__main__':
    get_video()
    input()
    
