import adata
import pandas as pd

# 设置 Pandas 的显示参数
pd.set_option('display.max_rows', None)  # 显示所有行
pd.set_option('display.max_columns', None)  # 显示所有列
pd.set_option('display.width', None)  # 不限制显示宽度
pd.set_option('display.max_colwidth', None)  # 不限制列的显示宽度

kline_df = adata.stock.market.get_market(stock_code='600329', start_date='2025-05-01', end_date='2025-05-08', k_type=1, adjust_type=1)
 
df = adata.stock.finance.get_core_index(stock_code='600329')
print(df)