import streamlit as st
import pandas as pd
import os
from datetime import date

# アプリの設定（ページ全体を広く使う）
st.set_page_config(page_title="経費精算システム", layout="wide")

# --- 独自デザイン（CSS）の適用 ---
st.markdown("""
    <style>
    /* 全体の背景を白に */
    .stApp {
        background-color: white;
    }
    /* ヘッダー部分（合計金額など）のデザイン */
    .custom-header {
        border-bottom: 2px solid #5d6d7e;
        padding-bottom: 10px;
        margin-bottom: 20px;
        display: flex;
        align-items: baseline;
    }
    .total-label {
        font-size: 1.2rem;
        font-weight: bold;
        color: #333;
        margin-right: 20px;
    }
    .total-amount {
        font-size: 2rem;
        font-weight: bold;
        color: #000;
    }
    /* 表のヘッダー色を画像に近づける */
    thead tr th {
        background-color: #5d6d7e !important;
        color: white !important;
    }
    /* 入力フォームの枠をシンプルに */
    div[data-testid="stExpander"] {
        border: 1px solid #ddd;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

CSV_FILE = "expenses.csv"

def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df["日付"] = pd.to_datetime(df["日付"]).dt.date
        return df
    return pd.DataFrame(columns=["日付", "支払先", "品名・名目", "備考", "金額"])

# --- データ入力（折りたたみ式） ---
with st.expander("➕ 新規データ入力"):
    with st.form("input_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            input_date = st.date_input("日付", date.today())
            payee = st.text_input("支払先")
        with col2:
            item_name = st.text_input("品名・名目")
            amount = st.number_input("金額 (円)", min_value=0, step=1, value=0)
        with col3:
            memo = st.text_area("備考", height=100)
        
        submit_button = st.form_submit_button("登録する")

if submit_button:
    if payee and amount > 0:
        new_row = pd.DataFrame([[input_date, payee, item_name, memo, amount]], 
                                columns=["日付", "支払先", "品名・名目", "備考", "金額"])
        df = load_data()
        updated_df = pd.concat([df, new_row], ignore_index=True)
        updated_df.to_csv(CSV_FILE, index=False)
        st.success("登録完了")
        st.rerun() # 画面を更新して合計値を即座に反映

# --- 表示エリア ---
df_display = load_data()

if not df_display.empty:
    # 月選択
    df_display['年月'] = df_display['日付'].apply(lambda x: x.strftime('%Y年%m月'))
    month_list = sorted(df_display['年月'].unique(), reverse=True)
    selected_month = st.selectbox("表示月", month_list)
    
    filtered_df = df_display[df_display['年月'] == selected_month].drop(columns=['年月'])
    
    # 2. 合計金額の表示（見本画像風のレイアウト）
    total = filtered_df["金額"].sum()
    st.markdown(f"""
        <div class="custom-header">
            <span class="total-label">経費合計：</span>
            <span class="total-amount">{total:,} 円</span>
        </div>
    """, unsafe_allow_html=True)

    # 1. 一覧表示（見本画像に近いシンプルな表）
    st.write(f"### {selected_month} の明細")
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("データがありません。")
