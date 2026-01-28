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

# --- デザイン（間隔を適正化） ---
css_code = f"""
<style>
    @font-face {{
        font-family: 'Mochiy Pop One';
        src: url(data:font/ttf;base64,{font_base64}) format('truetype');
    }}

    * {{ font-family: 'Mochiy Pop One', sans-serif !important; }}

    /* ヘッダーエリアの間隔を縮小 */
    .header-box {{
        border-bottom: 2px solid #5d6d7e;
        padding: 10px 0;
        margin-bottom: 25px;
    }}
    .total-t {{ font-size: 1.0rem; color: #666; margin-bottom: 5px; }}
    .total-a {{ font-size: 2.0rem; font-weight: bold; color: #000; margin: 0; }}

    /* 入力エリアのタイトル */
    .form-title {{
        background: #5d6d7e;
        color: white;
        padding: 8px 15px;
        border-radius: 5px;
        font-size: 1.1rem;
        margin-bottom: 15px;
    }}

    /* 入力項目の間隔を「広すぎず・重ならず」に調整 */
    div[data-testid="stVerticalBlock"] > div {{
        margin-bottom: 5px !important;  /* 前後の部品との隙間を最小限に */
        padding-bottom: 0px !important;
    }}

    /* ラベル（項目名）の余白調整 */
    label[data-testid="stWidgetLabel"] {{
        padding-bottom: 2px !important;
        margin-bottom: 2px !important;
        line-height: 1.2 !important;
    }}

    /* 入力ボックス自体の高さを微調整 */
    .stTextInput, .stNumberInput, .stDateInput, .stTextArea {{
        margin-bottom: 10px !important;
    }}

    /* テーブルの密度を上げる */
    .table-style {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
        font-size: 0.9rem;
    }}
    .table-style th {{ background: #5d6d7e; color: white; padding: 10px; text-align: left; }}
    .table-style td {{ border-bottom: 1px solid #eee; padding: 8px 10px; }}
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

# --- メイン表示 ---

# 1. 合計表示
df = load_data()
if not df.empty:
    df['年月'] = df['日付'].apply(lambda x: x.strftime('%Y年%m月'))
    selected_month = st.selectbox("表示月を選択", sorted(df['年月'].unique(), reverse=True))
    filtered_df = df[df['年月'] == selected_month].copy()
else:
    selected_month = ""
    filtered_df = pd.DataFrame(columns=COLS)

filtered_df["金額"] = pd.to_numeric(filtered_df["金額"], errors='coerce').fillna(0)
total = int(filtered_df["金額"].sum())

st.markdown(f'<div class="header-box"><p class="total-t">経費合計</p><p class="total-a">{total:,} 円</p></div>', unsafe_allow_html=True)

# 2. 入力フォーム（間隔を適正化）
st.markdown('<div class="form-title">📝 新規データ入力</div>', unsafe_allow_html=True)

# 1行に2項目並べることで画面の高さを節約（スマホでは自動で縦に並びます）
col1, col2 = st.columns(2)
with col1:
    input_date = st.date_input("日付", date.today())
    payee = st.text_input("支払先", placeholder="例：〇〇コンビニ")
with col2:
    item_name = st.text_input("品名・名目", placeholder="例：消耗品代")
    amount = st.number_input("金額 (円)", min_value=0, step=1)

memo = st.text_area("備考", height=70)

if st.button("登録する", use_container_width=True):
    if payee and amount > 0:
        new_row = pd.DataFrame([[input_date, payee, item_name, memo, amount]], columns=COLS)
        df_all = load_data()
        pd.concat([df_all, new_row], ignore_index=True).to_csv(CSV_FILE, index=False)
        st.success("登録完了！")
        st.rerun()

# 3. 履歴一覧
if not filtered_df.empty:
    st.write(f"### 🗓️ {selected_month} の明細")
    rows = "".join([f"<tr><td>{r['日付']}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}</td></tr>" for _, r in filtered_df.iterrows()])
    st.markdown(f'<table class="table-style"><thead><tr>{"".join([f"<th>{c}</th>" for c in COLS])}</tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
