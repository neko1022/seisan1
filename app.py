import streamlit as st
import pandas as pd
import os
from datetime import date

# --- アプリの設定 (VBAのUserFormの初期設定のようなもの) ---
st.set_page_config(page_title="交通費精算アプリ", layout="centered")
st.title("🚗 交通費精算アプリ")

# データ保存用のファイル名 (VBAでいう保存先ブック名)
CSV_FILE = "expenses.csv"

# --- データの読み込み関数 (VBAのWorkbooks.Openに相当) ---
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        # ファイルがない場合は空の表を作る (VBAのDimで構造を決めるイメージ)
        return pd.DataFrame(columns=["日付", "訪問先", "金額", "備考"])

# --- 入力フォーム (VBAのテキストボックスやラベルの配置) ---
with st.form("input_form"):
    st.subheader("新規入力")
    input_date = st.date_input("日付", date.today())
    destination = st.text_input("訪問先")
    amount = st.number_input("金額", min_value=0, step=10)
    memo = st.text_area("備考")
    
    # 送信ボタン (VBAのCommandButton_Clickイベント)
    submit_button = st.form_submit_button("登録する")

# --- 登録処理 (VBAの「最終行を取得して値を書き込む」処理) ---
if submit_button:
    if destination and amount > 0:
        # 新しい行を作成
        new_data = pd.DataFrame([[input_date, destination, amount, memo]], 
                                columns=["日付", "訪問先", "金額", "備考"])
        
        # 既存データに結合 (VBAの .End(xlUp).Offset(1) で追加するイメージ)
        df = load_data()
        updated_df = pd.concat([df, new_data], ignore_index=True)
        
        # CSVへ保存 (VBAの ActiveWorkbook.Save)
        updated_df.to_csv(CSV_FILE, index=False)
        st.success("登録完了しました！")
    else:
        st.error("訪問先と金額を入力してください。")

# --- 一覧表示 (VBAのリストボックスやセル範囲を表示するイメージ) ---
st.divider()
st.subheader("精算データ一覧")
display_df = load_data()

if not display_df.empty:
    st.dataframe(display_df, use_container_width=True)
    
    # 合計金額の表示 (VBAの WorksheetFunction.Sum)
    total = display_df["金額"].sum()
    st.metric("合計金額", f"{total:,} 円")
else:
    st.info("データはまだありません。")
