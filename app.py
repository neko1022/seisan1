import streamlit as st
import pandas as pd
import os
import base64
from datetime import date
import streamlit.components.v1 as components

# ページ設定
st.set_page_config(page_title="経費精算システム", layout="wide")

# --- フォント・CSS設定 ---
def get_base64_font(font_file):
    if os.path.exists(font_file):
        with open(font_file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

font_base64 = get_base64_font("MochiyPopOne-Regular.ttf")

css_code = f"""
<style>
    @font-face {{
        font-family: 'Mochiy Pop One';
        src: url(data:font/ttf;base64,{font_base64}) format('truetype');
    }}
    * {{ font-family: 'Mochiy Pop One', sans-serif !important; }}
    header, [data-testid="stHeader"] {{ display: none !important; }}

    .stApp {{ background-color: #DEBCE5 !important; }}
    .form-title {{ background: #71018C; color: white; padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; }}

    /* ★ 項目名とボタンを密着させて横並びにするための設定 ★ */
    .item-row {{
        display: flex;
        align-items: center; /* 上下中央を揃える */
        gap: 0px;            /* 文字とボタンの間の隙間をゼロにする */
        height: 40px;        /* 高さを一定にする */
    }}
    .item-label {{
        font-weight: bold;
        font-size: 1.0rem;
        margin-right: 5px;   /* 文字の直後に少しだけ隙間を作る */
    }}
    
    /* チェックボックスの外枠を消して文字に近づける */
    div[data-testid="stCheckbox"] {{
        width: auto !important;
        min-width: 0 !important;
        margin-top: 0 !important;
    }}
    div[data-testid="stCheckbox"] label {{
        margin: 0 !important;
        padding: 0 !important;
    }}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- データ処理 ---
CSV_FILE = "expenses.csv"
COLS = ["名前", "日付", "支払先", "品名・名目", "備考", "金額"]
def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            if "名前" not in df.columns: df.insert(0, "名前", "山田太郎")
            df["日付"] = pd.to_datetime(df["日付"]).dt.date
            return df.fillna("")
        except: return pd.DataFrame(columns=COLS)
    return pd.DataFrame(columns=COLS)

df_all = load_data()
def get_h(col): return sorted([str(x) for x in df_all[col].unique() if str(x).strip() != ""])

# --- 画面 ---
name_list = ["山田太郎", "佐藤花子", "鈴木一郎"] 
selected_user = st.selectbox("名前を選択", ["選択してください"] + name_list)

if selected_user != "選択してください":
    user_pwd = st.text_input(f"{selected_user} さんのパスワード", type="password")
    if user_pwd == "0000":
        st.markdown('<div class="form-title">📝 新規入力</div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("**日付**")
            input_date = st.date_input("日付", date.today(), label_visibility="collapsed")
            
            # 支払先：文字とボタンを一つの枠に入れて横に並べる
            st.markdown('<div class="item-row"><span class="item-label">支払先</span>', unsafe_allow_html=True)
            use_p_h = st.checkbox("履歴選択", key="use_p_h")
            st.markdown('</div>', unsafe_allow_html=True)
            if use_p_h:
                payee = st.selectbox("支払先履歴", [""] + get_h("支払先"), label_visibility="collapsed")
            else:
                payee = st.text_input("支払先手入力", placeholder="例：〇〇商事", label_visibility="collapsed")
                
        with c2:
            # 品名：文字とボタンを一つの枠に入れて横に並べる
            st.markdown('<div class="item-row"><span class="item-label">品名・名目</span>', unsafe_allow_html=True)
            use_i_h = st.checkbox("履歴選択", key="use_i_h")
            st.markdown('</div>', unsafe_allow_html=True)
            if use_i_h:
                item_name = st.selectbox("品名履歴", [""] + get_h("品名・名目"), label_visibility="collapsed")
            else:
                item_name = st.text_input("品名手入力", placeholder="例：交通費", label_visibility="collapsed")
            
            st.write("**金額 (円)**")
            amount_str = st.text_input("金額", placeholder="数字を入力", label_visibility="collapsed")

        if st.button("登録する", use_container_width=True):
            clean_amount = "".join(filter(str.isdigit, amount_str))
            if clean_amount and int(clean_amount) > 0:
                new_row = pd.DataFrame([[selected_user, input_date, payee, item_name, "", int(clean_amount)]], columns=COLS)
                pd.concat([df_all, new_row], ignore_index=True).to_csv(CSV_FILE, index=False)
                st.success("登録しました")
                st.rerun()
