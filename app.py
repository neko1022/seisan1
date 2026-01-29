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
    
    header, [data-testid="stHeader"], [data-testid="collapsedControl"], .st-emotion-cache-6qob1r {{
        display: none !important;
        height: 0px !important;
    }}

    .stApp {{ background-color: #DEBCE5 !important; }}
    .header-box {{ border-bottom: 3px solid #71018C; padding: 10px 0; margin-bottom: 20px; }}
    .total-label {{ font-size: 1.1rem; color: #444; margin-bottom: 5px; font-weight: bold; }}
    .total-a {{ font-size: 2.2rem; font-weight: bold; color: #71018C; margin: 0; }}
    .form-title {{ background: #71018C; color: white; padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; }}
    .stButton>button {{ background-color: #71018C !important; color: white !important; border-radius: 25px !important; font-weight: bold !important; }}
    
    .table-style {{ width: 100%; border-collapse: collapse; background-color: white; border-radius: 5px; table-layout: fixed; }}
    .table-style th {{ background: #71018C; color: white; padding: 8px 5px; text-align: left; font-size: 0.8rem; }}
    .table-style td {{ border-bottom: 1px solid #eee; padding: 10px 5px; color: #333; font-size: 0.8rem; word-wrap: break-word; }}

    .col-date {{ width: 55px; }}
    .col-payee {{ width: 22%; }}
    .col-item {{ width: 22%; }}
    .col-memo {{ width: auto; }}
    .col-amount {{ width: 85px; }}

    .custom-suggestion-list {{
        position: absolute; z-index: 1000; background: white; border: 1px solid #ddd;
        border-radius: 5px; max-height: 150px; overflow-y: auto; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        width: 100%; display: none;
    }}
    .suggestion-item {{ padding: 8px 12px; cursor: pointer; font-size: 0.9rem; border-bottom: 1px solid #f0f0f0; }}
    .suggestion-item:hover {{ background-color: #f7e6f9; }}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- 安定版データ処理 ---
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

# アプリ起動時にデータを読み込む
df_all = load_data()

def get_h(col):
    return sorted([str(x) for x in df_all[col].unique() if str(x).strip() != ""])

payee_h = get_h("支払先")
item_h = get_h("品名・名目")
memo_h = get_h("備考")

USER_PASS = "0000" 
ADMIN_PASS = "1234"

# --- 画面構成 ---
is_admin = st.toggle("🛠️ 管理者モードに切り替え (上司専用)")

if is_admin:
    # --- 管理者画面（変更なし） ---
    pwd = st.text_input("管理者パスワード", type="password")
    if pwd == ADMIN_PASS:
        st.markdown('<div class="form-title">📊 管理者用：全体集計パネル</div>', unsafe_allow_html=True)
        if not df_all.empty:
            df_all['年月'] = df_all['日付'].apply(lambda x: x.strftime('%Y年%m月'))
            target_month = st.selectbox("集計月", sorted(df_all['年月'].unique(), reverse=True))
            admin_df = df_all[df_all['年月'] == target_month].copy()
            total_admin = admin_df["金額"].sum()
            st.markdown(f'<div class="header-box"><p class="total-label">{target_month} 全員合計</p><p class="total-a">{int(total_admin):,} 円</p></div>', unsafe_allow_html=True)
            
            user_summary = admin_df.groupby("名前")["金額"].sum().reset_index()
            for idx, row in user_summary.iterrows():
                c_switch, c_name, c_amt = st.columns([1, 2, 2])
                with c_switch: show_detail = st.toggle("明細", key=f"details_{idx}")
                with c_name: st.write(f"**{row['名前']}**")
                with c_amt: st.write(f"{int(row['金額']):,} 円")
                if show_detail:
                    u_detail = admin_df[admin_df["名前"] == row["名前"]].copy()
                    rows_html = "".join([f"<tr><td>{r['日付'].strftime('%m-%d')}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}円</td></tr>" for _, r in u_detail.iterrows()])
                    st.markdown(f'<table class="table-style"><thead><tr><th class="col-date">日付</th><th class="col-payee">支払先</th><th class="col-item">品名</th><th class="col-memo">備考</th><th class="col-amount">金額</th></tr></thead><tbody>{rows_html}</tbody></table>', unsafe_allow_html=True)
                st.markdown("<hr style='margin:5px 0; border:0.5px solid #eee;'>", unsafe_allow_html=True)
            
            csv_data = admin_df.drop(columns=['年月']).to_csv(index=False).encode('utf_8_sig')
            st.download_button(label="📥 CSVダウンロード", data=csv_data, file_name=f"集計_{target_month}.csv", mime='text/csv')
    elif pwd != "":
        st.error("パスワードが違います")
else:
    # --- 個人申請モード（不具合修正版） ---
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        name_list = ["山田太郎", "佐藤花子", "鈴木一郎"] 
        selected_user = st.selectbox("名前を選択", ["選択してください"] + name_list)
    
    if selected_user != "選択してください":
        user_pwd = st.text_input(f"{selected_user} さんのパスワード", type="password")
        
        if user_pwd == USER_PASS:
            # ここで最新のデータをフィルタリング
            df_all['年月'] = df_all['日付'].apply(lambda x: x.strftime('%Y年%m月')) if not df_all.empty else ""
            month_list = sorted(df_all['年月'].unique(), reverse=True) if not df_all.empty else []
            
            with col_s2:
                selected_month = st.selectbox("表示月", month_list) if month_list else ""
            
            # フィルタリング条件を確実に適用
            if selected_month:
                filtered_df = df_all[(df_all['年月'] == selected_month) & (df_all['名前'] == selected_user)].copy()
            else:
                filtered_df = pd.DataFrame(columns=COLS)

            total_val = filtered_df["金額"].sum() if not filtered_df.empty else 0
            st.markdown(f'<div class="header-box"><p class="total-label">{selected_user} さんの合計</p><p class="total-a">{int(total_val):,} 円</p></div>', unsafe_allow_html=True)

            # 新規入力フォーム
            st.markdown(f'<div class="form-title">📝 新規入力</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                input_date = st.date_input("日付", date.today())
                payee = st.text_input("支払先", placeholder="例：〇〇商事", key="payee_in")
            with c2:
                item_name = st.text_input("品名・名目", placeholder="例：交通費", key="item_in")
                amount_str = st.text_input("金額 (円)", placeholder="数字を入力")
            memo = st.text_area("備考", placeholder="補足があれば入力", height=70, key="memo_in")

            if st.button("登録する", use_container_width=True):
                clean_amount = "".join(filter(str.isdigit, amount_str))
                amount_val = int(clean_amount) if clean_amount else 0
                if amount_val > 0 and payee != "" and item_name != "":
                    # 保存用のデータフレーム作成
                    new_row = pd.DataFrame([[selected_user, input_date, payee, item_name, memo, amount_val]], columns=COLS)
                    # 既存データと結合して保存（年月カラムは除外）
                    df_for_save = df_all.drop(columns=['年月'], errors='ignore')
                    updated_df = pd.concat([df_for_save, new_row], ignore_index=True)
                    updated_df.to_csv(CSV_FILE, index=False)
                    st.success("登録完了！")
                    st.rerun() # 画面をリロードして反映させる
                else:
                    st.warning("項目を正しく入力してください。")

            st.markdown("---")
            if not filtered_df.empty:
                st.write("### 🗓️ 明細履歴")
                delete_mode = st.toggle("🗑️ 編集・削除モード")
                if delete_mode:
                    for idx, row in filtered_df.iterrows():
                        cols = st.columns([5, 1])
                        with cols[0]: st.write(f"【{row['日付'].strftime('%m-%d')}】 {row['支払先']} / {int
