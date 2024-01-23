# -*- coding: UTF-8 -*-
'''
Author: Linzjian666
Date: 2024-01-22 23:02:35
LastEditors: Linzjian666
LastEditTime: 2024-01-23 23:16:47
'''
import yaml
import urllib.request
import logging
import re
import base64
from urllib.parse import unquote

def process_url(urls_file):
    with open(urls_file, 'r') as f:
        urls = f.read().splitlines()
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    proxies_urls = ''
    
    for url in urls:
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        proxies_base64 = response.read().decode('utf-8')
        
        proxies_urls += base64.b64decode(proxies_base64).decode('utf-8')
        
    
    return proxies_urls

def extract_vless_urls(data):
    all_vless_urls = re.findall(r'vless://[^\n]+', data)
    vless_urls = []
    for vless_url in all_vless_urls:
        name = re.search(r'#([^&]+)', vless_url).group(1)
        if(name in ['ed','Author%3A%20mjjonone']):
            continue
        vless_urls.append(vless_url)
    for i, vless_url in enumerate(vless_urls):  # 删去security及sni字段
        security = re.search(r'(security=[^&]+)&(sni=[^&]+)', vless_url)
        vless_urls[i] = vless_url.replace(security.group(0), "security=none")
        name = re.search(r'#([^&]+)', vless_url).group(1)
        country = re.search(r'([A-Z]{2})-', vless_url).group(1)
        flag_emoji = ''
        for j in range(len(country)):
            flag_emoji += chr(ord(country[j]) + ord('🇦') - ord('A'))  # 
        if(flag_emoji == '🇹🇼'):
            flag_emoji = '🇨🇳'
        vless_urls[i] = vless_urls[i].replace(name, f'{flag_emoji} {name}')
        logging.info(f'已处理: {vless_urls[i]}')
    
    return vless_urls

def write_clash_meta_profile(template_file, output_file, proxy_urls):
    with open(template_file, 'r', encoding='utf-8') as f:
        profile = yaml.safe_load(f)
    for proxy_url in proxy_urls:
        name = re.search(r'#([^&]+)', proxy_url).group(1)
        name = unquote(name)  # URL解码
        uuid = re.search(r'vless://([^@]+)@([^:]+):([^?]+)', proxy_url).group(1)
        server = re.search(r'vless://([^@]+)@([^:]+):([^?]+)', proxy_url).group(2)
        port = re.search(r'vless://([^@]+)@([^:]+):([^?]+)', proxy_url).group(3)
        host = re.search(r'host=([^&]+)&', proxy_url).group(1)
        path = re.search(r'path=([^#]+)#', proxy_url).group(1)
        path = unquote(path)

        proxy = {
            "name": f"{name}",
            "server": server,
            "port": port,
            "type": "vless",
            "uuid": uuid,
            "tls": False,
            "network": "ws",
            "ws-opts": {
                "path": f"{path}",
                "headers": {
                    "Host": host
                }
            }
        }

        # print(name, uuid, server, port, host, path)
        proxies.append(proxy)
    if('proxies' not in profile or not profile['proxies']):
        profile['proxies'] = proxies
    else:
        profile['proxies'].extend(proxies)
    for group in profile['proxy-groups']:
        if(group['name'] in ['🚀 节点选择','♻️ 自动选择','📺 巴哈姆特','📺 哔哩哔哩','🌏 国内媒体','🌍 国外媒体','📲 电报信息','Ⓜ️ 微软云盘','Ⓜ️ 微软服务','🍎 苹果服务','📢 谷歌FCM','🤖 OpenAI','🐟 漏网之鱼']):
            if('proxies' not in group or not group['proxies']):
                group['proxies'] = [proxy['name'] for proxy in proxies]
            else:
                group['proxies'].extend(proxy['name'] for proxy in proxies)
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(profile, f, sort_keys=False, allow_unicode=True)

def write_urls_file(output_file, proxy_urls):
    with open(output_file, 'w', encoding='utf-8') as f:
        for proxy_url in proxy_urls:
            f.write(proxy_url + '\n')

def write_base64_file(output_file, proxy_urls_file):
    with open(proxy_urls_file, 'r', encoding='utf-8') as f:
        proxy_urls = f.read()
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(base64.b64encode(proxy_urls.encode('utf-8')).decode('utf-8'))

if __name__ == '__main__':
    proxies_urls = process_url('urls.txt')
    vless_urls = extract_vless_urls(proxies_urls)
    proxies = []
    write_urls_file('./outputs/vless_urls', vless_urls)
    write_base64_file('./outputs/base64', './outputs/vless_urls')
    write_clash_meta_profile('./templates/clash_meta.yaml', './outputs/clash-meta.yaml', vless_urls)