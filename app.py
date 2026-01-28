import streamlit as st
import pandas as pd
import os
from datetime import date

# アプリの設定
st.set_page_config(page_title="経費精算アプリ", layout="centered")
st.title("📑 経費精算アプリ")

CSV_FILE = "expenses.csv"

# データの読み込み
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        # 日付列を日付型に変換
        df["日付"] = pd.to_datetime(df["日付"]).dt.date
        return df
    else:
        # Excelのヘッダーをイメージした構成
        return pd.DataFrame(columns=["日付", "支払先", "品名・名目", "備考", "金額"])

# --- 入力エリア ---
with st.expander("➕ 新規データを入力する", expanded=True):
    with st.form("input_form", clear_on_submit=True):
        input_date = st.date_input("日付", date.today())
        payee = st.text_input("支払先 (例: 〇〇商事)")
        item_name = st.text_input("品名・名目 (例: 文房具代)")
        memo = st.text_area("備考")
        
        # step=1を指定し、number_inputを使うことでスマホでテンキーが出やすくなります
        amount = st.number_input("金額 (円)", min_value=0, step=1, value=0)
        
        submit_button = st.form_submit_button("Excelに書き込むイメージで登録")

# 登録処理
if submit_button:
    if payee and amount > 0:
        new_row = pd.DataFrame([[input_date, payee, item_name, memo, amount]], 
                                columns=["日付", "支払先", "品名・名目", "備考", "金額"])
        df = load_data()
        updated_df = pd.concat([df, new_row], ignore_index=True)
        updated_df.to_csv(CSV_FILE, index=False)
        st.success("登録しました！")
    else:
        st.error("「支払先」と「金額」を入力してください。")

# --- 表示・集計エリア ---
st.divider()

df_display = load_data()

if not df_display.empty:
    # 3. 過去の履歴を年月でフィルタリング
    df_display['年月'] = df_display['日付'].apply(lambda x: x.strftime('%Y年%m月'))
    month_list = sorted(df_display['年月'].unique(), reverse=True)
    selected_month = st.selectbox("表示する月を選択", month_list)
    
    # 選択された月のデータのみ抽出
    filtered_df = df_display[df_display['年月'] == selected_month].drop(columns=['年月'])
    
    # 2. 合計金額の表示
    total_amount = filtered_df["金額"].sum()
    st.metric(label=f"{selected_month} の合計精算額", value=f"{total_amount:,} 円")
    
    # 1. Excel風の一覧表示
    st.write(f"### {selected_month} の明細")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
else:
    st.info("まだデータがありません。上のフォームから入力してください。")
