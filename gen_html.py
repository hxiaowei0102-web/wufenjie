#!/usr/bin/env python3
"""Generate HTML directly from analysis data"""
import json, os
json_path = 'analysis_result.json'
if not os.path.exists(json_path):
    json_path = 'D:/五五分解/analysis_result.json'
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

P = data['prediction']
A = data['accuracy']
B = data['backtest_200']
R = data['rec_accuracy']
V = P.get('version','S72')
M = P.get('rec_mean_22win',76.7)
S = P.get('rec_std_22win',2.0)
R = data['rec_accuracy']

# Build backup decomps HTML
backup_html = ''
for d in P['all_decomps']:
    if d['name'] != P['rec_name']:
        backup_html += f'<span class="bd">{d["name"]}: {d["decomp"]}</span>'

# Build accuracy cards
acc_cards = ''.join(
    f'<div class="stat-card"><div class="l">{k}</div><div class="v">{v}%</div></div>'
    for k, v in A.items()
)

# Build table rows
rows_html = ''
for r in B['results']:
    cls = '' if r['ensemble_ok'] else 'fail'
    s_ok = 'ok' if r['single_ok'] else 'ng'
    s_sym = '✓' if r['single_ok'] else '✗'
    e_ok = 'ens-ok' if r['ensemble_ok'] else 'ens-ng'
    e_sym = '✓' if r['ensemble_ok'] else '✗'
    rows_html += (
        f'<tr class="{cls}">'
        f'<td class="issue">{r["issue"]}</td>'
        f'<td>{r["date"]}</td>'
        f'<td class="num">{r["number"]}</td>'
        f'<td class="rec">{r["rec_decomp"]}</td>'
        f'<td class="{s_ok}">{s_sym}</td>'
        f'<td class="{e_ok}">{e_sym}</td>'
        f'</tr>'
    )

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>福彩3D 五五分解预测系统</title>
<style>
:root{{--bg:#f5f6fa;--card:#fff;--text:#2d3436;--t2:#636e72;--border:#e0e4ea;--ok:#27ae60;--fail:#e74c3c;--pri:#0984e3;--gold:#d4a017;--sh:0 2px 12px rgba(0,0,0,.06);--rd:12px}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;padding:8px;font-size:14px}}
.container{{max-width:1100px;margin:0 auto}}
.header{{background:linear-gradient(135deg,#2e7d32,#1b5e20);color:#fff;padding:22px 28px;border-radius:var(--rd);margin-bottom:20px;box-shadow:var(--sh)}}
.header h1{{font-size:22px;font-weight:700}}.header .sub{{font-size:12px;opacity:.9;margin-top:2px}}
.card{{background:var(--card);border-radius:var(--rd);padding:18px 22px;box-shadow:var(--sh);border:1px solid var(--border);margin-bottom:16px}}
.card h3{{font-size:13px;color:var(--t2);margin-bottom:10px;font-weight:600}}
.pred-main{{background:linear-gradient(135deg,#e8f5e9,#c8e6c9);border:2px solid var(--ok);display:flex;align-items:center;gap:20px;flex-wrap:wrap}}
.pred-left{{flex:1;min-width:150px}}.pred-center{{flex:2;min-width:280px;text-align:center}}.pred-right{{flex:1;min-width:150px;text-align:center}}
.pred-issue{{font-size:40px;font-weight:900;color:var(--ok);line-height:1}}
.pred-sub{{font-size:12px;color:var(--t2)}}.pred-date{{font-size:13px;color:var(--t2)}}
.pred-decomp{{background:#fff;border-radius:8px;padding:16px 20px;margin:8px 0;border:2px dashed var(--ok)}}
.pred-decomp .name{{font-size:11px;color:var(--pri);font-weight:700;margin-bottom:3px}}
.pred-decomp .split{{font-size:28px;font-weight:900;letter-spacing:4px}}
.pred-reason{{font-size:11px;color:var(--t2);margin-top:3px}}
.acc-big{{font-size:52px;font-weight:900;color:var(--ok);line-height:1}}.acc-sub{{font-size:11px;color:var(--t2)}}
.acc-big2{{font-size:36px;font-weight:900;color:#f39c12;line-height:1}}
.grid-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}}
.stat-card{{background:var(--card);border-radius:var(--rd);padding:12px 14px;text-align:center;box-shadow:var(--sh);border:1px solid var(--border);border-top:3px solid var(--ok)}}
.stat-card .v{{font-size:28px;font-weight:800;color:var(--ok)}}.stat-card .l{{font-size:11px;color:var(--t2)}}
.table-wrap{{overflow:auto;border-radius:var(--rd);box-shadow:var(--sh);background:var(--card);border:1px solid var(--border);max-height:60vh}}
table{{width:100%;border-collapse:collapse;font-size:11px}}
thead{{position:sticky;top:0;z-index:10}}
th{{background:#2d3436;color:#fff;padding:7px 5px;text-align:center;font-weight:600;font-size:10px;white-space:nowrap}}
td{{padding:6px 5px;text-align:center;border-bottom:1px solid #f0f0f0}}
tr:hover{{background:#f8f9ff}}tr.fail{{background:#fff5f5}}tr.fail:hover{{background:#ffebeb}}
td.issue{{font-weight:600;color:var(--pri);white-space:nowrap}}
td.num{{font-weight:700;font-size:13px;letter-spacing:2px}}
td.ok{{color:var(--ok);font-weight:700}}td.ng{{color:var(--fail);font-weight:700}}
td.ens-ok{{color:var(--ok);font-size:14px}}td.ens-ng{{color:var(--fail);font-size:14px;background:#fff0f0}}
td.rec{{font-size:10px;color:var(--pri);font-weight:600}}
.btn{{font-size:11px;padding:5px 12px;border:1px solid var(--border);border-radius:14px;cursor:pointer;background:#fff;color:var(--t2);margin:0 3px}}
.btn.active{{background:var(--pri);color:#fff;border-color:var(--pri)}}
.pill{{display:inline-block;padding:2px 10px;border-radius:10px;font-size:10px;font-weight:600;margin:2px}}
.pill.ok{{background:#e8f5e9;color:#2e7d32}}.pill.ng{{background:#ffebee;color:#c62828}}
.bd{{background:#f8f9fa;border-radius:6px;padding:4px 10px;font-size:10px;border:1px solid var(--border);margin:2px;display:inline-block}}
.note{{background:#fff9e6;border-left:4px solid var(--gold);padding:10px 14px;border-radius:4px;font-size:12px;color:#8d6e00;line-height:1.7}}
.backup{{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;margin-top:4px}}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>福彩3D 五五分解预测系统 <span style="font-size:14px;opacity:0.7;">v{V}</span></h1><div class="sub">四分解≥1命中 | 200期100% | 推荐均值{M}%±{S}% (22窗口交叉验证)</div></div>

<div class="pred-main card">
<div class="pred-left"><div class="pred-sub">预测</div><div class="pred-issue">{P['next_issue']}</div><div class="pred-date">{P['next_date']}</div><div class="pred-sub">上期 {P['last_issue']} <b style="color:#e74c3c;">{P['last_number']}</b></div></div>
<div class="pred-center"><div class="pred-decomp"><div class="name">{P['rec_name']}</div><div class="split">{P['rec_decomp']}</div></div><div class="pred-reason">{P['reason']}</div><div class="backup">{backup_html}</div></div>
<div class="pred-right"><div class="pred-sub">本期推荐率(异常)</div><div class="acc-big2">{R['200期']}%</div><div class="pred-sub">真实均值 {M}%±{S}%</div><div class="pred-sub" style="margin-top:8px">整体保障</div><div class="acc-big">{A['200期']}%</div></div>
</div>

<div class="grid-4">{acc_cards}</div>

<div class="card">
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;"><h3 style="margin-bottom:0">200期回测（近期→远期）</h3><div><button class="btn active" id="ba" onclick="F('all')">全部</button><button class="btn" id="bf" onclick="F('fail')">仅整体失败</button></div></div>
<div id="bstats" style="margin-bottom:10px"><span class="pill ok">整体命中 <b>{B['correct_ensemble']}</b> ({B['ensemble_acc']}%)</span><span class="pill ng">整体失败 <b>{B['total']-B['correct_ensemble']}</b></span></div>
<div class="table-wrap"><table><thead><tr><th>期号</th><th>日期</th><th>开奖号</th><th>预测分解</th><th>推荐结果</th><th>整体≥1</th></tr></thead><tbody>
{rows_html}
</tbody></table></div></div>

<div class="note">策略: 每天推荐一组（上期命中则继续），四分解整体≥1命中保障。⚠ 仅供娱乐参考，理性购彩。</div>
</div>
<script>
function F(t){{document.getElementById('ba').className='btn'+(t==='all'?' active':'');document.getElementById('bf').className='btn'+(t==='fail'?' active':'');var rows=document.querySelectorAll('tbody tr');for(var i=0;i<rows.length;i++)rows[i].style.display=(t==='all'||rows[i].querySelector('td:last-child').textContent==='✗')?'':'none';}}
</script>
</body>
</html>'''

with open('五五分解预测系统.html', 'w', encoding='utf-8') as f:
    f.write(html)
# Also generate index.html for GitHub Pages
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'OK, {len(html)} chars')
