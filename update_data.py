#!/usr/bin/env python3
"""福彩3D数据更新 — 三重备用源降级链"""
import csv, json, os, sys, re, time
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError

CSV_PATH = 'fc3d-history.csv'
BACKUP_PATH = 'fc3d-history.backup.csv'

def fetch_cwl():
    """源1: 中彩网官方API (JSON)"""
    url = 'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=3d&issueCount=5'
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = json.loads(urlopen(req, timeout=15).read())
    if data.get('state') != 0: raise Exception('API error')
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

def fetch_800820():
    """源2: 天齐网 (HTML)"""
    url = 'https://www.800820.net/Article/Index.html'
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urlopen(req, timeout=15).read().decode('gb2312', errors='ignore')
    # Parse: 福彩3D第2026192期 + 中奖号码：425
    results = []
    for match in re.finditer(r'第(\d{7})期.*?中奖号码[：:]\s*(\d{3})', html, re.DOTALL):
        issue, num = match.group(1), match.group(2)
        # Find date near the issue
        date_match = re.search(rf'{issue}.*?(\d{{4}}-\d{{2}}-\d{{2}})', html)
        date_str = date_match.group(1) if date_match else (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        results.append({'issue': issue, 'date': date_str,
                        'hundreds': num[0], 'tens': num[1], 'ones': num[2],
                        'number': num})
    results.sort(key=lambda x: x['issue'])
    return results

def fetch_sina():
    """源3: 新浪彩票走势图 (HTML)"""
    url = 'https://view.lottery.sina.com.cn/lotto/pc_zst/index?lottoType=3d&actionType=joxt&dpc=1'
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
    # Pattern: 2026192 425 in HTML table
    results = []
    for match in re.finditer(r'(\d{7})\s+(\d)\s+(\d)\s+(\d)\s+', html):
        issue, b, s, g = match.group(1), match.group(2), match.group(3), match.group(4)
        num = b + s + g
        if int(issue) > 2002000:  # valid 3D issue
            results.append({'issue': issue, 'date': '',  # date not in this view
                            'hundreds': b, 'tens': s, 'ones': g, 'number': num})
    results.sort(key=lambda x: x['issue'])
    return results

def load_existing():
    """加载已有CSV"""
    if not os.path.exists(CSV_PATH): return []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def save_csv(rows):
    """保存CSV"""
    # Backup first
    if os.path.exists(CSV_PATH):
        import shutil
        shutil.copy(CSV_PATH, BACKUP_PATH)
    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['issue','date','hundreds','tens','ones','number','raw'])
        w.writeheader()
        for r in rows:
            r.setdefault('raw', ' '.join([r['hundreds'],r['tens'],r['ones']] 
                          + ['0']*12))
            w.writerow(r)

def main():
    existing = load_existing()
    existing_issues = {r['issue'] for r in existing}
    print(f"已有: {len(existing)}期, 最新: {existing[-1]['issue'] if existing else '无'}")
    
    # Try sources in order
    new_data = None
    sources = [(fetch_cwl, '中彩网API'), (fetch_800820, '天齐网'), (fetch_sina, '新浪')]
    
    for fetch_fn, name in sources:
        try:
            print(f"尝试 {name}...")
            data = fetch_fn()
            if data:
                # Verify: at least one new issue
                new_count = sum(1 for d in data if d['issue'] not in existing_issues)
                if new_count > 0:
                    print(f"  {name}返回{len(data)}条, 新数据{new_count}条")
                    new_data = data
                    break
                else:
                    print(f"  {name}无新数据")
            else:
                print(f"  {name}返回空")
        except Exception as e:
            print(f"  {name}失败: {e}")
    
    if not new_data:
        print("所有源均无新数据，退出")
        return
    
    # Merge: append new issues
    updated = list(existing)
    for d in new_data:
        if d['issue'] not in existing_issues:
            updated.append(d)
    
    # Sort by issue
    updated.sort(key=lambda x: x['issue'])
    
    # Save
    save_csv(updated)
    new_added = len(updated) - len(existing)
    print(f"✓ 追加{new_added}期, 总计{len(updated)}期")
    print(f"  最新5期: {', '.join(r['number'] for r in updated[-5:])}")

if __name__ == '__main__':
    main()
