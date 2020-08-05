#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import os
import sys
import re
import json
import requests
import argparse

re_avid = re.compile(r"(?<=Av)\d+(?=,)")
cache_json_fn = "cache.json"

def avinfo(avid):
    info_url = "https://api.bilibili.com/x/web-interface/view?aid=%s"%avid
    r = requests.get(info_url)
    if r.status_code == 200:
        info_json = json.loads(r.text)
        if info_json['code'] == 0:
            return info_json['code'], info_json["data"]["owner"]["name"]
        else:
            return info_json['code'],""
    return -1,""
def fetch_info(src_path):
    owner_dict = {}

    files = [f for f in os.listdir(src_path) if os.path.isfile(os.path.join(src_path, f))]
    total_file = len(files)
    count = 0
    for filename in files:
        count += 1
        if os.path.isdir(filename):
            continue
        result = re_avid.findall(filename)
        if len(result):
            avid = result[0]
            code, owner = avinfo(avid)
            if code == -1:
                pass
            if code == 0:
                print("%d/%d owner: %s\tfilename:%s"%(count, total_file, owner, filename))
                if owner in owner_dict:
                    owner_dict[owner].append({"file":filename,"avid":avid})
                else:
                    owner_dict[owner]=[{"file":filename,"avid":avid}]
            if code != 0:
                print("%d/%d error: %d\tfilename:%s"%(count, total_file, code, filename))
                if code in owner_dict:
                    owner_dict[code].append({"file":filename,"avid":avid})
                else:
                    owner_dict[code]=[{"file":filename,"avid":avid}]
        if count >= 1000:
            print("over 1000 videos bilibili will trigger anti-crawler's strategy, process these 1000 videos first.")
            break
        if count %200 == 0:
            bak_file = open(cache_json_fn, "w+")
            bak_file.write(json.dumps(owner_dict))
            bak_file.close()
            time.sleep(30)

    bak_file = open(cache_json_fn, "w+")
    bak_file.write(json.dumps(owner_dict))
    bak_file.close()
    print("\n")
    return owner_dict

def move_file(owner_dict, src_path, dst_path, catlog_number, misc_path):
    for owner in owner_dict:
        owner = owner
        try:
            if len(owner_dict[owner]):
                owner_path = os.path.join(dst_path, owner)
                if os.path.exists(owner_path) == False:
                    if len(owner_dict[owner]) > catlog_number:
                        os.makedirs(owner_path, 777)
                    else:
                        owner_path = os.path.join(dst_path, misc_path)
                print(owner+"\t"+owner_path)
                for av in owner_dict[owner]:
                    try:
                        file_src_path = os.path.join(src_path, av["file"])
                        file_dst_path = os.path.join(owner_path, av["file"])
                        print("\t"+av["file"])
                        if file_src_path != file_dst_path:
	                        os.rename(file_src_path, file_dst_path)
                    except Exception as e:
                        print(av,"got Exception",str(e))
                print("\n")
        except Exception as e:
            print(owner,"got Exception",str(e))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Catalog video download from Bilibili(Need filename have av number).')
    parser.add_argument('video_path', help="un-catlog video path")
    parser.add_argument('catlog_path', help="video catlog path")
    parser.add_argument('-m', "--misc_path", help="path to store videos number less than a amount(default: (catlog_path)/%(default)s )", default="misc", required=False)
    parser.add_argument('-n', "--catlog_number", help="less than the number will store in misc_path(default: %(default)s).", default=5)
    parser.add_argument('-c', help="use json cache, skip fetch from bilibili", action='store_true')
    args = parser.parse_args()

    # show_path = "/mnt/show/宅舞/"
    src_path = args.video_path
    dst_path = args.catlog_path
    if os.path.exists(src_path) == False:
        print("video_path isn't exist.")
        sys.exit(1)
    if os.path.exists(dst_path) == False:
        print("catlog_path isn't exist.")
        sys.exit(1)

    if not args.c:
        owner_dict = fetch_info(src_path)
    with open(cache_json_fn, 'r') as f:
        owner_dict = json.load(f)

    move_file(owner_dict, args.video_path, args.catlog_path, args.catlog_number, args.misc_path)

