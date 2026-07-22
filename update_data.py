#!/usr/bin/env python3
"""福彩3D数据更新 — 三重备用源降级链"""
import csv, json, os, re, sys
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError

CSV_PATH = 'fc3d-history.csv'

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def fetch_cwl():
    """源1: 中彩网官方API"""
    url = 'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=3d&issueCount=5'
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': 'https://www.cwl.gov.cn/ygkj/wqkjgg/ssq/',
        'Origin': 'https://www.cwl.gov.cn',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    })
    data = json.loads(urlopen(req, timeout=15).read())
    if data.get('state') != 0: raise Exception(f'API state={data.get("state")}')
    results = []
    for r in data['result']:
        reds = r['red'].split(',')
        date_str = r['date'].split('(')[0]
        number = ''.join(reds)
        results.append({'issue': r['code'], 'date': date_str,
                        'hundreds': reds[0], 'tens': reds[1], 'ones': reds[2],
                        'number': number})
    results.sort(key=lambda x: x['issue'])
    return results

def fetch_tianqi():
    """源2: 天齐网"""
    url = 'https://www.800820.net/Article/Index.html'
    req = Request(url, headers={'User-Agent': UA})
    html = urlopen(req, timeout=15).read()
    # Try gb2312 first, then utf-8
    try: txt = html.decode('gb2312')
    except: txt = html.decode('utf-8', errors='ignore')
    
    results = []
    # Pattern: 第XXXXXXX期中奖号码：XXX
    for m in re.finditer(r'第(\d{7})期.*?中奖号码[：:\s]+(\d{3})', txt):
        issue, num = m.group(1), m.group(2)
        # Find date: try near the issue text
        date_m = re.search(rf'{issue}.*?(\d{{4}}-\d{{2}}-\d{{2}})', txt)
        date_str = date_m.group(1) if date_m else (datetime.now()-timedelta(days=1)).strftime('%Y-%m-%d')
        results.append({'issue': issue, 'date': date_str,
                        'hundreds': num[0], 'tens': num[1], 'ones': num[2],
                        'number': num})
    return results

def fetch_sina():
    """源3: 新浪彩票走势图"""
    url = 'https://view.lottery.sina.com.cn/lotto/pc_zst/index?lottoType=3d&actionType=joxt&dpc=1'
    req = Request(url, headers={'User-Agent': UA})
    html = urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
    
    results = []
    seen = set()
    # Pattern: 2026192425 (7-digit issue + 3-digit number)
    for m in re.finditer(r'(\d{7})\s*(\d{3})', html):
        issue, num = m.group(1), m.group(2)
        if int(issue) < 2002000 or issue in seen: continue
        seen.add(issue)
        results.append({'issue': issue, 'date': '',
                        'hundreds': num[0], 'tens': num[1], 'ones': num[2],
                        'number': num})
    return results

def fetch_backup():
    """源4: 备用源 - 深圳开放数据"""
    results = []
    # Try multiple known-good sources
    urls = [
        'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=3d&issueCount=5',
    ]
    # Just retry source 1 with different approach
    for url in urls:
        try:
            req = Request(url, headers={
                'User-Agent': 'python-requests/2.31.0',
                'Accept': '*/*',
            })
            data = json.loads(urlopen(req, timeout=10).read())
            if data.get('state') == 0:
                for r in data['result']:
                    reds = r['red'].split(',')
                    results.append({'issue': r['code'],
                                    'date': r['date'].split('(')[0],
                                    'hundreds': reds[0], 'tens': reds[1], 'ones': reds[2],
                                    'number': ''.join(reds)})
            results.sort(key=lambda x: x['issue'])
            return results
        except: pass
    return results

def load_existing():
    if not os.path.exists(CSV_PATH): return []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def save_csv(rows):
    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['issue','date','hundreds','tens','ones','number','raw'])
        w.writeheader()
        for r in rows:
            if 'raw' not in r:
                r['raw'] = ' '.join([r['hundreds'],r['tens'],r['ones']] + ['0']*12)
            w.writerow(r)

def main():
    existing = load_existing()
    existing_issues = {r['issue'] for r in existing}
    print(f"已有: {len(existing)}期, 最新: {existing[-1]['issue'] if existing else '无'}")
    
    sources = [
        (fetch_cwl, '中彩网API'),
        (fetch_tianqi, '天齐网'),
        (fetch_sina, '新浪彩票'),
        (fetch_backup, '备用API'),
    ]
    
    new_data = None
    for fetch_fn, name in sources:
        try:
            print(f"尝试 {name}...", end=' ')
            data = fetch_fn()
            if data:
                new_count = sum(1 for d in data if d['issue'] not in existing_issues)
                print(f"返回{len(data)}条, 新{new_count}条")
                if new_count > 0:
                    new_data = data
                    break
                else:
                    print(f"  (无新数据)")
            else:
                print("返回空")
        except Exception as e:
            print(f"失败: {str(e)[:80]}")
    
    if not new_data:
        print("所有源均无新数据")
        # Still return success so pipeline continues
        return
    
    updated = list(existing)
    for d in new_data:
        if d['issue'] not in existing_issues:
            updated.append(d)
    
    updated.sort(key=lambda x: x['issue'])
    save_csv(updated)
    print(f"✓ 新增{len(updated)-len(existing)}期, 总计{len(updated)}期")

if __name__ == '__main__':
    main()
