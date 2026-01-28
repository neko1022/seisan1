import streamlit as st
import pandas as pd
import os
import base64
from datetime import date

# ページ設定
st.set_page_config(page_title="経費精算システム", layout="wide")

# --- フォントファイルを読み込むための関数 ---
def get_base64_font(font_file):
    with open(font_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# フォントの適用（GitHubにファイルを上げた状態で動きます）
FONT_FILE = "MochiyPopOne-Regular.ttf"
if os.path.exists(FONT_FILE):
    font_base64 = get_base64_font(FONT_FILE)
    font_style = f"""
        <style>
        @font-face {{
            font-family: 'Mochiy Pop One';
            src: url(data:font/ttf;base64,{font_base64}) format('truetype');
        }}
        /* アプリ全体のフォントを上書き */
        html, body, [class*="css"], .stText, .stMarkdown, .stButton, div, span, h1, h2, h3, input, textarea {{
            font-family: 'Mochiy Pop One', sans-serif !important;
        }}
        
        /* 前回のデザインも維持 */
        .stApp {{ background-color: white; }}
        .header-container {{
            border-bottom: 2px solid #5d6d7e;
            padding: 10px 0;
            margin-bottom: 30px;
        }}
        .total-text {{ font-size: 1.1rem; font-weight: bold; }}
        .total-amount {{ font-size: 1.8rem; font-weight: bold; margin-left: 20px; }}
        th {{ background-color: #5d6d7e !important; color: white !important; font-weight: normal !important; }}
        .stButton>button {{ background-color: #5d6d7e; color: white; border-radius: 5px; }}
        </style>
        """
    st.markdown(font_style, unsafe_allow_html=True)

# --- 以下、これまでのロジック ---

CSV_FILE = "expenses.csv"

def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df["日付"] = pd.to_datetime(df["日付"]).dt.date
        return df
    return pd.DataFrame(columns=["日付", "支払先", "品名・名目", "備考", "金額"])

# データ入力エリア
with st.expander("📝 新規データ入力フォーム"):
    with st.form("input_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            input_date = st.date_input("日付", date.today())
            payee = st.text_input("支払先")
        with c2:
            item_name = st.text_input("品名・名目")
            amount = st.number_input("金額 (円)", min_value=0, step=1)
        with c3:
            memo = st.text_area("備考", height=68)
        
        if st.form_submit_button("データを登録"):
            if payee and amount > 0:
                new_row = pd.DataFrame([[input_date, payee, item_name, memo, amount]], 
                                        columns=["日付", "支払先", "品名・名目", "備考", "金額"])
                df = load_data()
                pd.concat([df, new_row], ignore_index=True).to_csv(CSV_FILE, index=False)
                st.rerun()

# メイン表示エリア
df = load_data()
if not df.empty:
    df['年月'] = df['日付'].apply(lambda x: x.strftime('%Y年%m月'))
    selected_month = st.selectbox("表示月を選択", sorted(df['年月'].unique(), reverse=True))
    filtered_df = df[df['年月'] == selected_month].drop(columns=['年月'])
    
    total = filtered_df["金額"].sum()
    st.markdown(f"""
        <div class="header-container">
            <span class="total-text">経費合計：</span>
            <span class="total-amount">{total:,} 円</span>
        </div>
    """, unsafe_allow_html=True)

    st.dataframe(
        filtered_df[["日付", "支払先", "品名・名目", "備考", "金額"]],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("データがありません。")
