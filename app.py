import streamlit as st
import pandas as pd
import os
import base64
from datetime import date

# ページ設定
st.set_page_config(page_title="経費精算システム", layout="wide")

# --- フォントファイルを読み込むための関数 ---
def get_base64_font(font_file):
    if os.path.exists(font_file):
        with open(font_file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

font_base64 = get_base64_font("MochiyPopOne-Regular.ttf")

# --- デザイン（CSS） ---
css_code = f"""
<style>
    @font-face {{
        font-family: 'Mochiy Pop One';
        src: url(data:font/ttf;base64,{font_base64}) format('truetype');
    }}

    /* 全体にフォントを適用 */
    html, body, [class*="css"], div, span, p, input, select, textarea, button {{
        font-family: 'Mochiy Pop One', sans-serif !important;
    }}

    /* 上段の重なり解消：高さをしっかり確保し、要素をブロック化 */
    .header-container {{
        border-bottom: 2px solid #5d6d7e;
        padding: 20px 10px;
        margin-bottom: 30px;
        background-color: #ffffff;
        display: block;
        clear: both;
    }}
    .total-text {{
        font-size: 1.1rem;
        color: #555;
        display: block; /* 改行させる */
        margin-bottom: 8px;
    }}
    .total-amount {{
        font-size: 2.2rem;
        font-weight: bold;
        color: #000;
        display: block; /* 改行させる */
        line-height: 1.2;
    }}

    /* テーブル設定 */
    .custom-table-container {{
        overflow-x: auto;
        width: 100%;
        margin-top: 20px;
    }}
    .custom-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
    }}
    .custom-table th {{
        background-color: #5d6d7e;
        color: white;
        text-align: left;
        padding: 12px 10px;
        white-space: nowrap;
    }}
    .custom-table td {{
        border-bottom: 1px solid #eee;
        padding: 12px 10px;
        background-color: white;
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
        # 「nan」を空文字列に置き換える（VBAでいう「If IsNull Then ""」のような処理）
        df = df.fillna("")
        return df
    return pd.DataFrame(columns=["日付", "支払先", "品名・名目", "備考", "金額"])

# 入力フォーム
with st.expander("📝 新規データ入力"):
    with st.form("input_form", clear_on_submit=True):
        input_date = st.date_input("日付", date.today())
        payee = st.text_input("支払先")
        item_name = st.text_input("品名・名目")
        amount = st.number_input("金額 (円)", min_value=0, step=1)
        memo = st.text_area("備考", height=68)
        if st.form_submit_button("データを登録"):
            if payee and amount > 0:
                new_row = pd.DataFrame([[input_date, payee, item_name, memo, amount]], 
                                        columns=["日付", "支払先", "品名・名目", "備考", "金額"])
                df = load_data()
                pd.concat([df, new_row], ignore_index=True).to_csv(CSV_FILE, index=False)
                st.rerun()

# 表示エリア
df = load_data()
if not df.empty:
    df['年月'] = df['日付'].apply(lambda x: x.strftime('%Y年%m月'))
    selected_month = st.selectbox("表示月を選択", sorted(df['年月'].unique(), reverse=True))
    filtered_df = df[df['年月'] == selected_month].drop(columns=['年月'])
    
    # 合計表示（HTML構造を整理して重なりを防止）
    total = pd.to_numeric(filtered_df["金額"]).sum()
    st.markdown(f'''
        <div class="header-container">
            <span class="total-text">経費合計</span>
            <span class="total-amount">{total:,} 円</span>
        </div>
    ''', unsafe_allow_html=True)

    # カスタムテーブル表示
    table_html = f"""
    <div class="custom-table-container">
        <table class="custom-table">
            <thead>
                <tr>
                    <th>日付</th><th>支払先</th><th>品名・名目</th><th>備考</th><th>金額</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f"<tr><td>{r['日付']}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}</td></tr>" for _, r in filtered_df.iterrows()])}
            </tbody>
        </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
else:
    st.info("データがありません。")
