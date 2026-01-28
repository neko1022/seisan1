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
    * {{ font-family: 'Mochiy Pop One', sans-serif !important; }}
    .stApp {{ background-color: #DEBCE5 !important; }}
    .header-box {{ border-bottom: 3px solid #71018C; padding: 10px 0; margin-bottom: 20px; }}
    .total-a {{ font-size: 2.2rem; font-weight: bold; color: #71018C; margin: 0; }}
    .form-title {{ background: #71018C; color: white; padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; }}
    .stButton>button {{ background-color: #71018C !important; color: white !important; border-radius: 25px !important; font-weight: bold !important; }}
    
    /* テーブル全体のデザイン */
    .table-style {{ width: 100%; border-collapse: collapse; background-color: white; border-radius: 5px; table-layout: fixed; }}
    .table-style th {{ background: #71018C; color: white; padding: 12px; text-align: left; font-size: 0.9rem; }}
    .table-style td {{ border-bottom: 1px solid #eee; padding: 12px; color: #333; font-size: 0.85rem; word-wrap: break-word; }}

    /* 項目の幅を個別に指定 */
    .col-date {{ width: 130px; }}    /* 日付を狭く */
    .col-payee {{ width: 20%; }}
    .col-item {{ width: 20%; }}
    .col-memo {{ width: auto; }}
    .col-amount {{ width: 110px; }}   /* 金額も少し固定幅に */

</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# JavaScript: Enter移動 + テンキー
components.html(
    """
    <script>
    const doc = window.parent.document;
    setInterval(() => {
        const inputs = doc.querySelectorAll('input');
        inputs.forEach(input => {
            if (input.ariaLabel && input.ariaLabel.includes('金額')) {
                input.type = 'number';
                input.inputMode = 'numeric';
                input.pattern = '[0-9]*';
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
    """,
    height=0,
)

# --- データ処理関数 ---
CSV_FILE = "expenses.csv"
COLS = ["日付", "支払先", "品名・名目", "備考", "金額"]

def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            df["日付"] = pd.to_datetime(df["日付"]).dt.date
            return df.fillna("")
        except:
            return pd.DataFrame(columns=COLS)
    return pd.DataFrame(columns=COLS)

# --- メイン画面 ---
df_all = load_data()

if not df_all.empty:
    df_all['年月'] = df_all['日付'].apply(lambda x: x.strftime('%Y年%m月'))
    month_list = sorted(df_all['年月'].unique(), reverse=True)
    selected_month = st.selectbox("表示月を選択", month_list)
    filtered_df = df_all[df_all['年月'] == selected_month].copy()
else:
    selected_month = ""
    filtered_df = pd.DataFrame(columns=COLS)

total_val = pd.to_numeric(filtered_df["金額"], errors='coerce').fillna(0).sum()
st.markdown(f'<div class="header-box"><p class="total-a">{int(total_val):,} 円</p></div>', unsafe_allow_html=True)

# 2. 入力フォーム
st.markdown('<div class="form-title">📝 新規データ入力</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    input_date = st.date_input("日付", date.today())
    payee = st.text_input("支払先", placeholder="例：〇〇商事")
with c2:
    item_name = st.text_input("品名・名目", placeholder="例：交通費")
    amount_str = st.text_input("金額 (円)", placeholder="数字を入力")
memo = st.text_area("備考", height=70)

if st.button("登録する", use_container_width=True):
    clean_amount = "".join(filter(str.isdigit, amount_str))
    amount_val = int(clean_amount) if clean_amount else 0
    if amount_val > 0:
        new_row = pd.DataFrame([[input_date, payee, item_name, memo, amount_val]], columns=COLS)
        df_for_save = df_all.drop(columns=['年月'], errors='ignore')
        updated_df = pd.concat([df_for_save, new_row], ignore_index=True)
        updated_df.fillna("").to_csv(CSV_FILE, index=False)
        st.success("登録完了しました！")
        st.rerun()
    else:
        st.warning("金額を入力してください。")

# 3. 履歴明細
st.markdown("---")
if not filtered_df.empty:
    st.write(f"### {selected_month} の明細")
    delete_mode = st.toggle("🗑️ 編集・削除モード")

    if delete_mode:
        for idx, row in filtered_df.iterrows():
            cols = st.columns([5, 1])
            with cols[0]:
                p = row['支払先'] if row['支払先'] != "" else "(未入力)"
                i = row['品名・名目'] if row['品名・名目'] != "" else "(未入力)"
                st.write(f"【{row['日付']}】 {p} / {i} / {int(row['金額']):,}円")
            with cols[1]:
                if st.button("🗑️", key=f"del_{idx}"):
                    df_to_save = df_all.drop(idx).drop(columns=['年月'], errors='ignore')
                    df_to_save.fillna("").to_csv(CSV_FILE, index=False)
                    st.rerun()
            st.markdown("<hr style='margin:5px 0; border:0.5px solid #ddd;'>", unsafe_allow_html=True)
    else:
        # 通常表示
        rows_html = ""
        for _, r in filtered_df.iterrows():
            f_payee = r['支払先'] if pd.notna(r['支払先']) else ""
            f_item = r['品名・名目'] if pd.notna(r['品名・名目']) else ""
            f_memo = r['備考'] if pd.notna(r['備考']) else ""
            rows_html += f"<tr><td>{r['日付']}</td><td>{f_payee}</td><td>{f_item}</td><td>{f_memo}</td><td>{int(r['金額']):,} 円</td></tr>"
        
        # クラス名を各 th に付与して幅を制御
        st.markdown(f'''
            <table class="table-style">
                <thead>
                    <tr>
                        <th class="col-date">日付</th>
                        <th class="col-payee">支払先</th>
                        <th class="col-item">品名・名目</th>
                        <th class="col-memo">備考</th>
                        <th class="col-amount">金額</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        ''', unsafe_allow_html=True)
else:
    st.info("データがありません。")
