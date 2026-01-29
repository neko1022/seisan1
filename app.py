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
    
    header, [data-testid="stHeader"], [data-testid="collapsedControl"] {{
        display: none !important;
    }}

    .stApp {{ background-color: #DEBCE5 !important; }}
    .header-box {{ border-bottom: 3px solid #71018C; padding: 10px 0; margin-bottom: 20px; }}
    .total-label {{ font-size: 1.1rem; color: #444; margin-bottom: 5px; font-weight: bold; }}
    .total-a {{ font-size: 2.2rem; font-weight: bold; color: #71018C; margin: 0; }}
    .form-title {{ background: #71018C; color: white; padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; }}
    .stButton>button {{ background-color: #71018C !important; color: white !important; border-radius: 25px !important; font-weight: bold !important; }}
    
    /* 入力ラベルのデザイン設定 */
    .custom-label {{
        font-weight: bold;
        font-size: 0.95rem;
        margin-right: 15px;
        color: #333;
    }}

    /* ★ここが「🗓️ 明細履歴」専用の設定★ */
    .history-header {{
        font-size: 1.2rem; /* ここを大きくすると文字が大きくなります */
        color: #71018C;
        font-weight: bold;
        margin: 25px 0 10px 0;
    }}

    .table-style {{ width: 100%; border-collapse: collapse; background-color: white; border-radius: 5px; table-layout: fixed; }}
    .table-style th {{ background: #71018C; color: white; padding: 8px 5px; text-align: left; font-size: 0.8rem; }}
    .table-style td {{ border-bottom: 1px solid #eee; padding: 10px 5px; color: #333; font-size: 0.8rem; word-wrap: break-word; }}
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
            if "名前" not in df.columns:
                df.insert(0, "名前", "山田太郎")
            df["日付"] = pd.to_datetime(df["日付"]).dt.date
            return df.fillna("")
        except:
            return pd.DataFrame(columns=COLS)
    return pd.DataFrame(columns=COLS)

df_all = load_data()

USER_PASS = "0000" 
ADMIN_PASS = "1234"

# --- 画面構成 ---
is_admin = st.toggle("🛠️ 管理者モードに切り替え")

if is_admin:
    pwd = st.text_input("管理者パスワード", type="password")
    if pwd == ADMIN_PASS:
        st.markdown('<div class="form-title">📊 管理者用パネル</div>', unsafe_allow_html=True)
        # 管理者コード省略（データ表示等）
else:
    # 個人申請モード
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        name_list = ["山田太郎", "佐藤花子", "鈴木一郎"] 
        selected_user = st.selectbox("名前を選択", ["選択してください"] + name_list)
    
    if selected_user != "選択してください":
        user_pwd = st.text_input(f"{selected_user} さんのパスワード", type="password")
        
        if user_pwd == USER_PASS:
            df_all['年月'] = df_all['日付'].apply(lambda x: x.strftime('%Y年%m月')) if not df_all.empty else ""
            month_list = sorted(df_all['年月'].unique(), reverse=True) if not df_all.empty else []
            
            with col_s2:
                selected_month = st.selectbox("表示月", month_list) if month_list else ""
            
            if selected_month:
                filtered_df = df_all[(df_all['年月'] == selected_month) & (df_all['名前'] == selected_user)].copy()
            else:
                filtered_df = pd.DataFrame(columns=COLS)

            # 合計金額表示
            total_val = filtered_df["金額"].sum() if not filtered_df.empty else 0
            st.markdown(f'<div class="header-box"><p class="total-label">{selected_user} さんの合計</p><p class="total-a">{int(total_val):,} 円</p></div>', unsafe_allow_html=True)

            # 新規入力フォーム
            st.markdown('<div class="form-title">📝 新規入力</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<span class="custom-label">日付</span>', unsafe_allow_html=True)
                input_date = st.date_input("d", date.today(), label_visibility="collapsed")
                
                # ラベルとチェックボックスを横に並べる配置
                col_l1, col_c1 = st.columns([1, 1])
                with col_l1: st.markdown('<span class="custom-label">支払先</span>', unsafe_allow_html=True)
                with col_c1: pay_hist = st.checkbox("履歴選択", key="pay_hist")
                
                if pay_hist and not df_all.empty:
                    payee = st.selectbox("p", sorted(df_all["支払先"].unique()), label_visibility="collapsed")
                else:
                    payee = st.text_input("p", placeholder="例：〇〇商事", label_visibility="collapsed")
                
            with c2:
                col_l2, col_c2 = st.columns([1, 1])
                with col_l2: st.markdown('<span class="custom-label">品名・名目</span>', unsafe_allow_html=True)
                with col_c2: item_hist = st.checkbox("履歴選択", key="item_hist")
                
                if item_hist and not df_all.empty:
                    item_name = st.selectbox("i", sorted(df_all["品名・名目"].unique()), label_visibility="collapsed")
                else:
                    item_name = st.text_input("i", placeholder="例：交通費", label_visibility="collapsed")

                st.markdown('<span class="custom-label">金額 (円)</span>', unsafe_allow_html=True)
                amount_str = st.text_input("a", placeholder="数字を入力", label_visibility="collapsed")

            st.markdown('<span class="custom-label">備考</span>', unsafe_allow_html=True)
            memo = st.text_area("m", placeholder="補足があれば入力", height=70, label_visibility="collapsed")

            if st.button("登録する", use_container_width=True):
                # 登録ロジック
                pass

            st.markdown("---")
            
            # --- ここが修正ポイント：明細履歴の表示 ---
            if not filtered_df.empty:
                # ★作成したCSSクラス「history-header」をここで使用★
                st.markdown('<div class="history-header">🗓️ 明細履歴</div>', unsafe_allow_html=True)
                
                delete_mode = st.toggle("🗑️ 編集・削除モード")
                if delete_mode:
                    for idx, row in filtered_df.iterrows():
                        cols = st.columns([5, 1])
                        with cols[0]: st.write(f"【{row['日付'].strftime('%m-%d')}】 {row['支払先']} / {int(row['金額']):,}円")
                        with cols[1]:
                            if st.button("🗑️", key=f"del_{idx}"):
                                # 削除ロジック
                                pass
                else:
                    rows_html = "".join([f"<tr><td>{r['日付'].strftime('%m-%d')}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}円</td></tr>" for _, r in filtered_df.iterrows()])
                    st.markdown(f'<table class="table-style"><thead><tr><th class="col-date">日付</th><th class="col-payee">支払先</th><th class="col-item">品名</th><th class="col-memo">備考</th><th class="col-amount">金額</th></tr></thead><tbody>{rows_html}</tbody></table>', unsafe_allow_html=True)

# JavaScript省略（テンキー対応）
