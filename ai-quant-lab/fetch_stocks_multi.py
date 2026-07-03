#!/usr/bin/env python3
"""
fetch_stocks_multi.py — 批量股票取数脚本 v2.0
A股: TuShare Pro API (Python SDK)
港股: yfinance
输出: CSV + quality_report.json + stock_data_package.json
"""
import os, csv, json, warnings, datetime
warnings.filterwarnings("ignore")

OUT = "C:/Users/Administrator/Desktop/北大ppt/北京大学量化学习/task2/output"
os.makedirs(OUT, exist_ok=True)

TOKEN = "63d468bc71482999401f4ee00dc43bfdaf3ccae82c31d0897ac9e51c"
START = "20250702"
END   = "20260702"
TODAY = "2026-07-02"

# ═══════ 配置 ═══════
STOCKS_A = ["688981.SH", "002594.SZ", "600900.SH"]
HK_CODES = ["0981.HK", "1211.HK"]
NAMES = {
    "688981.SH":"中芯国际","002594.SZ":"比亚迪","600900.SH":"长江电力",
    "0981.HK":"中芯国际-H","1211.HK":"比亚迪股份-H"
}

# ═══════ Phase 1: A股 (TuShare) ═══════
print("=" * 55)
print("📥 Phase 1: A股数据 (TuShare Pro API)")
print("=" * 55)

import tushare as ts
pro = ts.pro_api(TOKEN)

a_data = {}
for code in STOCKS_A:
    try:
        df = pro.daily(ts_code=code, start_date=START, end_date=END)
        if df is None or df.empty:
            print(f"  ⚠ {code}: no data")
            continue
        # sort by trade_date ascending
        df = df.sort_values("trade_date")
        
        # Save CSV
        csv_path = os.path.join(OUT, f"{code.replace('.','_')}_daily.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"  ✅ {code} ({NAMES[code]}): {len(df)}条 → {code.replace('.','_')}_daily.csv")
        
        # Save JSON
        records = df.to_dict(orient="records")
        json_path = os.path.join(OUT, f"{code.replace('.','_')}_daily.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        a_data[code] = records
    except Exception as e:
        print(f"  ❌ {code}: {e}")

# ═══════ Phase 2: 港股 (yfinance) ═══════
print("\n" + "=" * 55)
print("📥 Phase 2: 港股数据 (yfinance)")
print("=" * 55)

import yfinance as yf

hk_data = {}
for code in HK_CODES:
    try:
        ticker = yf.Ticker(code)
        hist = ticker.history(start="2025-07-02", end="2026-07-02")
        if hist.empty:
            print(f"  ⚠ {code}: empty data")
            continue
        # Save CSV
        csv_path = os.path.join(OUT, f"{code.replace('.','_')}_daily.csv")
        hist.to_csv(csv_path, encoding="utf-8-sig")
        print(f"  ✅ {code} ({NAMES[code]}): {len(hist)}条 → {code.replace('.','_')}_daily.csv")
        
        # Save JSON
        records = []
        for idx, row in hist.iterrows():
            records.append({
                "trade_date": idx.strftime("%Y%m%d"),
                "open": round(row["Open"],2), "high": round(row["High"],2),
                "low": round(row["Low"],2), "close": round(row["Close"],2),
                "adj_close": round(row["Adj Close"],2), "vol": int(row["Volume"])
            })
        json_path = os.path.join(OUT, f"{code.replace('.','_')}_daily.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        hk_data[code] = records
    except Exception as e:
        print(f"  ❌ {code}: {e}")

# ═══════ Phase 3: 质量报告 ═══════
print("\n" + "=" * 55)
print("📊 Phase 3: 数据质量报告")
print("=" * 55)

qr = {"report_date": TODAY, "spec_version": "2.0", "stocks": {}}

all_stocks = a_data | hk_data
for code, records in all_stocks.items():
    if not records:
        continue
    name = NAMES.get(code, code)
    n = len(records)
    
    # 简单检查
    closes = [r.get("close", 0) for r in records]
    vols = [r.get("vol", 0) for r in records]
    min_c, max_c = min(closes), max(closes)
    avg_c = round(sum(closes)/n, 2)
    
    # 跳空检测
    gaps = []
    for i in range(1, n):
        prev = records[i-1].get("close", 0)
        curr = records[i].get("close", 0)
        if prev == 0: continue
        pct = abs(curr - prev) / prev * 100
        if pct > 15:
            gaps.append({"date": records[i].get("trade_date",""), "pct": round(pct,2)})
    
    report = {
        "name": name,
        "market": "港股" if "HK" in code else "A股",
        "record_count": n,
        "date_range": {
            "start": records[-1].get("trade_date",""),
            "end": records[0].get("trade_date","")
        },
        "completeness": "PASS" if n >= 220 else "WARN",
        "price_range": {"min": min_c, "max": max_c, "avg": avg_c},
        "gap_detection": {"count": len(gaps), "details": gaps[:5]}
    }
    qr["stocks"][code] = report
    
    status = "✅" if report["completeness"] == "PASS" else "⚠️"
    print(f"  {status} {code} {name}: {n}条, 跳空={len(gaps)}处")

with open(os.path.join(OUT, "quality_report.json"), "w", encoding="utf-8") as f:
    json.dump(qr, f, ensure_ascii=False, indent=2)
print(f"  📄 质量报告 → quality_report.json")

# ═══════ Phase 4: 统一数据包 ═══════
print("\n" + "=" * 55)
print("📦 Phase 4: 统一JSON数据包")
print("=" * 55)

pkg = {
    "metadata": {
        "package_name": "stock_data_package",
        "spec_version": "2.0",
        "created": TODAY,
        "data_sources": {"A股": "TuShare Pro", "港股": "yfinance"}
    },
    "stocks": {},
    "summary": {}
}

for code, records in all_stocks.items():
    if not records:
        continue
    name = NAMES.get(code, code)
    market = "港股" if "HK" in code else "A股"
    
    pkg["stocks"][code] = {
        "name": name, "market": market,
        "records": records,
        "record_count": len(records)
    }
    pkg["summary"][code] = {
        "name": name, "record_count": len(records), "market": market
    }

pkg["summary"]["total_stocks"] = len(pkg["stocks"])
pkg["summary"]["total_records"] = sum(s["record_count"] for s in pkg["stocks"].values())

pkg_path = os.path.join(OUT, "stock_data_package.json")
with open(pkg_path, "w", encoding="utf-8") as f:
    json.dump(pkg, f, ensure_ascii=False, indent=2)
print(f"  📦 数据包 → stock_data_package.json")
print(f"     共 {pkg['summary']['total_stocks']} 只, {pkg['summary']['total_records']} 条记录")

print("\n" + "=" * 55)
print("✅ 全部取数完成！")
print("=" * 55)
