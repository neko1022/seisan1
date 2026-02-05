import streamlit as st
import pandas as pd
import os
import base64
import json
from datetime import date
import streamlit.components.v1 as components
import gspread
from google.oauth2.service_account import Credentials

# --- スプレッドシート設定 ---
# 会社用の新しいURL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1dO51vjvj-Q9OH5SRAdP9SxDaGpBcyYgVi_wEE0qGMG0/edit?gid=0#gid=0"

def get_ss_client():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    # Secretsからサービスアカウント情報を読み込み
    service_account_info = json.loads(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    client = gspread.authorize(credentials)
    return client.open_by_url(SPREADSHEET_URL)

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
    
    .table-style {{ width: 100%; border-collapse: collapse; background-color: white; border-radius: 5px; table-layout: fixed; }}
    .table-style th {{ background: #71018C; color: white; padding: 8px 5px; text-align: left; font-size: 0.8rem; }}
    .table-style td {{ border-bottom: 1px solid #eee; padding: 10px 5px; color: #333; font-size: 0.8rem; word-wrap: break-word; }}

    .col-date {{ width: 10%; }}
    .col-payee {{ width: 20%; }}
    .col-item {{ width: 20%; }}
    .col-memo {{ width: 30%; }}
    .col-amount {{ width: 20%; }}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- 処理 ---
USER_FILE = "namae.txt"
COLS = ["名前", "日付", "支払先", "品名・名目", "備考", "金額"]

@st.cache_data(ttl=60)
def load_data():
    try:
        ss = get_ss_client()
        sheet = ss.worksheet("expenses") # タブ名を確認
        data = sheet.get_all_records()
        if not data: return pd.DataFrame(columns=COLS)
        df = pd.DataFrame(data)
        df["日付"] = pd.to_datetime(df["日付"]).dt.date
        return df.fillna("")
    except: return pd.DataFrame(columns=COLS)

def load_users():
    users = {}
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2: users[parts[0]] = parts[1]
    return users

df_all = load_data()
user_dict = load_users()
ADMIN_PASS = "1234"

# --- 画面構成 ---
is_admin = st.toggle("🛠️ 管理者モードに切り替え")

if is_admin:
    pwd = st.text_input("管理者パスワード", type="password")
    if pwd == ADMIN_PASS:
        st.markdown('<div class="form-title">📊 管理者用：全体集計パネル</div>', unsafe_allow_html=True)
        if not df_all.empty:
            df_all['年月'] = df_all['日付'].apply(lambda x: x.strftime('%Y年%m月'))
            target_month = st.selectbox("集計月", sorted(df_all['年月'].unique(), reverse=True))
            admin_df = df_all[df_all['年月'] == target_month].copy()
            st.markdown(f'<div class="header-box"><p class="total-label">{target_month} 全員合計</p><p class="total-a">{int(admin_df["金額"].sum()):,} 円</p></div>', unsafe_allow_html=True)
            
            user_summary = admin_df.groupby("名前")["金額"].sum().reset_index()
            for idx, row in user_summary.iterrows():
                c_sw, c_nm, c_at = st.columns([1, 2, 2])
                with c_sw: show_det = st.toggle("明細", key=f"det_{idx}")
                with c_nm: st.write(f"**{row['名前']}**")
                with c_at: st.write(f"{int(row['金額']):,} 円")
                if show_det:
                    u_det = admin_df[admin_df["名前"] == row["名前"]].copy()
                    rows_html = "".join([f"<tr><td>{r['日付'].strftime('%m-%d')}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}円</td></tr>" for _, r in u_det.iterrows()])
                    st.markdown(f'<table class="table-style"><thead><tr><th class="col-date">日付</th><th class="col-payee">支払先</th><th class="col-item">品名</th><th class="col-memo">備考</th><th class="col-amount">金額</th></tr></thead><tbody>{rows_html}</tbody></table>', unsafe_allow_html=True)
                st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
else:
    name_list = list(user_dict.keys())
    selected_user = st.selectbox("名前を選択", ["選択してください"] + name_list)
    
    if selected_user != "選択してください":
        user_pwd = st.text_input("パスワード", type="password")
        if user_pwd == user_dict.get(selected_user):
            df_all['年月'] = df_all['日付'].apply(lambda x: x.strftime('%Y年%m月')) if not df_all.empty else ""
            month_list = sorted(df_all['年月'].unique(), reverse=True) if not df_all.empty else [date.today().strftime('%Y年%m月')]
            selected_month = st.selectbox("表示月", month_list)
            filtered_df = df_all[(df_all['年月'] == selected_month) & (df_all['名前'] == selected_user)].copy() if not df_all.empty else pd.DataFrame(columns=COLS)
            
            st.markdown(f'<div class="header-box"><p class="total-label">{selected_user} さんの合計</p><p class="total-a">{int(filtered_df["金額"].sum()):,} 円</p></div>', unsafe_allow_html=True)

            st.markdown('<div class="form-title">📝 新規入力</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                input_date = st.date_input("日付", date.today())
                payee = st.text_input("支払先", placeholder="例：〇〇商事")
            with c2:
                item_name = st.text_input("品名・名目", placeholder="例：交通費")
                amount_str = st.text_input("金額 (円)", placeholder="数字を入力")
            memo = st.text_area("備考", placeholder="補足があれば入力", height=70)

            if st.button("登録する", use_container_width=True):
                clean_amount = "".join(filter(str.isdigit, amount_str))
                amount_val = int(clean_amount) if clean_amount else 0
                if amount_val > 0:
                    try:
                        ss = get_ss_client()
                        sheet = ss.worksheet("expenses")
                        new_row = [selected_user, input_date.strftime("%Y/%m/%d"), payee, item_name, memo, amount_val]
                        sheet.append_row(new_row)
                        st.cache_data.clear() 
                        st.success("登録完了！")
                        st.rerun()
                    except Exception as e: st.error(f"エラー: {e}")
                else: st.warning("金額を入力してください。")

            if not filtered_df.empty:
                st.markdown("---")
                st.write("### 🗓️ 明細履歴")
                delete_mode = st.toggle("🗑️ 編集・削除モード")
                if delete_mode:
                    for idx, row in filtered_df.iterrows():
                        cols = st.columns([5, 1])
                        with cols[0]: st.write(f"【{row['日付'].strftime('%m-%d')}】 {row['支払先']} / {int(row['金額']):,}円")
                        with cols[1]:
                            if st.button("🗑️", key=f"del_{idx}"):
                                try:
                                    ss = get_ss_client()
                                    sheet = ss.worksheet("expenses")
                                    # ボタンが押された瞬間のシート実データを取得
                                    all_vals = sheet.get_all_values()
                                    target_row = -1
                                    
                                    # 行特定を厳密にするための変数
                                    s_name = str(row['名前']).strip()
                                    s_date = row['日付'].strftime("%Y/%m/%d")
                                    s_amount = str(int(row['金額']))
                                    
                                    for i, v in enumerate(all_vals):
                                        if i == 0: continue
                                        if (len(v) >= 6 and 
                                            str(v[0]).strip() == s_name and 
                                            str(v[1]).replace("-", "/") == s_date and 
                                            str(v[5]).replace(",", "").strip() == s_amount):
                                            target_row = i + 1
                                            break
                                    
                                    if target_row > 0:
                                        # 削除を実行したら、その結果を待たずに即キャッシュクリアしてリロード
                                        sheet.delete_rows(target_row)
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        # もし行が見つからない場合は、すでに消えている可能性が高いのでリロード
                                        st.cache_data.clear()
                                        st.rerun()
                                except:
                                    # エラーが発生しても、念のため画面をリロードして整合性を取る
                                    st.cache_data.clear()
                                    st.rerun()
                else:
                    rows_html = "".join([f"<tr><td>{r['日付'].strftime('%m-%d')}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}円</td></tr>" for _, r in filtered_df.iterrows()])
                    st.markdown(f'<table class="table-style"><thead><tr><th class="col-date">日付</th><th class="col-payee">支払先</th><th class="col-item">品名</th><th class="col-memo">備考</th><th class="col-amount">金額</th></tr></thead><tbody>{rows_html}</tbody></table>', unsafe_allow_html=True)

components.html("""
<script>
const doc = window.parent.document;
setInterval(() => {
    doc.querySelectorAll('input').forEach(input => {
        if (input.ariaLabel && input.ariaLabel.includes('金額')) {
            input.type = 'number'; input.inputMode = 'numeric';
        }
    });
}, 1000);
</script>""", height=0)
