import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from anthropic import Anthropic
import io
import json

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Data Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600;700&display=swap');

    :root {
        --bg: #0f0f13;
        --surface: #1a1a24;
        --accent: #6ee7b7;
        --accent2: #818cf8;
        --text: #e2e8f0;
        --muted: #64748b;
        --danger: #f87171;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        color: var(--text);
    }

    .stApp {
        background: #0f0f13;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1a24 0%, #1e1e2e 100%);
        border: 1px solid rgba(110, 231, 183, 0.15);
        border-radius: 16px;
        padding: 20px 24px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }

    .metric-card:hover {
        border-color: rgba(110, 231, 183, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(110, 231, 183, 0.1);
    }

    .metric-value {
        font-family: 'Space Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #6ee7b7;
        line-height: 1.2;
    }

    .metric-label {
        font-size: 0.8rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 4px;
    }

    .metric-delta {
        font-size: 0.85rem;
        color: #6ee7b7;
        margin-top: 4px;
    }

    /* AI Chat bubble */
    .chat-user {
        background: linear-gradient(135deg, #818cf8 0%, #6366f1 100%);
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        margin: 8px 0;
        margin-left: 20%;
        color: white;
        font-size: 0.95rem;
    }

    .chat-ai {
        background: linear-gradient(135deg, #1e1e2e 0%, #1a1a24 100%);
        border: 1px solid rgba(110, 231, 183, 0.2);
        border-radius: 18px 18px 18px 4px;
        padding: 14px 18px;
        margin: 8px 0;
        margin-right: 20%;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* Section headers */
    .section-title {
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
        color: #6ee7b7;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(110, 231, 183, 0.2);
    }

    /* Upload area */
    .upload-hint {
        text-align: center;
        padding: 40px;
        border: 2px dashed rgba(110, 231, 183, 0.3);
        border-radius: 16px;
        color: #64748b;
    }

    /* Sidebar */
    .css-1d391kg {
        background: #12121a !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6ee7b7 0%, #34d399 100%) !important;
        color: #0f0f13 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(110, 231, 183, 0.3) !important;
    }

    /* Input */
    .stTextInput > div > div > input {
        background: #1a1a24 !important;
        border: 1px solid rgba(110, 231, 183, 0.2) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #6ee7b7 !important;
        box-shadow: 0 0 0 2px rgba(110, 231, 183, 0.2) !important;
    }

    /* Dataframe */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Anthropic client ──────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    return Anthropic()

client = get_client()

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "df_summary" not in st.session_state:
    st.session_state.df_summary = ""

# ── Helper functions ──────────────────────────────────────────────────────────
def load_data(uploaded_file):
    """Load CSV or Excel file."""
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Faylni o'qishda xato: {e}")
        return None


def create_summary(df: pd.DataFrame) -> str:
    """Create a concise data summary for the AI context."""
    buf = io.StringIO()
    buf.write(f"Dataset: {df.shape[0]} rows × {df.shape[1]} columns\n")
    buf.write(f"Columns: {list(df.columns)}\n\n")

    # Numeric stats
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if num_cols:
        buf.write("Numeric columns summary:\n")
        buf.write(df[num_cols].describe().to_string())
        buf.write("\n\n")

    # First 5 rows
    buf.write("Sample rows (first 5):\n")
    buf.write(df.head(5).to_string())
    buf.write("\n\n")

    # Categorical columns value counts (top 10)
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    for col in cat_cols[:4]:
        buf.write(f"Top values in '{col}':\n")
        buf.write(df[col].value_counts().head(10).to_string())
        buf.write("\n\n")

    return buf.getvalue()


def ask_ai(question: str, df_summary: str) -> str:
    """Ask Claude a question about the sales data."""
    system = f"""You are a professional sales data analyst assistant.
You have access to the following dataset summary:

{df_summary}

Answer the user's question based on this data. Be concise, insightful, and use numbers.
Format nicely with emojis where appropriate. Respond in the same language the user asks (Uzbek or English).
"""
    st.session_state.messages.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system,
        messages=st.session_state.messages,
    )
    answer = response.content[0].text
    st.session_state.messages.append({"role": "assistant", "content": answer})
    return answer


def fmt_number(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,.0f}"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-title">📂 Ma\'lumot yuklash</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "CSV yoki Excel fayl tanlang",
        type=["csv", "xlsx", "xls"],
        help="Satish ma'lumotlari bo'lgan CSV yoki Excel fayl yuklang",
    )

    if uploaded:
        df = load_data(uploaded)
        if df is not None:
            st.session_state.df = df
            st.session_state.df_summary = create_summary(df)
            st.session_state.messages = []  # reset chat on new file
            st.success(f"✅ {df.shape[0]:,} qator, {df.shape[1]} ustun yuklandi")

    st.markdown("---")
    st.markdown('<div class="section-title">💡 Namuna savollar</div>', unsafe_allow_html=True)

    sample_questions = [
        "Eng ko'p sotilgan 5 ta mahsulot?",
        "Oylar bo'yicha umumiy daromad?",
        "Qaysi region eng yaxshi ishlagan?",
        "O'rtacha buyurtma qiymati qancha?",
        "Qaysi kategoriya eng ko'p daromad keltirdi?",
    ]

    for q in sample_questions:
        if st.button(q, key=f"sq_{q}"):
            st.session_state["prefill"] = q

    st.markdown("---")

    if st.button("🗑️ Chatni tozalash"):
        st.session_state.messages = []
        st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────
# Header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <h1 style='font-family: Space Mono, monospace; font-size: 2rem; color: #6ee7b7; margin-bottom: 4px;'>
        📊 Sales Data Analyzer
    </h1>
    <p style='color: #64748b; font-size: 0.95rem; margin-top: 0;'>
        CSV / Excel faylni yuklang · Ma'lumotlarni ko'ring · AI bilan tahlil qiling
    </p>
    """, unsafe_allow_html=True)

# ── No data state ─────────────────────────────────────────────────────────────
if st.session_state.df is None:
    st.markdown("""
    <div class="upload-hint">
        <div style='font-size: 3rem; margin-bottom: 12px;'>📁</div>
        <div style='font-size: 1.1rem; font-weight: 600; color: #94a3b8;'>Chap paneldan fayl yuklang</div>
        <div style='font-size: 0.85rem; margin-top: 8px; color: #475569;'>CSV yoki Excel (.xlsx) formatdagi satish ma'lumotlari qo'llab-quvvatlanadi</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df = st.session_state.df

# ── Metric cards ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📈 Asosiy ko\'rsatkichlar</div>', unsafe_allow_html=True)

num_cols = df.select_dtypes(include="number").columns.tolist()

# Try to auto-detect revenue / quantity / profit columns
revenue_col = next((c for c in df.columns if any(k in c.lower() for k in ["revenue", "sales", "amount", "daromad", "summa", "total"])), None)
qty_col = next((c for c in df.columns if any(k in c.lower() for k in ["qty", "quantity", "count", "miqdor", "soni"])), None)
profit_col = next((c for c in df.columns if any(k in c.lower() for k in ["profit", "margin", "foyda"])), None)

metrics = []
if revenue_col:
    metrics.append(("💰 Umumiy daromad", fmt_number(df[revenue_col].sum()), revenue_col))
if qty_col:
    metrics.append(("📦 Jami sotish", fmt_number(df[qty_col].sum()), qty_col))
if profit_col:
    metrics.append(("📈 Umumiy foyda", fmt_number(df[profit_col].sum()), profit_col))
if revenue_col:
    metrics.append(("🧾 O'rtacha buyurtma", fmt_number(df[revenue_col].mean()), "avg"))

metrics.append(("🗂️ Jami qatorlar", f"{df.shape[0]:,}", "rows"))
metrics.append(("📋 Ustunlar soni", str(df.shape[1]), "cols"))

cols_m = st.columns(min(len(metrics), 6))
for i, (label, value, _) in enumerate(metrics[:6]):
    with cols_m[i]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Ma'lumotlar jadvali", "📊 Vizualizatsiya", "🤖 AI Tahlil"])

# ─── Tab 1: Data table ────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-title">Ma\'lumotlar jadvali</div>', unsafe_allow_html=True)

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search = st.text_input("🔍 Qidirish", placeholder="Kalit so'z kiriting...")
    with col_f2:
        n_rows = st.selectbox("Ko'rsatish", [10, 25, 50, 100, "Hammasi"], index=1)

    filtered = df.copy()
    if search:
        mask = filtered.apply(lambda col: col.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
        filtered = filtered[mask]

    if n_rows != "Hammasi":
        display_df = filtered.head(int(n_rows))
    else:
        display_df = filtered

    st.dataframe(
        display_df,
        use_container_width=True,
        height=420,
    )
    st.caption(f"Jami: {len(filtered):,} qator ko'rsatilmoqda (umumiy: {len(df):,})")

# ─── Tab 2: Charts ────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">Vizualizatsiya</div>', unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns(2)

    # Bar chart: categorical vs numeric
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    with chart_col1:
        if cat_cols and num_cols:
            x_col = st.selectbox("X o'qi (kategoriya)", cat_cols, key="x_col")
            y_col = st.selectbox("Y o'qi (raqam)", num_cols, key="y_col")
            top_n = st.slider("Top N", 5, 30, 10)

            agg = df.groupby(x_col)[y_col].sum().nlargest(top_n).reset_index()
            fig = px.bar(
                agg, x=y_col, y=x_col, orientation="h",
                color=y_col,
                color_continuous_scale=["#1e1e2e", "#6ee7b7"],
                title=f"Top {top_n}: {x_col} bo'yicha {y_col}",
            )
            fig.update_layout(
                plot_bgcolor="#1a1a24",
                paper_bgcolor="#0f0f13",
                font=dict(color="#e2e8f0", family="DM Sans"),
                title_font=dict(color="#6ee7b7", size=14),
                coloraxis_showscale=False,
                yaxis=dict(gridcolor="#1e1e2e"),
                xaxis=dict(gridcolor="#1e1e2e"),
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        if cat_cols and revenue_col:
            pie_col = st.selectbox("Kategoriya (doira diagramma)", cat_cols, key="pie_col")
            pie_data = df.groupby(pie_col)[revenue_col].sum().nlargest(8).reset_index()
            fig2 = px.pie(
                pie_data, values=revenue_col, names=pie_col,
                title=f"{pie_col} bo'yicha daromad taqsimoti",
                color_discrete_sequence=px.colors.sequential.Teal,
                hole=0.4,
            )
            fig2.update_layout(
                plot_bgcolor="#1a1a24",
                paper_bgcolor="#0f0f13",
                font=dict(color="#e2e8f0", family="DM Sans"),
                title_font=dict(color="#6ee7b7", size=14),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Line chart for time series
    date_cols = df.select_dtypes(include=["datetime64", "datetime"]).columns.tolist()
    # Also try to parse object columns
    if not date_cols:
        for c in cat_cols:
            try:
                sample = pd.to_datetime(df[c].dropna().head(20), infer_datetime_format=True)
                if not sample.isna().all():
                    date_cols.append(c)
                    break
            except Exception:
                pass

    if date_cols and num_cols:
        st.markdown("---")
        d_col = st.selectbox("Sana ustuni", date_cols, key="d_col")
        v_col = st.selectbox("Qiymat ustuni", num_cols, key="v_col")

        try:
            tmp = df.copy()
            tmp[d_col] = pd.to_datetime(tmp[d_col], infer_datetime_format=True)
            ts = tmp.groupby(tmp[d_col].dt.to_period("M").dt.to_timestamp())[v_col].sum().reset_index()
            fig3 = px.line(ts, x=d_col, y=v_col, title=f"Oylik {v_col} trendi",
                           line_shape="spline")
            fig3.update_traces(line_color="#6ee7b7", line_width=2.5)
            fig3.update_layout(
                plot_bgcolor="#1a1a24",
                paper_bgcolor="#0f0f13",
                font=dict(color="#e2e8f0", family="DM Sans"),
                title_font=dict(color="#6ee7b7", size=14),
                xaxis=dict(gridcolor="#1e1e2e"),
                yaxis=dict(gridcolor="#1e1e2e"),
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig3, use_container_width=True)
        except Exception:
            pass

# ─── Tab 3: AI Chat ───────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">🤖 AI bilan suhbat</div>', unsafe_allow_html=True)

    # Chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    # Input
    prefill = st.session_state.pop("prefill", "")
    question = st.text_input(
        "Savol bering",
        value=prefill,
        placeholder="Masalan: Eng ko'p sotilgan mahsulot qaysi?",
        key="chat_input",
    )

    col_send, col_clear = st.columns([1, 4])
    with col_send:
        send = st.button("📨 Yuborish", use_container_width=True)

    if send and question.strip():
        with st.spinner("AI tahlil qilmoqda..."):
            answer = ask_ai(question.strip(), st.session_state.df_summary)
        st.rerun()

    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align:center; padding: 24px; color: #475569; font-size: 0.9rem;'>
            ↖ Chap paneldagi namuna savollardan birini bosing yoki o'z savolingizni yozing
        </div>
        """, unsafe_allow_html=True)
