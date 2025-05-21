from flask import Flask, request, jsonify, render_template, send_from_directory
import adata
import os
import pandas as pd
from flask_cors import CORS  # 导入CORS扩展

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stock_data')
def stock_data():
    return render_template('stock_data.html')

@app.route('/api/financial-data', methods=['GET'])
def get_financial_data():
    try:
        # 尝试使用adata获取真实数据
        if adata:
            df = adata.stock.finance.get_core_index(stock_code='600329')
            
            # 检查必要字段是否存在，新增毛利润字段
            required_fields = {
               'report_date': '报告日期',
                'total_rev': '营业总收入',
                'net_profit_attr_sh': '归属净利润',
                'gross_profit': '毛利润',  # 直接使用数据源中的毛利润字段
                'gross_margin': '毛利率',
                'roa_wtd': '总资产收益率',
                'oper_cf_ps': '每股经营现金流',
                'basic_eps': '基本每股收益',
                'net_asset_ps': '每股净资产',
                'net_margin': '净利率',
                'asset_liab_ratio': '资产负债率',
                'non_gaap_net_profit': '扣非净利润'  # 添加扣非净利润字段
            }
            
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                return jsonify({'error': f"获取的数据缺少必要字段: {', '.join(missing_fields)}"}), 400
            
            # 重命名字段以匹配前端期望
            df = df.rename(columns=required_fields)
            
            # 将金额从元转换为亿元，保留两位小数
            df['营业总收入'] = (df['营业总收入'] / 1e8).round(2)
            df['归属净利润'] = (df['归属净利润'] / 1e8).round(2)
            df['毛利润'] = (df['毛利润'] / 1e8).round(2)  # 直接转换毛利润单位
            df['扣非净利润'] = (df['扣非净利润'] / 1e8).round(2)  # 转换扣非净利润单位
            
            # 处理NaN值
            df = df.fillna(0)
            
            # 确保数据按报告日期排序
            df['报告日期'] = pd.to_datetime(df['报告日期'])
            df = df.sort_values('报告日期')
            df['报告日期'] = df['报告日期'].dt.strftime('%Y-%m-%d')
            
            print(f"成功获取{len(df)}条财务数据")
        else:
            # 如果无法导入adata，使用示例数据
            print("使用示例数据")
            df = pd.DataFrame({
                '报告日期': ['2023-12-31', '2023-09-30', '2023-06-30', '2023-03-31'],
                '营业总收入': [125.8, 98.5, 82.3, 75.2],
                '归属净利润': [21.3, 16.8, 14.2, 12.5],
                '毛利润': [48.4, 36.6, 30.3, 27.2],  # 示例毛利润数据
                '毛利率': [38.5, 37.2, 36.8, 36.2],
                '总资产收益率': [8.2, 7.5, 7.0, 6.8],
                '每股经营现金流': [2.35, 1.82, 1.56, 1.28],
                '基本每股收益': [0.85, 0.67, 0.57, 0.50],
                '每股净资产': [6.23, 5.98, 5.71, 5.43],
                '净利率': [17.0, 17.1, 17.2, 16.6],
                '资产负债率': [42.3, 41.8, 42.1, 43.0],
                '扣非净利润': [18.5, 14.2, 12.3, 10.8]  # 示例扣非净利润数据
            })
        
        # 准备响应数据，添加毛利润相关字段
        data = {
            'dates': df['报告日期'].tolist(),
           'revenues': df['营业总收入'].tolist(),
            'profits': df['归属净利润'].tolist(),
            'grossProfits': df['毛利润'].tolist(),  # 直接使用数据源中的毛利润
           'margins': df['毛利率'].tolist(),
            'roa': df['总资产收益率'].tolist(),
            'cashFlows': df['每股经营现金流'].tolist(),
           'recentData': {
                '基本每股收益': df['基本每股收益'].iloc[-1],
                '每股净资产': df['每股净资产'].iloc[-1],
                '毛利率': df['毛利率'].iloc[-1],
                '净利率': df['净利率'].iloc[-1],
                '总资产收益率': df['总资产收益率'].iloc[-1],
                '资产负债率': df['资产负债率'].iloc[-1],
                '营业收入环比增长': calculate_growth(df, '营业总收入'),
                '净利润环比增长': calculate_growth(df, '归属净利润'),
                '毛利润环比增长': calculate_growth(df, '毛利润'),  # 计算毛利润环比增长
                '扣非净利润': df['扣非净利润'].iloc[-1]  # 添加扣非净利润字段
            }
        }
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
def calculate_growth(df, column):
    """计算环比增长率"""
    if len(df) < 2:
        return "N/A"
    
    current = df[column].iloc[-1]
    previous = df[column].iloc[-5]
    
    # 处理分母为零的情况
    if previous == 0:
        return "∞%" if current > 0 else "-∞%"
    
    growth = ((current / previous) - 1) * 100
    return f"{growth:.2f}%"

@app.route('/get_stock_info')
def get_stock_info():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "未提供有效的股票代码"}), 400

    try:
        # 这里以获取股票代码信息为例，你可以根据需求修改
        df = adata.stock.market.get_market(stock_code=code, start_date='2025-05-01', end_date='2025-05-08', k_type=1, adjust_type=1)
        specific_stock = df[df['stock_code'] == code]
        if specific_stock.empty:
            return jsonify({"error": f"未找到股票代码 {code} 的信息"}), 404
        result = specific_stock.to_dict(orient='records')[0]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"获取股票信息时出错: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)