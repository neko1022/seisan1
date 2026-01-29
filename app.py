import streamlit as st
import pandas as pd
import os
import base64
from datetime import date
import streamlit.components.v1 as components

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

# --- デザイン & JS設定 ---
css_code = f"""
<style>
    @font-face {{
        font-family: 'Mochiy Pop One';
        src: url(data:font/ttf;base64,{font_base64}) format('truetype');
    }}

    /* 全体にフォントを適用 */
    * {{ font-family: 'Mochiy Pop One', sans-serif !important; }}

    /* 【決定版】ヘッダーにあるアイコン文字（keyboard_double_arrow...）を完全に消す */
    header, [data-testid="stHeader"] {{
        display: none !important;
    }}
    
    /* サイドバー内のアイコンも念のため非表示または標準フォントに */
    [data-testid="collapsedControl"], button[kind="header"] {{
        display: none !important;
    }}

    /* 背景とヘッダーのデザイン */
    .stApp {{ background-color: #DEBCE5 !important; }}
    .header-box {{ border-bottom: 3px solid #71018C; padding: 10px 0; margin-bottom: 20px; }}
    .total-label {{ font-size: 1.1rem; color: #444; margin-bottom: 5px; font-weight: bold; }}
    .total-a {{ font-size: 2.2rem; font-weight: bold; color: #71018C; margin: 0; }}
    .form-title {{ background: #71018C; color: white; padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; }}
    
    /* ボタンデザイン */
    .stButton>button {{ 
        background-color: #71018C !important; 
        color: white !important; 
        border-radius: 25px !important; 
        font-weight: bold !important; 
    }}

    /* テーブルデザイン */
    .table-style {{ width: 100%; border-collapse: collapse; background-color: white; border-radius: 5px; table-layout: fixed; }}
    .table-style th {{ background: #71018C; color: white; padding: 8px 5px; text-align: left; font-size: 0.8rem; }}
    .table-style td {{ border-bottom: 1px solid #eee; padding: 10px 5px; color: #333; font-size: 0.8rem; word-wrap: break-word; }}

    .col-date {{ width: 55px; }}
    .col-payee {{ width: 15%; }}
    .col-item {{ width: 25%; }}
    .col-memo {{ width: auto; }}
    .col-amount {{ width: 85px; }}
    
    /* サイドバーの背景 */
    [data-testid="stSidebar"] {{ background-color: #f8f1f9 !important; }}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- 以下、ロジック部分は変更なし ---
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

st.sidebar.write("### ⚙️ メニュー")
mode = st.sidebar.radio("機能を選択", ["個人精算（申請）", "管理者画面（集計）"])

if mode == "個人精算（申請）":
    st.write("### 🔍 表示設定")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        name_list = ["山田太郎"]
        current_names = sorted(df_all["名前"].unique().tolist())
        for n in current_names:
            if n not in name_list and n != "": name_list.append(n)
        selected_user = st.selectbox("申請者を選択", name_list)
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

    st.markdown('<div class="form-title">📝 新規データ入力</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        user_name = st.selectbox("名前", name_list, key="input_name", index=name_list.index(selected_user) if selected_user in name_list else 0)
    with c2:
        input_date = st.date_input("日付", date.today())
    with c3:
        payee = st.text_input("支払先", placeholder="例：〇〇商事")

    c4, c5 = st.columns([1, 1])
    with c4:
        item_name = st.text_input("品名・名目", placeholder="例：交通費")
    with c5:
        amount_str = st.text_input("金額 (円)", placeholder="数字を入力")
    memo = st.text_area("備考", height=70)

    if st.button("登録する", use_container_width=True):
        clean_amount = "".join(filter(str.isdigit, amount_str))
        amount_val = int(clean_amount) if clean_amount else 0
        if amount_val > 0:
            new_row = pd.DataFrame([[user_name, input_date, payee, item_name, memo, amount_val]], columns=COLS)
            df_save = df_all.drop(columns=['年月'], errors='ignore')
            pd.concat([df_save, new_row], ignore_index=True).fillna("").to_csv(CSV_FILE, index=False)
            st.success("登録完了！")
            st.rerun()

    st.markdown("---")
    if not filtered_df.empty:
        st.write(f"### 🗓️ 明細履歴")
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
        else:
            rows_html = "".join([f"<tr><td>{r['日付'].strftime('%m-%d')}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}円</td></tr>" for _, r in filtered_df.iterrows()])
            st.markdown(f'<table class="table-style"><thead><tr><th class="col-date">日付</th><th class="col-payee">支払先</th><th class="col-item">品名</th><th class="col-memo">備考</th><th class="col-amount">金額</th></tr></thead><tbody>{rows_html}</tbody></table>', unsafe_allow_html=True)

elif mode == "管理者画面（集計）":
    st.write("### 📊 管理者用：全体集計パネル")
    if not df_all.empty:
        df_all['年月'] = df_all['日付'].apply(lambda x: x.strftime('%Y年%m月'))
        target_month = st.selectbox("確認月を選択", sorted(df_all['年月'].unique(), reverse=True))
        admin_df = df_all[df_all['年月'] == target_month].copy()
        total_admin = admin_df["金額"].sum()
        st.markdown(f'<div class="header-box"><p class="total-label">{target_month} 全員分合計</p><p class="total-a">{int(total_admin):,} 円</p></div>', unsafe_allow_html=True)
        st.write("#### 👤 人別集計")
        user_summary = admin_df.groupby("名前")["金額"].sum().reset_index()
        user_summary.columns = ["名前", "合計金額"]
        user_summary["合計金額"] = user_summary["合計金額"].apply(lambda x: f"{int(x):,} 円")
        st.table(user_summary)
        csv = admin_df.drop(columns=['年月']).to_csv(index=False).encode('utf_8_sig')
        st.download_button(label="📥 この月のデータをCSV保存", data=csv, file_name=f"経費集計_{target_month}.csv", mime='text/csv')
        with st.expander("📄 全員の明細を確認する"):
            st.dataframe(admin_df[COLS], use_container_width=True, hide_index=True)
    else:
        st.info("集計するデータがまだありません。")

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
