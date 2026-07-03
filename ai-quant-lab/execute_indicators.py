#!/usr/bin/env python3
"""
中芯国际技术指标计算 — 完整执行脚本
参照 task02_indicator_lab/indicator_spec.md 实现
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os, json, warnings, textwrap
warnings.filterwarnings('ignore')

# ═══ 路径配置 ═══
DATA_PATH = "C:/Users/Administrator/Desktop/北大ppt/北京大学量化学习/task2/output/688981_SH_daily.csv"
OUT_DIR = "C:/Users/Administrator/Desktop/北大ppt/北京大学量化学习/task02_indicator_lab/output"
NB_DIR = "C:/Users/Administrator/Desktop/北大ppt/北京大学量化学习/task02_indicator_lab"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120

# ═══ 1. 数据加载 ═══
print("=" * 55)
print("📥 1. 数据加载")
print("=" * 55)
df = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
df = df.sort_values('trade_date').reset_index(drop=True)
print(f"共 {len(df)} 条, {df['trade_date'].min().date()} ~ {df['trade_date'].max().date()}")

# ==================== 指标计算 ====================

# ═══ 2. SMA ═══
print("\n📈 2. 趋势指标: SMA/EMA")
df['SMA5'] = df['close'].rolling(5).mean()
df['SMA10'] = df['close'].rolling(10).mean()
df['SMA20'] = df['close'].rolling(20).mean()
df['SMA60'] = df['close'].rolling(60).mean()

def ema(series, period):
    alpha = 2/(period+1)
    result = series.copy()
    # 找到第一个有效的起始索引
    first_valid = series.first_valid_index()
    if first_valid is None:
        return result
    start = first_valid + period - 1
    if start >= len(series):
        return result
    # 用前period个有效值的均值初始化
    init_mean = series.loc[first_valid:first_valid+period-1].mean()
    result.iloc[start] = init_mean
    for i in range(start+1, len(series)):
        result.iloc[i] = series.iloc[i]*alpha + result.iloc[i-1]*(1-alpha)
    result.iloc[:start] = np.nan
    return result

df['EMA12'] = ema(df['close'], 12)
df['EMA26'] = ema(df['close'], 26)

# 交叉信号
df['golden_cross'] = (df['SMA5']>df['SMA20']) & (df['SMA5'].shift(1)<=df['SMA20'].shift(1))
df['death_cross'] = (df['SMA5']<df['SMA20']) & (df['SMA5'].shift(1)>=df['SMA20'].shift(1))

print(f"SMA5={df['SMA5'].iloc[-1]:.2f}, SMA20={df['SMA20'].iloc[-1]:.2f}, SMA60={df['SMA60'].iloc[-1]:.2f}")
print(f"EMA12={df['EMA12'].iloc[-1]:.2f}, EMA26={df['EMA26'].iloc[-1]:.2f}")
print(f"金叉: {df['golden_cross'].sum()}次, 死叉: {df['death_cross'].sum()}次")

# ═══ 3. MACD ═══
print("\n📊 3. MACD")
df['DIF'] = df['EMA12'] - df['EMA26']
df['DEA'] = ema(df['DIF'], 9)
df['MACD'] = 2*(df['DIF'] - df['DEA'])
print(f"DIF={df['DIF'].iloc[-1]:.4f}, DEA={df['DEA'].iloc[-1]:.4f}")
print(f"{'多头' if df['DIF'].iloc[-1]>df['DEA'].iloc[-1] else '空头'} (DIF {'>' if df['DIF'].iloc[-1]>df['DEA'].iloc[-1] else '<'} DEA)")

# ═══ 4. 布林带 ═══
print("\n📉 4. 布林带")
df['BOLL_MID'] = df['SMA20']
df['BOLL_STD'] = df['close'].rolling(20).std()
df['BOLL_UP'] = df['BOLL_MID'] + 2*df['BOLL_STD']
df['BOLL_DN'] = df['BOLL_MID'] - 2*df['BOLL_STD']
df['BOLL_WIDTH'] = (df['BOLL_UP'] - df['BOLL_DN'])/df['BOLL_MID']*100
pos = (df['close'].iloc[-1]-df['BOLL_DN'].iloc[-1])/(df['BOLL_UP'].iloc[-1]-df['BOLL_DN'].iloc[-1])*100
print(f"上轨={df['BOLL_UP'].iloc[-1]:.2f}, 中轨={df['BOLL_MID'].iloc[-1]:.2f}, 下轨={df['BOLL_DN'].iloc[-1]:.2f}")
print(f"带宽={df['BOLL_WIDTH'].iloc[-1]:.2f}%, 当前位置={pos:.0f}%分位")

# ═══ 5. RSI ═══
print("\n⚡ 5. RSI")
def calc_rsi(series, period):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_g = gain.rolling(period).mean()
    avg_l = loss.rolling(period).mean()
    rs = avg_g/avg_l
    return 100-100/(1+rs)

df['RSI6'] = calc_rsi(df['close'], 6)
df['RSI14'] = calc_rsi(df['close'], 14)
print(f"RSI6={df['RSI6'].iloc[-1]:.1f}, RSI14={df['RSI14'].iloc[-1]:.1f}")

# ═══ 6. KDJ ═══
print("\n📊 6. KDJ")
def calc_kdj(df, n=9):
    ln = df['low'].rolling(n).min()
    hn = df['high'].rolling(n).max()
    rsv = (df['close']-ln)/(hn-ln)*100
    rsv = rsv.fillna(50)
    k = pd.Series(50.0, index=df.index)
    d = pd.Series(50.0, index=df.index)
    for i in range(1, len(df)):
        k.iloc[i] = 2/3*k.iloc[i-1] + 1/3*rsv.iloc[i]
        d.iloc[i] = 2/3*d.iloc[i-1] + 1/3*k.iloc[i]
    j = 3*k - 2*d
    return rsv, k, d, j

df['RSV'], df['K'], df['D'], df['J'] = calc_kdj(df)
print(f"K={df['K'].iloc[-1]:.1f}, D={df['D'].iloc[-1]:.1f}, J={df['J'].iloc[-1]:.1f}")

# ═══ 7. 威廉指标 ═══
print("\n🔧 7. 威廉指标 W%R")
def calc_wr(df, n=14):
    hn = df['high'].rolling(n).max()
    ln = df['low'].rolling(n).min()
    return (hn-df['close'])/(hn-ln)*(-100)

df['WR'] = calc_wr(df, 14)
print(f"W%R(14)={df['WR'].iloc[-1]:.1f}")

# ═══ 8. 乖离率 ═══
print("\n📏 8. 乖离率 BIAS")
df['BIAS5'] = (df['close']-df['SMA5'])/df['SMA5']*100
df['BIAS10'] = (df['close']-df['SMA10'])/df['SMA10']*100
print(f"BIAS5={df['BIAS5'].iloc[-1]:.2f}%, BIAS10={df['BIAS10'].iloc[-1]:.2f}%")

# ═══ 9. 量价指标 ═══
print("\n💹 9. 量价指标")
df['VOL_MA5'] = df['vol'].rolling(5).mean()
df['VOL_MA20'] = df['vol'].rolling(20).mean()
df['VOL_RATIO'] = df['vol']/df['vol'].rolling(5).mean()

def calc_mfi(df, period=14):
    tp = (df['high']+df['low']+df['close'])/3
    mf = tp*df['vol']
    pos = mf.where(tp>tp.shift(1), 0)
    neg = mf.where(tp<tp.shift(1), 0)
    mfr = pos.rolling(period).sum()/neg.rolling(period).sum().replace(0, np.nan)
    return 100-100/(1+mfr)

df['MFI'] = calc_mfi(df, 14)
print(f"量比={df['VOL_RATIO'].iloc[-1]:.2f}, MFI={df['MFI'].iloc[-1]:.1f}")

# ═══ 10. ATR ═══
print("\n🌊 10. ATR")
def calc_atr(df, period=14):
    tr = pd.Series(0.0, index=df.index)
    for i in range(1, len(df)):
        tr.iloc[i] = max(df['high'].iloc[i]-df['low'].iloc[i],
                         abs(df['high'].iloc[i]-df['close'].iloc[i-1]),
                         abs(df['low'].iloc[i]-df['close'].iloc[i-1]))
    return tr, tr.rolling(period).mean()

df['TR'], df['ATR14'] = calc_atr(df, 14)
atr_pct = df['ATR14'].iloc[-1]/df['close'].iloc[-1]*100
print(f"ATR14={df['ATR14'].iloc[-1]:.2f}, ATR/Close={atr_pct:.2f}%")

# ==================== 可视化 ====================

# ═══ 视觉1: SMA图表 ═══
print("\n🎨 生成图表...")
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(df['trade_date'], df['close'], color='#333', lw=1.5, label='收盘价')
for ma, c, n in [('SMA5','#e24b4a','SMA5'),('SMA10','#ff9933','SMA10'),('SMA20','#378add','SMA20'),('SMA60','#1d9e75','SMA60')]:
    ax.plot(df['trade_date'], df[ma], color=c, lw=1, alpha=0.7, label=n)
gold = df[df['golden_cross']]; death = df[df['death_cross']]
ax.scatter(gold['trade_date'], gold['close'], color='red', marker='^', s=100, zorder=5, label='金叉')
ax.scatter(death['trade_date'], death['close'], color='green', marker='v', s=100, zorder=5, label='死叉')
ax.set_title('中芯国际(688981.SH) 收盘价 + 移动平均线', fontsize=14, fontweight='bold')
ax.set_ylabel('价格 (元)'); ax.legend(ncol=5, fontsize=9); ax.grid(True, alpha=0.2)
fig.savefig(f'{OUT_DIR}/sma_ema_plot.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# ═══ 视觉2: MACD ═══
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), gridspec_kw={'height_ratios':[2,1]})
ax1.plot(df['trade_date'], df['close'], color='#333', lw=1.5)
ax1.set_title('中芯国际 收盘价', fontsize=13, fontweight='bold'); ax1.set_ylabel('价格(元)')
ax1.grid(True, alpha=0.2)

macd_colors = ['#e24b4a' if v>=0 else '#1d9e75' for v in df['MACD'].fillna(0)]
ax2.bar(df['trade_date'], df['MACD'].fillna(0), color=macd_colors, alpha=0.6, width=0.7)
ax2.plot(df['trade_date'], df['DIF'], color='#333', lw=1.2, label='DIF')
ax2.plot(df['trade_date'], df['DEA'], color='orange', lw=1.2, label='DEA')
ax2.axhline(y=0, color='gray', lw=0.5, linestyle='--')
ax2.set_title('MACD', fontsize=13, fontweight='bold'); ax2.set_ylabel('MACD'); ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.2)
fig.savefig(f'{OUT_DIR}/macd_plot.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# ═══ 视觉3: 布林带 ═══
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(df['trade_date'], df['close'], color='#333', lw=1.5, label='收盘价')
ax.plot(df['trade_date'], df['BOLL_MID'], color='blue', lw=1, alpha=0.7, label='中轨(SMA20)')
ax.plot(df['trade_date'], df['BOLL_UP'], color='gray', lw=0.8, alpha=0.5, label='上轨')
ax.plot(df['trade_date'], df['BOLL_DN'], color='gray', lw=0.8, alpha=0.5, label='下轨')
ax.fill_between(df['trade_date'], df['BOLL_UP'], df['BOLL_DN'], alpha=0.08, color='blue')
ax.set_title('布林带 (20, 2σ)', fontsize=14, fontweight='bold')
ax.set_ylabel('价格 (元)'); ax.legend(fontsize=9); ax.grid(True, alpha=0.2)
fig.savefig(f'{OUT_DIR}/bollinger_plot.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# ═══ 视觉4: RSI ═══
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(df['trade_date'], df['RSI6'], color='#e24b4a', lw=1, alpha=0.6, label='RSI(6)')
ax.plot(df['trade_date'], df['RSI14'], color='#378add', lw=1.2, label='RSI(14)')
ax.axhline(y=70, color='red', lw=0.8, linestyle='--', alpha=0.5)
ax.axhline(y=30, color='green', lw=0.8, linestyle='--', alpha=0.5)
ax.fill_between(df['trade_date'], 70, 100, alpha=0.08, color='red')
ax.fill_between(df['trade_date'], 0, 30, alpha=0.08, color='green')
ax.set_ylim(0, 100)
ax.set_title('RSI (相对强弱指标)', fontsize=14, fontweight='bold')
ax.set_ylabel('RSI'); ax.legend(fontsize=9); ax.grid(True, alpha=0.2)
fig.savefig(f'{OUT_DIR}/rsi_plot.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# ═══ 视觉5: KDJ ═══
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(df['trade_date'], df['K'], color='#e24b4a', lw=1, label='K')
ax.plot(df['trade_date'], df['D'], color='#378add', lw=1, label='D')
ax.plot(df['trade_date'], df['J'], color='green', lw=0.8, alpha=0.5, label='J')
ax.axhline(y=80, color='red', lw=0.8, linestyle='--', alpha=0.4)
ax.axhline(y=20, color='green', lw=0.8, linestyle='--', alpha=0.4)
ax.set_ylim(0, 100)
ax.set_title('KDJ (随机指标)', fontsize=14, fontweight='bold')
ax.set_ylabel('KDJ'); ax.legend(fontsize=9); ax.grid(True, alpha=0.2)
fig.savefig(f'{OUT_DIR}/kdj_plot.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# ═══ 视觉6: W%R + BIAS ═══
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
ax1.plot(df['trade_date'], df['WR'], color='purple', lw=1.2, label='W%R(14)')
ax1.axhline(y=-20, color='red', lw=0.8, linestyle='--', alpha=0.5)
ax1.axhline(y=-80, color='green', lw=0.8, linestyle='--', alpha=0.5)
ax1.set_title('威廉指标 W%R', fontsize=13, fontweight='bold')
ax1.set_ylabel('W%R'); ax1.legend(); ax1.grid(True, alpha=0.2)

ax2.plot(df['trade_date'], df['BIAS5'], color='#e24b4a', lw=1, label='BIAS(5)')
ax2.plot(df['trade_date'], df['BIAS10'], color='#378add', lw=1, label='BIAS(10)')
ax2.axhline(y=5, color='red', lw=0.8, linestyle='--', alpha=0.4)
ax2.axhline(y=-5, color='green', lw=0.8, linestyle='--', alpha=0.4)
ax2.set_title('乖离率 BIAS', fontsize=13, fontweight='bold')
ax2.set_ylabel('BIAS(%)'); ax2.legend(); ax2.grid(True, alpha=0.2)
fig.savefig(f'{OUT_DIR}/wr_bias_plot.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# ═══ 视觉7: 成交量 ═══
fig, ax = plt.subplots(figsize=(14, 5))
vol_c = ['#e24b4a' if v>=0 else '#1d9e75' for v in df['pct_chg'].fillna(0)]
ax.bar(df['trade_date'], df['vol']/10000, color=vol_c, alpha=0.6, width=0.7, label='成交量')
ax.plot(df['trade_date'], df['VOL_MA5']/10000, color='orange', lw=1, label='VOL_MA5')
ax.plot(df['trade_date'], df['VOL_MA20']/10000, color='purple', lw=1, label='VOL_MA20')
ax.set_title('成交量 + 均量线', fontsize=14, fontweight='bold')
ax.set_ylabel('成交量(万手)'); ax.legend(); ax.grid(True, alpha=0.2)
fig.savefig(f'{OUT_DIR}/volume_plot.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# ═══ 视觉8: ATR ═══
fig, ax = plt.subplots(figsize=(14, 4))
ax.bar(df['trade_date'], df['ATR14'].fillna(0), color='orange', alpha=0.7, width=0.7)
ax.set_title('ATR(14) 平均真实波幅', fontsize=14, fontweight='bold')
ax.set_ylabel('ATR'); ax.grid(True, alpha=0.2)
fig.savefig(f'{OUT_DIR}/atr_plot.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# ═══ 视觉9: 综合看板 (9子图) ═══
print("📊 生成9子图综合看板...")
plot_df = df.tail(120).copy()
dates = plot_df['trade_date']

fig = plt.figure(figsize=(16, 22))
gs = fig.add_gridspec(9, 1, hspace=0.35, height_ratios=[2.2, 0.8, 1.2, 1, 1, 1, 1, 1, 0.8])

# 1: 价格+SMA
ax1 = fig.add_subplot(gs[0])
ax1.plot(dates, plot_df['close'], color='#333', lw=1.8, label='收盘价')
for ma, c in [('SMA5','#e24b4a'),('SMA20','#378add'),('SMA60','#1d9e75')]:
    ax1.plot(dates, plot_df[ma], color=c, lw=1, alpha=0.8, label=ma)
g = plot_df[plot_df['golden_cross']]
d = plot_df[plot_df['death_cross']]
ax1.scatter(g['trade_date'], g['close'], color='red', marker='^', s=80, zorder=5)
ax1.scatter(d['trade_date'], d['close'], color='green', marker='v', s=80, zorder=5)
ax1.set_title('中芯国际(688981.SH) 收盘价 + 均线', fontsize=13, fontweight='bold')
ax1.set_ylabel('价格(元)'); ax1.legend(ncol=6, fontsize=9); ax1.grid(True, alpha=0.2)
ax1.tick_params(labelbottom=False)

# 2: 成交量
ax2 = fig.add_subplot(gs[1])
vc = ['#e24b4a' if v>=0 else '#1d9e75' for v in plot_df['pct_chg'].fillna(0)]
ax2.bar(dates, plot_df['vol']/10000, color=vc, alpha=0.6, width=0.7)
ax2.plot(dates, plot_df['VOL_MA5']/10000, color='orange', lw=1, label='VOL_MA5')
ax2.plot(dates, plot_df['VOL_MA20']/10000, color='purple', lw=1, label='VOL_MA20')
ax2.set_ylabel('成交量(万手)'); ax2.legend(fontsize=9); ax2.grid(True, alpha=0.2)
ax2.tick_params(labelbottom=False)

# 3: MACD
ax3 = fig.add_subplot(gs[2])
mc = ['#e24b4a' if v>=0 else '#1d9e75' for v in plot_df['MACD'].fillna(0)]
ax3.bar(dates, plot_df['MACD'].fillna(0), color=mc, alpha=0.6, width=0.7)
ax3.plot(dates, plot_df['DIF'], color='#333', lw=1.2, label='DIF')
ax3.plot(dates, plot_df['DEA'], color='orange', lw=1.2, label='DEA')
ax3.axhline(y=0, color='gray', lw=0.5, linestyle='--')
ax3.set_title('MACD', fontsize=12, fontweight='bold'); ax3.set_ylabel('MACD')
ax3.legend(fontsize=9); ax3.grid(True, alpha=0.2); ax3.tick_params(labelbottom=False)

# 4: 布林带
ax4 = fig.add_subplot(gs[3])
ax4.plot(dates, plot_df['close'], color='#333', lw=1.5, label='收盘价')
ax4.plot(dates, plot_df['BOLL_MID'], color='blue', lw=1, alpha=0.7, label='中轨')
ax4.plot(dates, plot_df['BOLL_UP'], color='gray', lw=0.8, alpha=0.5, label='上轨')
ax4.plot(dates, plot_df['BOLL_DN'], color='gray', lw=0.8, alpha=0.5, label='下轨')
ax4.fill_between(dates, plot_df['BOLL_UP'], plot_df['BOLL_DN'], alpha=0.08, color='blue')
ax4.set_title('布林带 (20,2σ)', fontsize=12, fontweight='bold'); ax4.set_ylabel('价格(元)')
ax4.legend(fontsize=9); ax4.grid(True, alpha=0.2); ax4.tick_params(labelbottom=False)

# 5: RSI
ax5 = fig.add_subplot(gs[4])
ax5.plot(dates, plot_df['RSI6'], color='#e24b4a', lw=1, alpha=0.6, label='RSI(6)')
ax5.plot(dates, plot_df['RSI14'], color='#378add', lw=1.2, label='RSI(14)')
ax5.axhline(y=70, color='red', lw=0.8, linestyle='--', alpha=0.5)
ax5.axhline(y=30, color='green', lw=0.8, linestyle='--', alpha=0.5)
ax5.fill_between(dates, 70, 100, alpha=0.08, color='red')
ax5.fill_between(dates, 0, 30, alpha=0.08, color='green')
ax5.set_ylim(0, 100); ax5.set_title('RSI', fontsize=12, fontweight='bold')
ax5.set_ylabel('RSI'); ax5.legend(fontsize=9); ax5.grid(True, alpha=0.2)
ax5.tick_params(labelbottom=False)

# 6: KDJ
ax6 = fig.add_subplot(gs[5])
ax6.plot(dates, plot_df['K'], color='#e24b4a', lw=1, label='K')
ax6.plot(dates, plot_df['D'], color='#378add', lw=1, label='D')
ax6.plot(dates, plot_df['J'], color='green', lw=0.8, alpha=0.5, label='J')
ax6.axhline(y=80, color='red', lw=0.8, linestyle='--', alpha=0.4)
ax6.axhline(y=20, color='green', lw=0.8, linestyle='--', alpha=0.4)
ax6.set_ylim(0, 100); ax6.set_title('KDJ', fontsize=12, fontweight='bold')
ax6.set_ylabel('KDJ'); ax6.legend(fontsize=9); ax6.grid(True, alpha=0.2)
ax6.tick_params(labelbottom=False)

# 7: W%R
ax7 = fig.add_subplot(gs[6])
ax7.plot(dates, plot_df['WR'], color='purple', lw=1.2, label='W%R(14)')
ax7.axhline(y=-20, color='red', lw=0.8, linestyle='--', alpha=0.5)
ax7.axhline(y=-80, color='green', lw=0.8, linestyle='--', alpha=0.5)
ax7.set_title('威廉指标W%R', fontsize=12, fontweight='bold')
ax7.set_ylabel('W%R'); ax7.legend(fontsize=9); ax7.grid(True, alpha=0.2)
ax7.tick_params(labelbottom=False)

# 8: BIAS
ax8 = fig.add_subplot(gs[7])
ax8.plot(dates, plot_df['BIAS5'], color='#e24b4a', lw=1, label='BIAS(5)')
ax8.plot(dates, plot_df['BIAS10'], color='#378add', lw=1, label='BIAS(10)')
ax8.axhline(y=5, color='red', lw=0.8, linestyle='--', alpha=0.4)
ax8.axhline(y=-5, color='green', lw=0.8, linestyle='--', alpha=0.4)
ax8.set_title('乖离率BIAS', fontsize=12, fontweight='bold')
ax8.set_ylabel('BIAS(%)'); ax8.legend(fontsize=9); ax8.grid(True, alpha=0.2)
ax8.tick_params(labelbottom=False)

# 9: ATR
ax9 = fig.add_subplot(gs[8])
ax9.bar(dates, plot_df['ATR14'].fillna(0), color='orange', alpha=0.7, width=0.7)
ax9.set_title('ATR(14)', fontsize=12, fontweight='bold')
ax9.set_xlabel('交易日'); ax9.grid(True, alpha=0.2)
ax9.tick_params(axis='x', rotation=45)

for ax in [ax1,ax2,ax3,ax4,ax5,ax6,ax7,ax8]:
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

fig.savefig(f'{OUT_DIR}/smic_indicators_dashboard.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"✅ 综合看板已保存")

# ==================== 输出汇总 ====================

# 数据文件: 包含所有计算指标
df_out = df[['trade_date','open','high','low','close','vol','pct_chg',
             'SMA5','SMA10','SMA20','SMA60','EMA12','EMA26',
             'DIF','DEA','MACD',
             'BOLL_MID','BOLL_UP','BOLL_DN','BOLL_WIDTH',
             'RSI6','RSI14','K','D','J','WR','BIAS5','BIAS10',
             'VOL_MA5','VOL_MA20','VOL_RATIO','MFI','TR','ATR14']]
df_out.to_csv(f'{OUT_DIR}/smic_all_indicators.csv', index=False, encoding='utf-8-sig')
print(f"📄 指标数据CSV已保存")

# JSON 摘要
summary = {
    "stock": "中芯国际(688981.SH)",
    "data_range": f"{df['trade_date'].min().date()} ~ {df['trade_date'].max().date()}",
    "record_count": len(df),
    "last_close": df['close'].iloc[-1],
    "latest_indicators": {
        "SMA5": round(df['SMA5'].iloc[-1],2), "SMA20": round(df['SMA20'].iloc[-1],2),
        "SMA60": round(df['SMA60'].iloc[-1],2),
        "EMA12": round(df['EMA12'].iloc[-1],2), "EMA26": round(df['EMA26'].iloc[-1],2),
        "MACD_DIF": round(df['DIF'].iloc[-1],4), "MACD_DEA": round(df['DEA'].iloc[-1],4),
        "BOLL_upper": round(df['BOLL_UP'].iloc[-1],2), "BOLL_lower": round(df['BOLL_DN'].iloc[-1],2),
        "RSI6": round(df['RSI6'].iloc[-1],1), "RSI14": round(df['RSI14'].iloc[-1],1),
        "K": round(df['K'].iloc[-1],1), "D": round(df['D'].iloc[-1],1), "J": round(df['J'].iloc[-1],1),
        "WR": round(df['WR'].iloc[-1],1),
        "BIAS5": round(df['BIAS5'].iloc[-1],2), "BIAS10": round(df['BIAS10'].iloc[-1],2),
        "MFI": round(df['MFI'].iloc[-1],1),
        "ATR14": round(df['ATR14'].iloc[-1],2)
    },
    "signals": {
        "trend": "多头排列" if df['SMA5'].iloc[-1] > df['SMA20'].iloc[-1] > df['SMA60'].iloc[-1] else "空头排列" if df['SMA5'].iloc[-1] < df['SMA20'].iloc[-1] < df['SMA60'].iloc[-1] else "交叉整理",
        "macd": "多头" if df['DIF'].iloc[-1] > df['DEA'].iloc[-1] else "空头",
        "rsi": "超买" if df['RSI14'].iloc[-1] > 70 else "超卖" if df['RSI14'].iloc[-1] < 30 else "中性"
    }
}

with open(f'{OUT_DIR}/indicator_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"📄 指标摘要JSON已保存")

# 打印最终摘要
print("\n" + "=" * 55)
print("✅ 全部完成！")
print("=" * 55)
print(f"\n输出目录: {OUT_DIR}")
print(f"图表文件:")
for f in sorted(os.listdir(OUT_DIR)):
    print(f"  {f}")
