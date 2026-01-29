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
    header[data-testid="stHeader"], [data-testid="collapsedControl"] {{ display: none !important; }}
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
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- データ処理関数 ---
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

# --- 履歴取得関数 ---
def get_history(column_name):
    if column_name in df_all.columns:
        return sorted([str(x) for x in df_all[column_name].unique() if str(x).strip() != ""])
    return []

# --- 1. 共通の表示・登録用設定 ---
is_admin = st.toggle("🛠️ 管理者モードに切り替え (上司専用)")

if is_admin:
    # --- 管理者画面 ---
    pwd = st.text_input("パスワードを入力してください", type="password")
    if pwd == "1234":
        st.markdown('<div class="form-title">📊 管理者用：全体集計パネル</div>', unsafe_allow_html=True)
        if not df_all.empty:
            df_all['年月'] = df_all['日付'].apply(lambda x: x.strftime('%Y年%m月'))
            target_month = st.selectbox("集計月を選択", sorted(df_all['年月'].unique(), reverse=True))
            admin_df = df_all[df_all['年月'] == target_month].copy()
            total_admin = admin_df["金額"].sum()
            st.markdown(f'<div class="header-box"><p class="total-label">{target_month} 全員合計</p><p class="total-a">{int(total_admin):,} 円</p></div>', unsafe_allow_html=True)
            user_summary = admin_df.groupby("名前")["金額"].sum().reset_index()
            user_summary.columns = ["名前", "合計"]
            user_summary["合計"] = user_summary["合計"].apply(lambda x: f"{int(x):,} 円")
            st.table(user_summary)
            csv_data = admin_df.drop(columns=['年月']).to_csv(index=False).encode('utf_8_sig')
            st.download_button(label="📥 CSVダウンロード", data=csv_data, file_name=f"集計_{target_month}.csv", mime='text/csv')
    elif pwd != "":
        st.error("パスワードが違います")

else:
    # --- 個人申請モード（統合版） ---
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        name_list = ["山田太郎", "佐藤花子", "鈴木一郎"] 
        selected_user = st.selectbox("あなたの名前を選択してください", name_list)
    with col_s2:
        if not df_all.empty:
            df_all['年月'] = df_all['日付'].apply(lambda x: x.strftime('%Y年%m月'))
            month_list = sorted(df_all['年月'].unique(), reverse=True)
            selected_month = st.selectbox("表示月を選択", month_list)
            filtered_df = df_all[(df_all['年月'] == selected_month) & (df_all['名前'] == selected_user)].copy()
        else:
            selected_month = ""
            filtered_df = pd.DataFrame(columns=COLS)

    total_val = pd.to_numeric(filtered_df["金額"], errors='coerce').fillna(0).sum()
    st.markdown(f'''<div class="header-box"><p class="total-label">{selected_user} さんの合計 ({selected_month})</p><p class="total-a">{int(total_val):,} 円</p></div>''', unsafe_allow_html=True)

    # --- 統合された入力フォーム ---
    st.markdown(f'<div class="form-title">📝 {selected_user} さんの新規入力</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        input_date = st.date_input("日付", date.today())
        
        # 支払先の統合
        p_history = get_history("支払先")
        payee = st.selectbox("支払先", ["新規入力する..."] + p_history)
        if payee == "新規入力する...":
            payee = st.text_input("支払先名を入力", placeholder="例：〇〇商事")
            
    with c2:
        # 品名の統合
        i_history = get_history("品名・名目")
        item_name = st.selectbox("品名・名目", ["新規入力する..."] + i_history)
        if item_name == "新規入力する...":
            item_name = st.text_input("品名を入力", placeholder="例：交通費")
            
        amount_str = st.text_input("金額 (円)", placeholder="数字を入力")

    # 備考の統合
    m_history = get_history("備考")
    memo = st.selectbox("備考", ["新規入力する..."] + m_history)
    if memo == "新規入力する...":
        memo = st.text_area("備考詳細を入力", height=70)

    if st.button("登録する", use_container_width=True):
        clean_amount = "".join(filter(str.isdigit, amount_str))
        amount_val = int(clean_amount) if clean_amount else 0
        if amount_val > 0 and payee != "" and item_name != "" and payee != "新規入力する..." and item_name != "新規入力する...":
            new_row = pd.DataFrame([[selected_user, input_date, payee, item_name, memo, amount_val]], columns=COLS)
            df_for_save = df_all.drop(columns=['年月'], errors='ignore')
            pd.concat([df_for_save, new_row], ignore_index=True).fillna("").to_csv(CSV_FILE, index=False)
            st.success("登録完了！")
            st.rerun()
        else:
            st.warning("各項目を正しく入力してください。")

    st.markdown("---")
    if not filtered_df.empty:
        st.write(f"### 🗓️ {selected_user} さんの明細履歴")
        delete_mode = st.toggle("🗑️ 編集・削除モード")
        if delete_mode:
            for idx, row in filtered_df.iterrows():
                cols = st.columns([5, 1])
                with cols[0]:
                    st.write(f"【{row['日付'].strftime('%m-%d')}】 {row['支払先']} / {int(row['金額']):,}円")
                with cols[1]:
                    if st.button("🗑️", key=f"del_{idx}"):
                        df_all.drop(idx).drop(columns=['年月'], errors='ignore').to_csv(CSV_FILE, index=False)
                        st.rerun()
                st.markdown("<hr style='margin:5px 0; border:0.5px solid #ddd;'>", unsafe_allow_html=True)
        else:
            rows_html = "".join([f"<tr><td>{r['日付'].strftime('%m-%d')}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}円</td></tr>" for _, r in filtered_df.iterrows()])
            st.markdown(f'<table class="table-style"><thead><tr><th class="col-date">日付</th><th class="col-payee">支払先</th><th class="col-item">品名</th><th class="col-memo">備考</th><th class="col-amount">金額</th></tr></thead><tbody>{rows_html}</tbody></table>', unsafe_allow_html=True)

# JS（テンキー対応等）
components.html("""
    <script>
    const doc = window.parent.document;
    setInterval(() => {
        const inputs = doc.querySelectorAll('input');
        inputs.forEach(input => {
            if (input.ariaLabel && input.ariaLabel.includes('金額')) {
                input.type = 'number';
                input.inputMode = 'numeric';
            }
        });
    }, 1000);
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const all = Array.from(doc.querySelectorAll('input, textarea, select, button'));
            const idx = all.indexOf(doc.activeElement);
            if (idx > -1 && idx < all.length - 1) {
                all[idx + 1].focus();
                e.preventDefault();
            }
        }
    });
    </script>
""", height=0)
