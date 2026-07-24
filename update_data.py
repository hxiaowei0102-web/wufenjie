#!/usr/bin/env python3
"""福彩3D数据更新 — 灰鸟API主源 + 三重兜底"""
import csv, json, os, re, sys
from datetime import datetime, timedelta
from urllib.request import Request, urlopen

CSV_PATH = 'fc3d-history.csv'

def fetch_huiniao(count=5):
    """源1: 灰鸟API (免费, 无认证, 已验证准确)"""
    url = f'http://api.huiniao.top/interface/home/lotteryHistory?type=fcsd&limit={count}'
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = json.loads(urlopen(req, timeout=15).read())
    if data.get('code') != 1: return []
    results = []
    for item in data['data']['data']['list']:
        num = f"{item['one']}{item['two']}{item['three']}"
        results.append({'issue': item['code'], 'date': item['day'],
                        'hundreds': str(item['one']), 'tens': str(item['two']), 'ones': str(item['three']),
                        'number': num})
    results.sort(key=lambda x: x['issue'])
    return results

def fetch_cwl():
    """源2: 中彩网官方API"""
    try:
        url = 'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=3d&issueCount=5'
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.cwl.gov.cn/',
        })
        data = json.loads(urlopen(req, timeout=10).read())
        if data.get('state') != 0: return []
        results = []
        for r in data['result']:
            reds = r['red'].split(',')
            results.append({'issue': r['code'], 'date': r['date'].split('(')[0],
                            'hundreds': reds[0], 'tens': reds[1], 'ones': reds[2],
                            'number': ''.join(reds)})
        results.sort(key=lambda x: x['issue'])
        return results
    except: return []

def fetch_cors():
    """源3: CORS代理+中彩网"""
    api_url = 'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=3d&issueCount=5'
    from urllib.parse import quote
    encoded = quote(api_url, safe='')
    proxies = [f'https://api.allorigins.win/raw?url={encoded}',
               f'https://api.codetabs.com/v1/proxy?quest={encoded}']
    for url in proxies:
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = json.loads(urlopen(req, timeout=20).read())
            if isinstance(data, dict) and data.get('state') == 0:
                results = []
                for r in data['result']:
                    reds = r['red'].split(',')
                    results.append({'issue': r['code'], 'date': r['date'].split('(')[0],
                                    'hundreds': reds[0], 'tens': reds[1], 'ones': reds[2],
                                    'number': ''.join(reds)})
                results.sort(key=lambda x: x['issue'])
                return results
        except: continue
    return []

def main():
    if not os.path.exists(CSV_PATH):
        print(f'ERROR: {CSV_PATH} not found')
        sys.exit(1)

    existing = set()
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f): existing.add(row['issue'])

    sources = [('灰鸟API', fetch_huiniao), ('中彩网API', fetch_cwl), ('CORS代理', fetch_cors)]
    new_data = []
    for name, fn in sources:
        try:
            results = fn()
            if results:
                new = [r for r in results if r['issue'] not in existing]
                print(f'  源 {name}: 返回{len(results)}条, 新增{len(new)}条')
                if new:
                    new_data = new
                    break
            else:
                print(f'  源 {name}: 无数据')
        except Exception as e:
            print(f'  源 {name}: 失败 - {e}')
    
    if not new_data:
        print('所有源均无新数据, 跳过更新')
        return

    with open(CSV_PATH, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for r in new_data:
            writer.writerow([r['issue'], r['date'], r['hundreds'], r['tens'], r['ones'],
                            r['number'], f'{r["hundreds"]} {r["tens"]} {r["ones"]} 0 0 0 0 0 0 0 0 0 0 0 0'])
    print(f'追加{len(new_data)}期: {[r["issue"] for r in new_data]}')

if __name__ == '__main__':
    main()
