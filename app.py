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

# --- デザイン（HTML/CSSだけで構築） ---
css_code = f"""
<style>
    @font-face {{
        font-family: 'Mochiy Pop One';
        src: url(data:font/ttf;base64,{font_base64}) format('truetype');
    }}

    * {{ font-family: 'Mochiy Pop One', sans-serif !important; }}

    /* ヘッダー */
    .header-box {{
        border-bottom: 3px solid #5d6d7e;
        padding: 20px 0;
        margin-bottom: 40px;
    }}
    .total-t {{ font-size: 1.2rem; color: #666; margin: 0; }}
    .total-a {{ font-size: 2.5rem; font-weight: bold; color: #000; margin: 5px 0 0 0; }}

    /* 入力エリアのタイトル */
    .form-title {{
        background: #5d6d7e;
        color: white;
        padding: 10px;
        border-radius: 5px 5px 0 0;
        margin-top: 20px;
    }}

    /* テーブル */
    .table-style {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }}
    .table-style th {{ background: #5d6d7e; color: white; padding: 12px; text-align: left; }}
    .table-style td {{ border-bottom: 1px solid #eee; padding: 12px; }}

    /* Streamlit標準の要素に大きな余白を強制 */
    div[data-testid="stVerticalBlock"] > div {{
        margin-bottom: 25px !important;
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

# --- メイン表示 ---

# 1. 合計表示
df = load_data()
df['年月'] = df['日付'].apply(lambda x: x.strftime('%Y年%m月')) if not df.empty else ""
selected_month = st.selectbox("表示月を選択", sorted(df['年月'].unique(), reverse=True)) if not df.empty else ""

filtered_df = df[df['年月'] == selected_month].copy() if not df.empty else pd.DataFrame(columns=COLS)
filtered_df["金額"] = pd.to_numeric(filtered_df["金額"], errors='coerce').fillna(0)
total = int(filtered_df["金額"].sum())

st.markdown(f'<div class="header-box"><p class="total-t">経費合計</p><p class="total-a">{total:,} 円</p></div>', unsafe_allow_html=True)

# 2. 入力フォーム（余白を最大化）
st.markdown('<div class="form-title">📝 新規データ入力</div>', unsafe_allow_html=True)

# 各項目の間に空行を挟んで配置
input_date = st.date_input("【日付】", date.today())
st.write("---")
payee = st.text_input("【支払先】", placeholder="例：〇〇コンビニ")
st.write("---")
item_name = st.text_input("【品名・名目】", placeholder="例：消耗品代")
st.write("---")
amount = st.number_input("【金額 (円)】", min_value=0, step=1)
st.write("---")
memo = st.text_area("【備考】")

if st.button("この内容で登録する", use_container_width=True):
    if payee and amount > 0:
        new_row = pd.DataFrame([[input_date, payee, item_name, memo, amount]], columns=COLS)
        df_all = load_data()
        pd.concat([df_all, new_row], ignore_index=True).to_csv(CSV_FILE, index=False)
        st.success("登録しました！")
        st.rerun()
    else:
        st.warning("支払先と金額を入力してください。")

# 3. 履歴一覧
if not filtered_df.empty:
    st.markdown(f"### 🗓️ {selected_month} の明細")
    rows = "".join([f"<tr><td>{r['日付']}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}</td></tr>" for _, r in filtered_df.iterrows()])
    st.markdown(f'<table class="table-style"><thead><tr>{"".join([f"<th>{c}</th>" for c in COLS])}</tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
