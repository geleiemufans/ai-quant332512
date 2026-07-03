#!/usr/bin/env python3
"""Generate 中芯国际技术指标计算.ipynb"""
import json, os, textwrap

NB_DIR = "C:/Users/Administrator/Desktop/北大ppt/北京大学量化学习/task02_indicator_lab"
DATA_PATH = "C:/Users/Administrator/Desktop/北大ppt/北京大学量化学习/task2/output/688981_SH_daily.csv"
os.makedirs(NB_DIR, exist_ok=True)

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}

def py(code):
    return {"cell_type": "code", "metadata": {}, "source": code, "outputs": [], "execution_count": None}

# Build all cells
cells = []

# C1: Title
cells.append(md([
    "# 中芯国际(688981.SH) A股 技术指标计算\n",
    "\n",
    "## 项目概览\n",
    "\n",
    "- **标的**: 中芯国际集成电路制造有限公司 (688981.SH)\n",
    "- **行业**: 半导体 (科创板)\n",
    "- **数据周期**: 2025-07-02 ~ 2026-07-02 (近1年)\n",
    "- **数据源**: TuShare Pro API\n",
    "- **指标**: 趋势类 + 动量振荡类 + 量价类 + 波动率类 共12种\n",
    "- **方法**: 全部指标使用 Python 手写实现, 不依赖 talib 等黑盒库\n",
    "\n",
    "## 指标清单\n",
    "\n",
    "| # | 类别 | 指标 | 缩写 | 参数 |\n",
    "|---|------|------|------|------|\n",
    "| 1 | 趋势 | 简单移动平均 | SMA | 5/10/20/60日 |\n",
    "| 2 | 趋势 | 指数移动平均 | EMA | 12/26日 |\n",
    "| 3 | 趋势 | 平滑异同移动平均 | MACD | 12,26,9 |\n",
    "| 4 | 趋势 | 布林带 | BOLL | 20日, 2sigma |\n",
    "| 5 | 动量 | 相对强弱指标 | RSI | 6/14日 |\n",
    "| 6 | 动量 | 随机指标 | KDJ | 9,3,3 |\n",
    "| 7 | 动量 | 威廉指标 | W%25R | 14日 |\n",
    "| 8 | 动量 | 乖离率 | BIAS | 5/10日 |\n",
    "| 9 | 量价 | 成交量均线 | VOL_MA | 5/20日 |\n",
    "| 10 | 量价 | 量比 | VOL_RATIO | -- |\n",
    "| 11 | 量价 | 资金流向指标 | MFI | 14日 |\n",
    "| 12 | 波动率 | 平均真实波幅 | ATR | 14日 |\n"
]))

# C2: Imports
cells.append(py([
    "# Cell 2: 环境准备 -- 导入依赖库\n",
    "import pandas as pd\n",
    "import numpy as np\n",
    "import matplotlib\n",
    "matplotlib.use('Agg')\n",
    "import matplotlib.pyplot as plt\n",
    "import matplotlib.dates as mdates\n",
    "import warnings\n",
    "warnings.filterwarnings('ignore')\n",
    "\n",
    "plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']\n",
    "plt.rcParams['axes.unicode_minus'] = False\n",
    "plt.rcParams['figure.dpi'] = 120\n",
    "plt.rcParams['figure.figsize'] = (14, 6)\n",
    '\nprint("✅ 环境准备完成")\n',
    'print(f"   pandas: {pd.__version__}")\n',
    'print(f"   numpy:  {np.__version__}")\n',
    'print(f"   matplotlib: {matplotlib.__version__}")\n'
]))

# C3: Data Loading
cells.append(md([
    "## 数据加载\n",
    "\n",
    "从 task2 的输出目录读取中芯国际 A 股日线数据。\n",
    "字段包括: trade_date(交易日), open/high/low/close(价格), vol(成交量,手), amount(成交额,元), pct_chg(涨跌幅,%)\n"
]))

cells.append(py([
    '# Cell 3: 读取数据\n',
    f"df = pd.read_csv(r'{DATA_PATH}', encoding='utf-8-sig')\n",
    "df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')\n",
    "df = df.sort_values('trade_date').reset_index(drop=True)\n",
    "df.index = pd.RangeIndex(len(df))\n",
    'print(f"✅ 数据加载完毕: {len(df)} 条记录")\n',
    'print(f"   日期范围: {df[\'trade_date\'].min().date()} ~ {df[\'trade_date\'].max().date()}")\n'
]))

# C4: Data Exploration
cells.append(md(["## 数据探查\n", "\n查看数据的基本信息、统计摘要, 检查缺失值。\n"]))

cells.append(py([
    '# Cell 4: 数据探查\n',
    'print("数据基本信息:")\n',
    'print(f"列名: {list(df.columns)}")\n',
    'print(f"\\n缺失值统计:\\n{df.isnull().sum()}")\n',
    'desc = df[["open","high","low","close","vol","amount","pct_chg"]].describe()\n',
    'print("\\n描述性统计:")\n',
    'print(desc.round(2))\n',
    'print(f"\\n总交易日: {len(df)} 天")\n',
    'print(f"日均成交量: {df[\'vol\'].mean()/10000:.2f} 万手")\n'
]))

# C5: SMA / EMA
cells.append(md([
    "---\n",
    "## 5. 趋势指标: 移动平均线\n",
    "\n",
    "### 5.1 简单移动平均线 (SMA)\n",
    "\n",
    "SMA(n) = (P1 + P2 + ... + Pn) / n\n",
    "\n",
    "### 5.2 指数移动平均线 (EMA)\n",
    "\n",
    "EMA(t) = P(t) x alpha + EMA(t-1) x (1-alpha),  alpha = 2 / (n + 1)\n",
    "\n",
    "EMA 对近期价格赋予更高权重, 反应更快。\n",
    "- SMA5 / SMA10: 短期趋势\n",
    "- SMA20 / SMA60: 中期趋势\n",
    "- EMA12 / EMA26: MACD 基础\n"
]))

cells.append(py([
    "# Cell 5: 计算移动平均线\n",
    "\n",
    "# SMA\n",
    "df['SMA5'] = df['close'].rolling(window=5).mean()\n",
    "df['SMA10'] = df['close'].rolling(window=10).mean()\n",
    "df['SMA20'] = df['close'].rolling(window=20).mean()\n",
    "df['SMA60'] = df['close'].rolling(window=60).mean()\n",
    "\n",
    "# EMA\n",
    "def ema(series, period):\n",
    "    alpha = 2 / (period + 1)\n",
    "    result = series.copy()\n",
    "    first_valid = series.iloc[:period].mean()\n",
    "    result.iloc[period-1] = first_valid\n",
    "    for i in range(period, len(series)):\n",
    "        result.iloc[i] = series.iloc[i] * alpha + result.iloc[i-1] * (1 - alpha)\n",
    "    result.iloc[:period-1] = np.nan\n",
    "    return result\n",
    "\n",
    "df['EMA12'] = ema(df['close'], 12)\n",
    "df['EMA26'] = ema(df['close'], 26)\n",
    "\n",
    'print(f"SMA5={df[\'SMA5\'].iloc[-1]:.2f}, SMA20={df[\'SMA20\'].iloc[-1]:.2f}")\n',
    'print(f"EMA12={df[\'EMA12\'].iloc[-1]:.2f}, EMA26={df[\'EMA26\'].iloc[-1]:.2f}")\n',
    "\n",
    "# 均线交叉信号\n",
    "df['golden_cross'] = (df['SMA5'] > df['SMA20']) & (df['SMA5'].shift(1) <= df['SMA20'].shift(1))\n",
    "df['death_cross'] = (df['SMA5'] < df['SMA20']) & (df['SMA5'].shift(1) >= df['SMA20'].shift(1))\n",
    'print(f"金叉: {df[\'golden_cross\'].sum()}次, 死叉: {df[\'death_cross\'].sum()}次")\n'
]))

# C6: MACD
cells.append(md([
    "---\n",
    "## 6. MACD (平滑异同移动平均线)\n",
    "\n",
    "DIF = EMA12 - EMA26\n",
    "DEA = DIF 的 9 日 EMA\n",
    "MACD柱 = 2 x (DIF - DEA)\n",
    "\n",
    "解读: DIF > DEA -> 多头(红柱); DIF < DEA -> 空头(绿柱)\n"
]))

cells.append(py([
    "# Cell 6: MACD 计算\n",
    "df['DIF'] = df['EMA12'] - df['EMA26']\n",
    "df['DEA'] = ema(df['DIF'], 9)\n",
    "df['MACD'] = 2 * (df['DIF'] - df['DEA'])\n",
    '\nprint(f"DIF={df["DIF"].iloc[-1]:.4f}, DEA={df["DEA"].iloc[-1]:.4f}")\n',
    'if df["DIF"].iloc[-1] > df["DEA"].iloc[-1]:\n',
    '    print("信号: 多头 (DIF > DEA)")\n',
    'else:\n',
    '    print("信号: 空头 (DIF < DEA)")\n'
]))

# C7: Bollinger Bands
cells.append(md([
    "---\n",
    "## 7. 布林带 (Bollinger Bands)\n",
    "\n",
    "中轨 = SMA(20)\n",
    "上轨 = 中轨 + 2 x std(20)\n",
    "下轨 = 中轨 - 2 x std(20)\n",
    "\n",
    "带宽 = (上轨 - 下轨) / 中轨\n",
    "带宽收窄 -> 变盘信号, 带宽扩大 -> 趋势确立\n"
]))

cells.append(py([
    "# Cell 7: 布林带计算\n",
    "df['BOLL_MID'] = df['SMA20']\n",
    "df['BOLL_STD'] = df['close'].rolling(window=20).std()\n",
    "df['BOLL_UP'] = df['BOLL_MID'] + 2 * df['BOLL_STD']\n",
    "df['BOLL_DN'] = df['BOLL_MID'] - 2 * df['BOLL_STD']\n",
    "df['BOLL_WIDTH'] = (df['BOLL_UP'] - df['BOLL_DN']) / df['BOLL_MID'] * 100\n",
    "\n",
    'close_now = df["close"].iloc[-1]\n',
    'print(f"上轨={df["BOLL_UP"].iloc[-1]:.2f}, 中轨={df["BOLL_MID"].iloc[-1]:.2f}, 下轨={df["BOLL_DN"].iloc[-1]:.2f}")\n',
    'pos = (close_now - df["BOLL_DN"].iloc[-1]) / (df["BOLL_UP"].iloc[-1] - df["BOLL_DN"].iloc[-1]) * 100\n',
    'print(f"当前位置: 布林带 {pos:.1f}% 分位")\n'
]))

# C8: RSI
cells.append(md([
    "---\n",
    "## 8. RSI (相对强弱指标)\n",
    "\n",
    "RS = n日平均上涨 / n日平均下跌\n",
    "RSI = 100 - 100 / (1 + RS)\n",
    "\n",
    "RSI > 70 -> 超买, 可能回调\n",
    "RSI < 30 -> 超卖, 可能反弹\n"
]))

cells.append(py([
    "# Cell 8: RSI 计算\n",
    "def calc_rsi(series, period):\n",
    "    delta = series.diff()\n",
    "    gain = delta.clip(lower=0)\n",
    "    loss = (-delta).clip(lower=0)\n",
    "    avg_gain = gain.rolling(window=period).mean()\n",
    "    avg_loss = loss.rolling(window=period).mean()\n",
    "    rs = avg_gain / avg_loss\n",
    "    return 100 - (100 / (1 + rs))\n",
    "\n",
    "df['RSI6'] = calc_rsi(df['close'], 6)\n",
    "df['RSI14'] = calc_rsi(df['close'], 14)\n",
    '\nprint(f"RSI6={df["RSI6"].iloc[-1]:.1f}, RSI14={df["RSI14"].iloc[-1]:.1f}")\n',
    'if df["RSI14"].iloc[-1] > 70:\n',
    '    print("RSI14 > 70, 超买区域")\n',
    'elif df["RSI14"].iloc[-1] < 30:\n',
    '    print("RSI14 < 30, 超卖区域")\n',
    'else:\n',
    '    print("RSI14 中性区间")\n'
]))

# C9: KDJ
cells.append(md([
    "---\n",
    "## 9. KDJ (随机指标)\n",
    "\n",
    "RSV = (Close - Ln) / (Hn - Ln) x 100\n",
    "Kt = (2/3)Kt-1 + (1/3)RSVt\n",
    "Dt = (2/3)Dt-1 + (1/3)Kt\n",
    "Jt = 3Kt - 2Dt\n",
    "\n",
    "K > D -> 看涨; K,D > 80 -> 超买; K,D < 20 -> 超卖\n"
]))

cells.append(py([
    "# Cell 9: KDJ 计算\n",
    "def calc_kdj(df, n=9, k_smooth=3, d_smooth=3):\n",
    "    low_n = df['low'].rolling(window=n).min()\n",
    "    high_n = df['high'].rolling(window=n).max()\n",
    "    rsv = (df['close'] - low_n) / (high_n - low_n) * 100\n",
    "    rsv = rsv.fillna(50)\n",
    "    k = pd.Series(index=df.index, dtype=float); k.iloc[0] = 50\n",
    "    d = pd.Series(index=df.index, dtype=float); d.iloc[0] = 50\n",
    "    for i in range(1, len(df)):\n",
    "        k.iloc[i] = (k_smooth-1)/k_smooth*k.iloc[i-1] + (1/k_smooth)*rsv.iloc[i]\n",
    "        d.iloc[i] = (d_smooth-1)/d_smooth*d.iloc[i-1] + (1/d_smooth)*k.iloc[i]\n",
    "    j = 3*k - 2*d\n",
    "    return rsv, k, d, j\n",
    "\n",
    "df['RSV'], df['K'], df['D'], df['J'] = calc_kdj(df)\n",
    'print(f"K={df["K"].iloc[-1]:.1f}, D={df["D"].iloc[-1]:.1f}, J={df["J"].iloc[-1]:.1f}")\n'
]))

# C10: W%R + BIAS
cells.append(md([
    "---\n",
    "## 10. 威廉指标 (W%25R) & 乖离率 (BIAS)\n",
    "\n",
    "W%25R = (Hn - Close) / (Hn - Ln) x (-100)\n",
    "BIAS(n) = (Close - SMA(n)) / SMA(n) x 100%25\n",
    "\n",
    "W%25R > -20 -> 超买; W%25R < -80 -> 超卖\n",
    "BIAS(5) > 5%25 -> 短期超买; BIAS(5) < -5%25 -> 短期超卖\n"
]))

cells.append(py([
    "# Cell 10: 威廉指标 + 乖离率\n",
    "def calc_wr(df, n=14):\n",
    "    h_n = df['high'].rolling(n).max()\n",
    "    l_n = df['low'].rolling(n).min()\n",
    "    return (h_n - df['close']) / (h_n - l_n) * (-100)\n",
    "\n",
    "df['WR'] = calc_wr(df, 14)\n",
    "df['BIAS5'] = (df['close'] - df['SMA5']) / df['SMA5'] * 100\n",
    "df['BIAS10'] = (df['close'] - df['SMA10']) / df['SMA10'] * 100\n",
    '\nprint(f"威廉指标 W%R(14)={df["WR"].iloc[-1]:.1f}")\n',
    'print(f"BIAS5={df["BIAS5"].iloc[-1]:.2f}%%, BIAS10={df["BIAS10"].iloc[-1]:.2f}%%")\n'
]))

# C11: Volume indicators
cells.append(md([
    "---\n",
    "## 11. 量价指标\n",
    "\n",
    "VOL_MA5/VOL_MA20: 成交量的短期和中期均线\n",
    "量比 = 当日成交量 / 前5日平均成交量 (>1.5放量, <0.5缩量)\n",
    "MFI(资金流向指标): 类似 RSI 但引入成交量, >80超买, <20超卖\n"
]))

cells.append(py([
    "# Cell 11: 量价指标\n",
    "df['VOL_MA5'] = df['vol'].rolling(window=5).mean()\n",
    "df['VOL_MA20'] = df['vol'].rolling(window=20).mean()\n",
    "df['VOL_RATIO'] = df['vol'] / df['vol'].rolling(window=5).mean()\n",
    "\n",
    "def calc_mfi(df, period=14):\n",
    "    tp = (df['high'] + df['low'] + df['close']) / 3\n",
    "    mf = tp * df['vol']\n",
    "    pos = mf.where(tp > tp.shift(1), 0)\n",
    "    neg = mf.where(tp < tp.shift(1), 0)\n",
    "    mfr = pos.rolling(period).sum() / neg.rolling(period).sum().replace(0, np.nan)\n",
    "    return 100 - (100 / (1 + mfr))\n",
    "\n",
    "df['MFI'] = calc_mfi(df, 14)\n",
    'print(f"量比={df["VOL_RATIO"].iloc[-1]:.2f}, MFI={df["MFI"].iloc[-1]:.1f}")\n'
]))

# C12: ATR
cells.append(md([
    "---\n",
    "## 12. ATR (平均真实波幅)\n",
    "\n",
    "TR = max(High-Low, |High-PrevClose|, |Low-PrevClose|)\n",
    "ATR(n) = TR的n日移动平均\n",
    "\n",
    "ATR越大 -> 波动越剧烈。用于止损设置(如2xATR)和仓位管理。\n"
]))

cells.append(py([
    "# Cell 12: ATR 计算\n",
    "def calc_atr(df, period=14):\n",
    "    tr = pd.Series(index=df.index, dtype=float)\n",
    "    for i in range(1, len(df)):\n",
    "        tr.iloc[i] = max(\n",
    "            df['high'].iloc[i] - df['low'].iloc[i],\n",
    "            abs(df['high'].iloc[i] - df['close'].iloc[i-1]),\n",
    "            abs(df['low'].iloc[i] - df['close'].iloc[i-1])\n",
    "        )\n",
    "    return tr, tr.rolling(window=period).mean()\n",
    "\n",
    "df['TR'], df['ATR14'] = calc_atr(df, 14)\n",
    'atr_pct = df["ATR14"].iloc[-1] / df["close"].iloc[-1] * 100\n',
    'print(f"ATR14={df["ATR14"].iloc[-1]:.2f}, ATR/Close={atr_pct:.2f}%%")\n',
    'print(f"建议止损(2xATR)={2*df["ATR14"].iloc[-1]:.2f}")\n'
]))

# C13: Visualization
cells.append(md([
    "---\n",
    "## 13. 多指标综合可视化\n",
    "\n",
    "将前12个指标整合为 9 个子图的综合看板, 完整展现技术面全貌。\n"
]))

cells.append(py([
    "# Cell 13: 综合看板 -- 9子图\n",
    "# 取最近120个交易日 (约半年)\n",
    "plot_df = df.tail(120).copy()\n",
    "dates = plot_df['trade_date']\n",
    "\n",
    "fig = plt.figure(figsize=(16, 22))\n",
    "gs = fig.add_gridspec(9, 1, hspace=0.35, height_ratios=[2.2, 0.8, 1.2, 1, 1, 1, 1, 1, 0.8])\n",
    "\n",
    "# Subplot 1: 价格 + SMA\n",
    "ax1 = fig.add_subplot(gs[0])\n",
    "ax1.plot(dates, plot_df['close'], color='#333', lw=1.8, label='收盘价')\n",
    "ax1.plot(dates, plot_df['SMA5'], color='#e24b4a', lw=1, alpha=0.8, label='SMA5')\n",
    "ax1.plot(dates, plot_df['SMA20'], color='#378add', lw=1, alpha=0.8, label='SMA20')\n",
    "ax1.plot(dates, plot_df['SMA60'], color='#1d9e75', lw=1, alpha=0.8, label='SMA60')\n",
    "golden = plot_df[plot_df['golden_cross']]\n",
    "death = plot_df[plot_df['death_cross']]\n",
    "ax1.scatter(golden['trade_date'], golden['close'], color='red', marker='^', s=80, zorder=5, label='金叉')\n",
    "ax1.scatter(death['trade_date'], death['close'], color='green', marker='v', s=80, zorder=5, label='死叉')\n",
    "ax1.set_title('中芯国际(688981.SH) 收盘价 + 均线', fontsize=13, fontweight='bold')\n",
    "ax1.legend(ncol=6, fontsize=9, loc='upper left')\n",
    "ax1.grid(True, alpha=0.2)\n",
    "ax1.tick_params(labelbottom=False)\n",
    "\n",
    "# Subplot 2: 成交量\n",
    "ax2 = fig.add_subplot(gs[1])\n",
    "vol_colors = ['#e24b4a' if v >= 0 else '#1d9e75' for v in plot_df['pct_chg'].fillna(0)]\n",
    "ax2.bar(dates, plot_df['vol']/10000, color=vol_colors, alpha=0.6, width=0.7)\n",
    "ax2.plot(dates, plot_df['VOL_MA5']/10000, color='orange', lw=1, label='VOL_MA5')\n",
    "ax2.plot(dates, plot_df['VOL_MA20']/10000, color='purple', lw=1, label='VOL_MA20')\n",
    "ax2.set_ylabel('成交量 (万手)', fontsize=11)\n",
    "ax2.legend(fontsize=9, loc='upper left')\n",
    "ax2.grid(True, alpha=0.2)\n",
    "ax2.tick_params(labelbottom=False)\n",
    "\n",
    "# Subplot 3: MACD\n",
    "ax3 = fig.add_subplot(gs[2])\n",
    "macd_colors = ['#e24b4a' if v >= 0 else '#1d9e75' for v in plot_df['MACD'].fillna(0)]\n",
    "ax3.bar(dates, plot_df['MACD'].fillna(0), color=macd_colors, alpha=0.6, width=0.7)\n",
    "ax3.plot(dates, plot_df['DIF'], color='#333', lw=1.2, label='DIF')\n",
    "ax3.plot(dates, plot_df['DEA'], color='orange', lw=1.2, label='DEA')\n",
    "ax3.axhline(y=0, color='gray', lw=0.5, linestyle='--')\n",
    "ax3.set_title('MACD', fontsize=12, fontweight='bold')\n",
    "ax3.legend(fontsize=9, loc='upper left')\n",
    "ax3.grid(True, alpha=0.2)\n",
    "ax3.tick_params(labelbottom=False)\n",
    "\n",
    "# Subplot 4: Bollinger\n",
    "ax4 = fig.add_subplot(gs[3])\n",
    "ax4.plot(dates, plot_df['close'], color='#333', lw=1.5, label='收盘价')\n",
    "ax4.plot(dates, plot_df['BOLL_MID'], color='blue', lw=1, alpha=0.7, label='中轨')\n",
    "ax4.plot(dates, plot_df['BOLL_UP'], color='gray', lw=0.8, alpha=0.5, label='上轨')\n",
    "ax4.plot(dates, plot_df['BOLL_DN'], color='gray', lw=0.8, alpha=0.5, label='下轨')\n",
    "ax4.fill_between(dates, plot_df['BOLL_UP'], plot_df['BOLL_DN'], alpha=0.08, color='blue')\n",
    "ax4.set_title('布林带 (20, 2sigma)', fontsize=12, fontweight='bold')\n",
    "ax4.legend(fontsize=9, loc='upper left')\n",
    "ax4.grid(True, alpha=0.2)\n",
    "ax4.tick_params(labelbottom=False)\n",
    "\n",
    "# Subplot 5: RSI\n",
    "ax5 = fig.add_subplot(gs[4])\n",
    "ax5.plot(dates, plot_df['RSI6'], color='#e24b4a', lw=1, alpha=0.6, label='RSI(6)')\n",
    "ax5.plot(dates, plot_df['RSI14'], color='#378add', lw=1.2, label='RSI(14)')\n",
    "ax5.axhline(y=70, color='red', lw=0.8, linestyle='--', alpha=0.5)\n",
    "ax5.axhline(y=30, color='green', lw=0.8, linestyle='--', alpha=0.5)\n",
    "ax5.fill_between(dates, 70, 100, alpha=0.08, color='red')\n",
    "ax5.fill_between(dates, 0, 30, alpha=0.08, color='green')\n",
    "ax5.set_ylim(0, 100)\n",
    "ax5.set_title('RSI', fontsize=12, fontweight='bold')\n",
    "ax5.legend(fontsize=9, loc='upper left')\n",
    "ax5.grid(True, alpha=0.2)\n",
    "ax5.tick_params(labelbottom=False)\n",
    "\n",
    "# Subplot 6: KDJ\n",
    "ax6 = fig.add_subplot(gs[5])\n",
    "ax6.plot(dates, plot_df['K'], color='#e24b4a', lw=1, label='K')\n",
    "ax6.plot(dates, plot_df['D'], color='#378add', lw=1, label='D')\n",
    "ax6.plot(dates, plot_df['J'], color='green', lw=0.8, alpha=0.5, label='J')\n",
    "ax6.axhline(y=80, color='red', lw=0.8, linestyle='--', alpha=0.4)\n",
    "ax6.axhline(y=20, color='green', lw=0.8, linestyle='--', alpha=0.4)\n",
    "ax6.set_ylim(0, 100)\n",
    "ax6.set_title('KDJ', fontsize=12, fontweight='bold')\n",
    "ax6.legend(fontsize=9, loc='upper left')\n",
    "ax6.grid(True, alpha=0.2)\n",
    "ax6.tick_params(labelbottom=False)\n",
    "\n",
    "# Subplot 7: Williams %R\n",
    "ax7 = fig.add_subplot(gs[6])\n",
    "ax7.plot(dates, plot_df['WR'], color='purple', lw=1.2, label='W%R(14)')\n",
    "ax7.axhline(y=-20, color='red', lw=0.8, linestyle='--', alpha=0.5)\n",
    "ax7.axhline(y=-80, color='green', lw=0.8, linestyle='--', alpha=0.5)\n",
    "ax7.set_title('威廉指标 W%R', fontsize=12, fontweight='bold')\n",
    "ax7.legend(fontsize=9, loc='upper left')\n",
    "ax7.grid(True, alpha=0.2)\n",
    "ax7.tick_params(labelbottom=False)\n",
    "\n",
    "# Subplot 8: BIAS\n",
    "ax8 = fig.add_subplot(gs[7])\n",
    "ax8.plot(dates, plot_df['BIAS5'], color='#e24b4a', lw=1, label='BIAS(5)')\n",
    "ax8.plot(dates, plot_df['BIAS10'], color='#378add', lw=1, label='BIAS(10)')\n",
    "ax8.axhline(y=5, color='red', lw=0.8, linestyle='--', alpha=0.4)\n",
    "ax8.axhline(y=-5, color='green', lw=0.8, linestyle='--', alpha=0.4)\n",
    "ax8.set_title('乖离率 BIAS', fontsize=12, fontweight='bold')\n",
    "ax8.legend(fontsize=9, loc='upper left')\n",
    "ax8.grid(True, alpha=0.2)\n",
    "ax8.tick_params(labelbottom=False)\n",
    "\n",
    "# Subplot 9: ATR\n",
    "ax9 = fig.add_subplot(gs[8])\n",
    "ax9.bar(dates, plot_df['ATR14'].fillna(0), color='orange', alpha=0.7, width=0.7)\n",
    "ax9.set_title('ATR(14) 平均真实波幅', fontsize=12, fontweight='bold')\n",
    "ax9.set_xlabel('交易日', fontsize=11)\n",
    "ax9.grid(True, alpha=0.2)\n",
    "ax9.tick_params(axis='x', rotation=45)\n",
    "\n",
    "for ax in [ax1,ax2,ax3,ax4,ax5,ax6,ax7,ax8]:\n",
    "    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))\n",
    "    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))\n",
    "\n",
    "fig_path = os.path.join(r'" + NB_DIR + r"', 'smic_indicators_dashboard.png')\n",
    "plt.savefig(fig_path, dpi=150, bbox_inches='tight', facecolor='white')\n",
    "plt.close()\n",
    'print(f"✅ 综合看板已保存: {fig_path}")\n'
]))

# C14: Summary
cells.append(md([
    "---\n",
    "## 14. 技术面综合摘要\n",
    "\n",
    "基于上述12种指标的计算结果, 汇总当前中芯国际的技术面状态。\n"
]))

cells.append(py([
    "# Cell 14: 技术面综合摘要\n",
    'print("=" * 50)\n',
    'print("中芯国际(688981.SH) 技术面综合摘要")\n',
    'print(f"数据截至: {df[\'trade_date\'].iloc[-1].date()}")\n',
    'print(f"最新收盘价: {df[\'close\'].iloc[-1]:.2f}")\n',
    'print("=" * 50)\n',
    "\n",
    '# 趋势\n',
    'sma5, sma20, sma60 = df["SMA5"].iloc[-1], df["SMA20"].iloc[-1], df["SMA60"].iloc[-1]\n',
    'print(f"\\n趋势: SMA5={sma5:.1f}, SMA20={sma20:.1f}, SMA60={sma60:.1f}")\n',
    'if sma5 > sma20 > sma60:\n',
    '    print("  均线多头排列 (SMA5 > SMA20 > SMA60)")\n',
    'elif sma5 < sma20 < sma60:\n',
    '    print("  均线空头排列 (SMA5 < SMA20 < SMA60)")\n',
    'else:\n',
    '    print("  均线交叉状态")\n',
    "\n",
    '# MACD\n',
    'print(f"\\nMACD: DIF={df["DIF"].iloc[-1]:.2f}, DEA={df["DEA"].iloc[-1]:.2f}")\n',
    'print(f"  信号: {"多头" if df["DIF"].iloc[-1] > df["DEA"].iloc[-1] else "空头"}")\n',
    "\n",
    '# RSI\n',
    'print(f"\\nRSI(14)={df["RSI14"].iloc[-1]:.1f}")\n',
    '# KDJ\n',
    'print(f"KDJ: K={df["K"].iloc[-1]:.1f}, D={df["D"].iloc[-1]:.1f}")\n',
    "\n",
    '# 量价\n',
    'print(f"\\n量比={df["VOL_RATIO"].iloc[-1]:.2f}, MFI={df["MFI"].iloc[-1]:.1f}")\n',
    "\n",
    '# ATR\n',
    'atr_pct = df["ATR14"].iloc[-1] / df["close"].iloc[-1] * 100\n',
    'print(f"\\nATR(14)={df["ATR14"].iloc[-1]:.2f} ({atr_pct:.2f}% of close)")\n'
]))

# Build notebook JSON
notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.13.0"}
    },
    "cells": cells
}

nb_path = os.path.join(NB_DIR, "中芯国际技术指标计算.ipynb")
with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"✅ Notebook 生成完毕: {nb_path}")
print(f"   共 {len(cells)} 个 Cell")
print(f"   Markdown: {sum(1 for c in cells if c['cell_type']=='markdown')}")
print(f"   Code: {sum(1 for c in cells if c['cell_type']=='code')}")
