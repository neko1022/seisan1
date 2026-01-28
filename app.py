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

    /* 入力フォームのラベルとタイトルの重なり防止 */
    .stExpander {{
        margin-top: 30px !important;
        margin-bottom: 30px !important;
        border: 1px solid #ddd !important;
    }}
    
    /* 項目名（ラベル）の余白を極大にする */
    label[data-testid="stWidgetLabel"] {{
        padding-top: 20px !important;
        padding-bottom: 10px !important;
        display: block !important;
    }}

    /* ヘッダーの重なり解消 */
    .header-container {{
        width: 100%;
        border-bottom: 3px solid #5d6d7e;
        padding: 30px 10px !important;
        margin-bottom: 50px !important;
    }}
    
    .total-text {{ font-size: 1.1rem; display: block; margin-bottom: 15px !important; }}
    .total-amount {{ font-size: 2.5rem; font-weight: bold; display: block; }}

    /* テーブル設定 */
    .custom-table-container {{ overflow-x: auto; width: 100%; margin-top: 40px; }}
    .custom-table {{ width: 100%; border-collapse: collapse; }}
    .custom-table th {{ background-color: #5d6d7e; color: white; padding: 15px; text-align: left; }}
    .custom-table td {{ border-bottom: 1px solid #eee; padding: 15px; background-color: white; }}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- データ処理 ---
CSV_FILE = "expenses.csv"
COLS = ["日付", "支払先", "品名・名目", "備考", "金額"]

def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df["日付"] = pd.to_datetime(df["日付"]).dt.date
        return df.astype(object).fillna("")
    return pd.DataFrame(columns=COLS)

# --- 入力フォーム ---
st.write("### ") # タイトルの上に空行を入れて重なり防止
with st.expander("📝 新規データ入力フォーム", expanded=False):
    with st.form("input_form", clear_on_submit=True):
        input_date = st.date_input("日付", date.today())
        payee = st.text_input("支払先")
        item_name = st.text_input("品名・名目")
        amount = st.number_input("金額 (円)", min_value=0, step=1)
        memo = st.text_area("備考")
        
        if st.form_submit_button("登録"):
            if payee and amount > 0:
                new_row = pd.DataFrame([[input_date, payee, item_name, memo, amount]], columns=COLS)
                df = load_data()
                pd.concat([df, new_row], ignore_index=True).to_csv(CSV_FILE, index=False)
                st.rerun()

# --- 表示エリア ---
df = load_data()
if not df.empty:
    df['年月'] = df['日付'].apply(lambda x: x.strftime('%Y年%m月'))
    selected_month = st.selectbox("表示月を選択", sorted(df['年月'].unique(), reverse=True))
    filtered_df = df[df['年月'] == selected_month].copy()
    
    filtered_df["金額"] = pd.to_numeric(filtered_df["金額"], errors='coerce').fillna(0)
    total = int(filtered_df["金額"].sum())
    
    st.markdown(f'<div class="header-container"><p class="total-text">経費合計</p><p class="total-amount">{total:,} 円</p></div>', unsafe_allow_html=True)

    rows_html = "".join([f"<tr><td>{r['日付']}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}</td></tr>" for _, r in filtered_df.iterrows()])
    table_html = f'<div class="custom-table-container"><table class="custom-table"><thead><tr>{"".join([f"<th>{c}</th>" for c in COLS])}</tr></thead><tbody>{rows_html}</tbody></table></div>'
    st.markdown(table_html, unsafe_allow_html=True)
else:
    st.info("データがありません。")
