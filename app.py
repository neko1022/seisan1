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
    
    /* ボタン類 */
    .stButton>button {{ 
        background-color: #71018C !important; 
        color: white !important; 
        border-radius: 25px !important; 
        font-weight: bold !important; 
    }}

    /* テーブルデザイン */
    .table-style {{ width: 100%; border-collapse: collapse; background-color: white; border-radius: 5px; overflow: hidden; }}
    .table-style th {{ background: #71018C; color: white; padding: 12px; text-align: left; font-size: 0.9rem; }}
    .table-style td {{ border-bottom: 1px solid #eee; padding: 12px; color: #333; font-size: 0.85rem; }}

    label[data-testid="stWidgetLabel"] p {{ color: #333 !important; font-weight: bold !important; }}
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

# --- データ処理 ---
CSV_FILE = "expenses.csv"
COLS = ["日付", "支払先", "品名・名目", "備考", "金額"]

def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df["日付"] = pd.to_datetime(df["日付"]).dt.date
        return df
    return pd.DataFrame(columns=COLS)

# --- メイン画面 ---
df_all = load_data()

# 1. 合計表示
if not df_all.empty:
    df_all['年月'] = df_all['日付'].apply(lambda x: x.strftime('%Y年%m月'))
    selected_month = st.selectbox("表示月を選択", sorted(df_all['年月'].unique(), reverse=True))
    filtered_df = df_all[df_all['年月'] == selected_month].copy()
else:
    selected_month = ""
    filtered_df = pd.DataFrame(columns=COLS)

total = int(pd.to_numeric(filtered_df["金額"], errors='coerce').fillna(0).sum())
st.markdown(f'<div class="header-box"><p class="total-a">{total:,} 円</p></div>', unsafe_allow_html=True)

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
    if payee and amount_val > 0:
        new_row = pd.DataFrame([[input_date, payee, item_name, memo, amount_val]], columns=COLS)
        updated_df = pd.concat([df_all.drop(columns=['年月'], errors='ignore'), new_row], ignore_index=True)
        updated_df.to_csv(CSV_FILE, index=False)
        st.success("登録しました！")
        st.rerun()

# 3. 履歴明細（美しさを維持した削除機能）
if not filtered_df.empty:
    st.write(f"### 🗓️ {selected_month} の明細")
    
    # 削除モードの切り替えスイッチ
    delete_mode = st.toggle("🗑️ 編集・削除モードにする")

    if delete_mode:
        st.warning("削除したい項目のゴミ箱ボタンを押してください。")
        for idx, row in filtered_df.iterrows():
            cols = st.columns([0.5, 5, 1])
            with cols[1]:
                st.write(f"【{row['日付']}】 {row['支払先']} / {row['品名・名目']} / {int(row['金額']):,}円")
            with cols[2]:
                if st.button("🗑️", key=f"del_{idx}"):
                    new_df = df_all.drop(idx).drop(columns=['年月'], errors='ignore')
                    new_df.to_csv(CSV_FILE, index=False)
                    st.success("削除しました。")
                    st.rerun()
            st.markdown("<hr style='margin:5px 0; border:0.5px solid #ddd;'>", unsafe_allow_html=True)
    else:
        # 通常時の美しいテーブル表示
        rows = "".join([f"<tr><td>{r['日付']}</td><td>{r['支払先']}</td><td>{r['品名・名目']}</td><td>{r['備考']}</td><td>{int(r['金額']):,}</td></tr>" for _, r in filtered_df.iterrows()])
        st.markdown(f'<table class="table-style"><thead><tr>{"".join([f"<th>{c}</th>" for c in COLS])}</tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)

else:
    st.info("データがありません。")
