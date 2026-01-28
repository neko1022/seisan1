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

# --- デザイン（色指定：R113, G1, B140 & R222, G188, B229） ---
css_code = f"""
<style>
    @font-face {{
        font-family: 'Mochiy Pop One';
        src: url(data:font/ttf;base64,{font_base64}) format('truetype');
    }}

    * {{ font-family: 'Mochiy Pop One', sans-serif !important; }}

    /* 全体の背景色（薄い部分） */
    .stApp {{
        background-color: #DEBCE5 !important;
    }}

    /* ヘッダーエリア（濃い部分の線） */
    .header-box {{
        border-bottom: 3px solid #71018C;
        padding: 10px 0;
        margin-bottom: 20px;
    }}
    .total-t {{ font-size: 1.0rem; color: #444; margin-bottom: 5px; }}
    .total-a {{ font-size: 2.2rem; font-weight: bold; color: #71018C; margin: 0; }}

    /* 入力エリアのタイトル（濃い部分） */
    .form-title {{
        background: #71018C;
        color: white;
        padding: 8px 15px;
        border-radius: 5px;
        font-size: 1.1rem;
        margin-bottom: 15px;
    }}

    /* 登録ボタン（濃い部分） */
    .stButton>button {{
        background-color: #71018C !important;
        color: white !important;
        border-radius: 25px !important;
        border: none !important;
        height: 3em !important;
        font-weight: bold !important;
        margin-top: 10px;
    }}

    /* テーブル設定 */
    .table-style {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
        font-size: 0.9rem;
        background-color: white;
    }}
    .table-style th {{ background: #71018C; color: white; padding: 12px; text-align: left; }}
    .table-style td {{ border-bottom: 1px solid #ddd; padding: 10px; color: #333; }}

    /* 入力項目のラベル */
    label[data-testid="stWidgetLabel"] p {{
        color: #333 !important;
        font-weight: bold !important;
    }}
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

# --- メイン画面 ---

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

# 2. 入力フォーム
st.markdown('<div class="form-title">📝 新規データ入力</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    input_date = st.date_input("日付", date.today())
    payee = st.text_input("支払先", placeholder="例：〇〇商事")
with col2:
    item_name = st.text_input("品名・名目", placeholder="例：交通費")
    # 修正：初期値を空にするため text_input を使用（スマホで数字キーボードを出すヒント付き）
    amount_str = st.text_input("金額 (円)", placeholder="数字を入力してください")

memo = st.text_area("備考", height=70)

if st.button("登録する", use_container_width=True):
    # 数値変換のチェック
    try:
        amount_val = int(amount_str.replace(",", "")) if amount_str else 0
    except ValueError:
        st.error("金額には数字を入力してください。")
        amount_val = 0

    if payee and amount_val > 0:
        new_row = pd.DataFrame([[input_date, payee, item_name, memo, amount_val]], columns=COLS)
        df_all = load_data()
        pd.concat([df_all, new_row], ignore_index=True).to_csv(CSV_FILE, index=False)
        st.success("登録しました！")
        st.rerun()
    elif not payee:
        st.warning("支払先を入力してください。")
    elif amount_val <= 0:
        st.warning("金額を正しく入力してください。")

# 3. 履歴一覧
if not filtered_df.empty:
    st.write(f"### 🗓️ {selected_month} の明細")
    rows = "".join([f"<tr><td>{r['日付']}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}</td></tr>" for _, r in filtered_df.iterrows()])
    st.markdown(f'<table class="table-style"><thead><tr>{"".join([f"<th>{c}</th>" for c in COLS])}</tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
