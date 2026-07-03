# AI Quant Lab — 技术指标分析工作台

基于中芯国际(688981.SH) A股日线数据的技术指标计算与分析工作台。

## 内容

| 文件 | 说明 |
|------|------|
| `indicator_analyzer_design.md` | 交互式指标分析工具设计文档 |
| `indicator_spec.md` | Notebook 技术指标计算规范 |
| `stock_data_spec.json` | 股票数据取数规范 v2.0 |
| `build_notebook.py` | Notebook 构建脚本 |
| `execute_indicators.py` | 指标批量计算脚本 |
| `fetch_stocks_multi.py` | 多股票批量取数脚本 |
| `中芯国际技术指标计算.ipynb` | Jupyter Notebook |
| `push_to_github.ps1` | 一键推送脚本 |
| `output/` | 计算结果 CSV/JSON/图表 |

## 数据源

- A 股: TuShare Pro API
- 标的: 中芯国际(688981.SH), 比亚迪(002594.SZ), 长江电力(600900.SH)
- 周期: 2025-07-02 ~ 2026-07-02 (近1年)

## 技术指标

- **趋势类**: SMA, EMA, MACD, 布林带
- **动量振荡类**: RSI, KDJ, 威廉指标, 乖离率
- **量价类**: VOL_MA, 量比, MFI
- **波动率类**: ATR

## 使用方法

```bash
# 批量取数
python fetch_stocks_multi.py

# 计算全部指标
python execute_indicators.py

# 设置 GitHub Token 后推送
.\push_to_github.ps1
```
