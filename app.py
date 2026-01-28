import streamlit as st
import pandas as pd
import os
import base64
from datetime import date

# ページ設定
st.set_page_config(page_title="経費精算システム", layout="wide")

# --- フォント読み込み ---
def get_base64_font(font_file):
    if os.path.exists(font_file):
        with open(font_file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

font_base64 = get_base64_font("MochiyPopOne-Regular.ttf")

# --- デザイン修正：重なりを徹底防止 ---
css_code = f"""
<style>
    @font-face {{
        font-family: 'Mochiy Pop One';
        src: url(data:font/ttf;base64,{font_base64}) format('truetype');
    }}

    /* 全体にフォントを適用 */
    html, body, div, span, p, input, select, textarea, button, label {{
        font-family: 'Mochiy Pop One', sans-serif !important;
    }}

    /* 1. 「新規データ入力」の枠（expander）と項目名（label）の重なり防止 */
    .stExpander {{
        margin-top: 10px !important;
        margin-bottom: 20px !important;
    }}
    
    /* 項目名（ラベル）に十分な高さを与えて、入力欄と重ならないようにする */
    label[data-testid="stWidgetLabel"] p {{
        font-size: 0.9rem !important;
        line-height: 2.0 !important; /* 行間を広く */
        padding-bottom: 5px !important;
        margin-bottom: 0px !important;
    }}

    /* 2. ヘッダー（合計金額）の重なり解消 */
    .header-container {{
        width: 100%;
        border-bottom: 3px solid #5d6d7e;
        padding: 25px 10px !important; /* 余白をさらに拡大 */
        margin-bottom: 40px !important;
        background-color: #ffffff;
    }}
    
    .total-text {{
        font-size: 1.0rem;
        color: #555;
        margin: 0 0 15px 0 !important;
        display: block;
    }}
    
    .total-amount {{
        font-size: 2.2rem;
        font-weight: bold;
        color: #000;
        margin: 0 !important;
        display: block;
    }}

    /* テーブル設定 */
    .custom-table-container {{
        overflow-x: auto;
        width: 100%;
        margin-top: 30px;
    }}
    .custom-table {{
        width: 100%;
        border-collapse: collapse;
    }}
    .custom-table th {{
        background-color: #5d6d7e;
        color: white;
        text-align: left;
        padding: 15px 10px;
        white-space: nowrap;
    }}
    .custom-table td {{
        border-bottom: 1px solid #eee;
        padding: 15px 10px;
        background-color: white;
        color: #333;
    }}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- データ処理 ---
CSV_FILE = "expenses.csv"

def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df["日付"] = pd.to_datetime(df["日付"]).dt.date
        df = df.astype(object).fillna("") # nan排除
        return df
    return pd.DataFrame(columns=["日付", "支払先", "品名・名
