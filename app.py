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
    header, [data-testid="stHeader"], [data-testid="collapsedControl"] {{ display: none !important; }}
    .stApp {{ background-color: #DEBCE5 !important; }}
    .header-box {{ border-bottom: 3px solid #71018C; padding: 10px 0; margin-bottom: 20px; }}
    .total-label {{ font-size: 1.1rem; color: #444; margin-bottom: 5px; font-weight: bold; }}
    .total-a {{ font-size: 2.2rem; font-weight: bold; color: #71018C; margin: 0; }}
    .form-title {{ background: #71018C; color: white; padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; }}
    .stButton>button {{ background-color: #71018C !important; color: white !important; border-radius: 25px !important; font-weight: bold !important; }}
    .table-style {{ width: 100%; border-collapse: collapse; background-color: white; border-radius: 5px; table-layout: fixed; }}
    .table-style th {{ background: #71018C; color: white; padding: 8px 5px; text-align: left; font-size: 0.8rem; }}
    .table-style td {{ border-bottom: 1px solid #eee; padding: 10px 5px; color: #333; font-size: 0.8rem; word-wrap: break-word; }}
    .custom-suggestion-list {{
        position: absolute; z-index: 1000; background: white; border: 1px solid #ddd;
        border-radius: 5px; max-height: 150px; overflow-y: auto; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        width: 100%; display: none;
    }}
    .suggestion-item {{ padding: 8px 12px; cursor: pointer; font-size: 0.9rem; border-bottom: 1px solid #f0f0f0; }}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- データ処理（不変の部分） ---
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

def get_h(col):
    return sorted([str(x) for x in df_all[col].unique() if str(x).strip() != ""])

payee_h, item_h, memo_h = get_h("支払先"), get_h("品名・名目"), get_h("備考")
USER_PASS, ADMIN_PASS = "0000", "1234"

# --- 画面構成 ---
is_admin = st.toggle("🛠️ 管理者モードに切り替え (上司専用)")

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
                c_switch, c_name, c_amt = st.columns([1, 2, 2])
                with c_switch: show_detail = st.toggle("明細", key=f"adm_det_{idx}")
                with c_name: st.write(f"**{row['名前']}**")
                with c_amt: st.write(f"{int(row['金額']):,} 円")
                if show_detail:
                    u_detail = admin_df[admin_df["名前"] == row["名前"]].copy()
                    rows_html = "".join([f"<tr><td>{r['日付'].strftime('%m-%d')}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}円</td></tr>" for _, r in u_detail.iterrows()])
                    st.markdown(f'<table class="table-style"><thead><tr><th>日付</th><th>支払先</th><th>品名</th><th>備考</th><th>金額</th></tr></thead><tbody>{rows_html}</tbody></table>', unsafe_allow_html=True)
            st.download_button("CSV保存", admin_df.to_csv(index=False).encode('utf_8_sig'), f"sum_{target_month}.csv")
else:
    # 個人モード
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
            
            filtered_df = df_all[(df_all['年月'] == selected_month) & (df_all['名前'] == selected_user)].copy() if selected_month else pd.DataFrame(columns=COLS)
            st.markdown(f'<div class="header-box"><p class="total-label">{selected_user} 合計</p><p class="total-a">{int(filtered_df["金額"].sum()):,} 円</p></div>', unsafe_allow_html=True)

            # 新規入力
            st.markdown('<div class="form-title">📝 新規入力</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                input_date = st.date_input("日付", date.today())
                payee = st.text_input("支払先", key="payee_in")
            with c2:
                item_name = st.text_input("品名・名目", key="item_in")
                amount_str = st.text_input("金額 (円)")
            memo = st.text_area("備考", height=70, key="memo_in")

            if st.button("登録する", use_container_width=True):
                clean_amount = "".join(filter(str.isdigit, amount_str))
                amount_val = int(clean_amount) if clean_amount else 0
                if amount_val > 0 and payee and item_name:
                    new_row = pd.DataFrame([[selected_user, input_date, payee, item_name, memo, amount_val]], columns=COLS)
                    pd.concat([df_all.drop(columns=['年月'], errors='ignore'), new_row], ignore_index=True).to_csv(CSV_FILE, index=False)
                    st.success("登録完了！")
                    st.rerun()

            # 明細
            st.markdown("---")
            if not filtered_df.empty:
                st.write("### 🗓️ 明細履歴")
                delete_mode = st.toggle("🗑️ 編集・削除モード")
                if delete_mode:
                    for idx, row in filtered_df.iterrows():
                        cols = st.columns([5, 1])
                        with cols[0]:
                            # エラーの原因だった箇所をシンプルに修正
                            disp = f"【{row['日付'].strftime('%m-%d')}】 {row['支払先']} / {int(row['金額']):,}円"
                            st.write(disp)
                        with cols[1]:
                            if st.button("🗑️", key=f"del_{idx}"):
                                df_all.drop(idx).drop(columns=['年月'], errors='ignore').to_csv(CSV_FILE, index=False)
                                st.rerun()
                else:
                    rows_html = "".join([f"<tr><td>{r['日付'].strftime('%m-%d')}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}円</td></tr>" for _, r in filtered_df.iterrows()])
                    st.markdown(f'<table class="table-style"><thead><tr><th>日付</th><th>支払先</th><th>品名</th><th>備考</th><th>金額</th></tr></thead><tbody>{rows_html}</tbody></table>', unsafe_allow_html=True)
        elif user_pwd != "": st.error("パスワード不一致")

# サジェスト用JS
history_js = f"""
<script>
const doc = window.parent.document;
const hData = {{ "支払先": {payee_h}, "品名・名目": {item_h}, "備考": {memo_h} }};
function cList(input, list) {{
    const old = input.parentElement.querySelector('.custom-suggestion-list');
    if (old) old.remove();
    const div = doc.createElement('div');
    div.className = 'custom-suggestion-list';
    list.forEach(i => {{
        const item = doc.createElement('div');
        item.className = 'suggestion-item';
        item.innerText = i;
        item.onmousedown = () => {{ input.value = i; input.dispatchEvent(new Event('input', {{ bubbles: true }})); }};
        div.appendChild(item);
    }});
    input.parentElement.style.position = 'relative';
    input.parentElement.appendChild(div);
    return div;
}}
setInterval(() => {{
    doc.querySelectorAll('input, textarea').forEach(el => {{
        const label = el.ariaLabel;
        if (hData[label] && !el.dataset.hasList) {{
            const div = cList(el, hData[label]);
            el.onfocus = () => div.style.display = 'block';
            el.onblur = () => setTimeout(() => div.style.display = 'none', 200);
            el.dataset.hasList = "true";
        }}
    }});
}}, 1000);
</script>
"""
components.html(history_js, height=0)
