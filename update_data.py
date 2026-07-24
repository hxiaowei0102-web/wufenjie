#!/usr/bin/env python3
"""福彩3D数据更新 — 500.com主源 + 中彩网兜底"""
import csv, json, os, re, sys
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError

CSV_PATH = 'fc3d-history.csv'

def fetch_500():
    """源1: 500.com 开奖页面 HTML解析"""
    url = 'https://kaijiang.500.com/3d.shtml'
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
    })
    try:
        html = urlopen(req, timeout=15).read().decode('gb2312', errors='ignore')
    except Exception as e:
        raise Exception(f'500.com: {e}')
    
    results = []
    # Pattern: <span class="span_right">2026194</span> ... <div class="ball_red">2</div><div class="ball_red">8</div><div class="ball_red">3</div>
    # or simple: find issue-number pairs
    issues = re.findall(r'<span[^>]*>(\d{7})</span>', html)
    # find 3-digit numbers near the issue
    for issue in issues[-5:]:
        # Search for 3 single-digit numbers after this issue
        pos = html.find(issue)
        if pos < 0: continue
        snippet = html[pos:pos+500]
        digits = re.findall(r'>(\d)<', snippet)
        if len(digits) >= 3:
            num = ''.join(digits[:3])
            if num.isdigit() and len(num) == 3:
                results.append({'issue': issue, 'date': '',
                                'hundreds': num[0], 'tens': num[1], 'ones': num[2],
                                'number': num})
    results.sort(key=lambda x: x['issue'])
    return results

def fetch_cwl():
    """源2: 中彩网官方API"""
    url = 'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=3d&issueCount=5'
    try:
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.cwl.gov.cn/',
        })
        data = json.loads(urlopen(req, timeout=10).read())
    except: return []
    
    if data.get('state') != 0: return []
    results = []
    for r in data['result']:
        reds = r['red'].split(',')
        results.append({'issue': r['code'], 'date': r['date'].split('(')[0],
                        'hundreds': reds[0], 'tens': reds[1], 'ones': reds[2],
                        'number': ''.join(reds)})
    results.sort(key=lambda x: x['issue'])
    return results

def fetch_cors():
    """源3: 中彩网API via CORS代理"""
    proxies = [
        'https://api.allorigins.win/raw?url=',
        'https://corsproxy.io/?',
    ]
    api_path = 'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=3d&issueCount=5'
    from urllib.parse import quote
    for proxy in proxies:
        try:
            url = proxy + quote(api_path, safe='')
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = json.loads(urlopen(req, timeout=15).read())
            if data.get('state') == 0:
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
    # Ensure CSV exists
    if not os.path.exists(CSV_PATH):
        print(f'ERROR: {CSV_PATH} not found')
        sys.exit(1)
    
    # Read existing issues
    existing = set()
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            existing.add(row['issue'])
    
    # Try sources in order
    sources = [
        ('500.com', fetch_500),
        ('中彩网API', fetch_cwl),
        ('CORS代理', fetch_cors),
    ]
    
    new_data = []
    for name, fn in sources:
        try:
            results = fn()
            if results:
                new_count = len([r for r in results if r['issue'] not in existing])
                print(f'  源 {name}: 返回{len(results)}条, 新增{new_count}条')
                new_data = [r for r in results if r['issue'] not in existing]
                if new_data:
                    break
            else:
                print(f'  源 {name}: 无数据')
        except Exception as e:
            print(f'  源 {name}: 失败 - {e}')
    
    if not new_data:
        print('所有源均无新数据, 跳过更新')
        return
    
    # Append new data
    with open(CSV_PATH, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for r in new_data:
            writer.writerow([r['issue'], r['date'], r['hundreds'], r['tens'], r['ones'],
                            r['number'], f'{r["hundreds"]} {r["tens"]} {r["ones"]} 0 0 0 0 0 0 0 0 0 0 0 0'])
    print(f'追加{len(new_data)}期: {[r["issue"] for r in new_data]}')
    
    # Also write backup
    with open('fc3d-history.backup.csv', 'w', encoding='utf-8') as fb:
        with open(CSV_PATH, 'r', encoding='utf-8') as fsrc:
            fb.write(fsrc.read())

if __name__ == '__main__':
    main()
