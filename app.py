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

# --- デザイン（絶対に重ならないよう余白と高さを固定） ---
css_code = f"""
<style>
    @font-face {{
        font-family: 'Mochiy Pop One';
        src: url(data:font/ttf;base64,{font_base64}) format('truetype');
    }}

    /* 全体にフォントを適用 */
    html, body, div, span, p, input, select, textarea, button {{
        font-family: 'Mochiy Pop One', sans-serif !important;
    }}

    /* ヘッダーエリア：高さを自動にせず、十分な余白（margin）を確保 */
    .header-container {{
        width: 100%;
        border-bottom: 3px solid #5d6d7e;
        padding-top: 20px;
        padding-bottom: 20px;
        margin-bottom: 50px; /* 下との間隔を大きく開ける */
        background-color: #ffffff;
    }}
    
    .total-text {{
        font-size: 1.2rem;
        color: #555;
        margin: 0 0 10px 0;
        display: block;
    }}
    
    .total-amount {{
        font-size: 2.5rem; /* 数字を大きく */
        font-weight: bold;
        color: #000;
        margin: 0;
        display: block;
        line-height: 1.2;
    }}

    /* テーブルのスタイル */
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
        # 全ての列の nan を空欄にする
        df = df.astype(object).fillna("")
        return df
    return pd.DataFrame(columns=["日付", "支払先", "品名・名目", "備考", "金額"])

# 入力フォーム
with st.expander("📝 新規データ入力", expanded=False):
    with st.form("input_form", clear_on_submit=True):
        input_date = st.date_input("日付", date.today())
        payee = st.text_input("支払先")
        item_name = st.text_input("品名・名目")
        amount = st.number_input("金額 (円)", min_value=0, step=1)
        memo = st.text_area("備考")
        if st.form_submit_button("登録"):
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
    filtered_df = df[df['年月'] == selected_month].copy()
    
    # 金額を数値に変換（nan対策済み）
    filtered_df["金額"] = pd.to_numeric(filtered_df["金額"], errors='coerce').fillna(0)
    total = int(filtered_df["金額"].sum())
    
    # 合計表示：絶対に重ならないようHTMLをシンプル化
    st.markdown(f'''
        <div class="header-container">
            <p class="total-text">経費合計</p>
            <p class="total-amount">{total:,} 円</p>
        </div>
    ''', unsafe_allow_html=True)

    # テーブル表示
    rows_html = ""
    for _, r in filtered_df.iterrows():
        # 金額が0なら空欄、そうでなければカンマ区切り
        amt = f"{int(r['金額']):,}" if r['金額'] > 0 else "0"
        rows_html += f"<tr><td>{r['日付']}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{amt}</td></tr>"

    table_html = f"""
    <div class="custom-table-container">
        <table class="custom-table">
            <thead>
                <tr>
                    <th>日付</th><th>支払先</th><th>品名</th><th>備考</th><th>金額</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
else:
    st.info("データがありません。")
