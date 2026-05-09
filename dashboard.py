import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
# st.markdown("""
# <style>
#     .block-container { padding-top: 1.5rem; }
#     [data-testid="metric-container"] {
#         background: #ddebe981;
#         border: 1px solid #a3a8af;
#         border-radius: 10px;
#         padding: 12px 18px;
#     }
#     [data-testid="stMetricValue"] { font-size: 1.6rem; }
#     .section-title {
#         font-size: 1rem;
#         font-weight: 600;
#         color: #32607b;
#         margin: 1rem 0 0.5rem;
#     }
# </style>
# """, unsafe_allow_html=True)
# st.markdown("""
# <style>
#     .block-container { padding-top: 1.5rem; }
#     [data-testid="metric-container"],
#     [data-testid="stMetric"],
#     div[data-testid^="stMetric"] {
#         background: #ddebe981;
#         border: 1px solid #a3a8af;
#         border-radius: 10px;
#         padding: 12px 18px;
#     }
#     [data-testid="stMetricValue"],
#     [data-testid="stMetricValue"] div { font-size: 1.6rem; }
#     .section-title {
#         font-size: 1rem;
#         font-weight: 600;
#         color: #32607b;
#         margin: 1rem 0 0.5rem;
#     }
# </style>
# """, unsafe_allow_html=True)
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    div[data-testid^="stMetric"] {
        background: #f8f9fb;
        border: 1px solid #f8f9fb;
        border-radius: 10px;
        padding: 12px 18px;
    }
    [data-testid="stMetricValue"] div { font-size: 1.6rem; }
    [data-testid="stMetricLabel"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #32607b;
        margin: 1rem 0 0.5rem;
    }
</style>
""", unsafe_allow_html=True)
color="#eff1f5"
#cahed colors[#1a1a2e #32607b #f8f9fb #e8eaed]
# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["week"]  = df["date"].dt.to_period("W").astype(str)
    return df

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Sales Dashboard")
    st.markdown("---")

    uploaded = st.file_uploader("Upload your own CSV", type=["csv"])
    if uploaded:
        df_raw = load_data(uploaded)
        st.success("Your file loaded!")
    else:
        df_raw = load_data("data/sales_data.csv")
        st.info("Using demo data (800 orders)")

    st.markdown("---")
    st.subheader("Filters")

    # Date range
    min_date = df_raw["date"].min().date()
    max_date = df_raw["date"].max().date()
    date_range = st.date_input(
        "Date range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date,
    )

    # Region
    regions = ["All"] + sorted(df_raw["region"].unique().tolist())
    selected_region = st.selectbox("Region", regions)

    # Category
    categories = ["All"] + sorted(df_raw["category"].unique().tolist())
    selected_category = st.multiselect(
        "Category", df_raw["category"].unique().tolist(),
        default=df_raw["category"].unique().tolist()
    )

    # Status
    statuses = st.multiselect(
        "Order status",
        df_raw["status"].unique().tolist(),
        default=df_raw["status"].unique().tolist()
    )

    st.markdown("---")
    st.caption("Built with Streamlit + Plotly")

# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_raw.copy()

if len(date_range) == 2:
    df = df[(df["date"].dt.date >= date_range[0]) & (df["date"].dt.date <= date_range[1])]

if selected_region != "All":
    df = df[df["region"] == selected_region]

if selected_category:
    df = df[df["category"].isin(selected_category)]

if statuses:
    df = df[df["status"].isin(statuses)]

completed = df[df["status"] == "Completed"]

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Sales Performance Dashboard")
st.caption(f"Showing {len(df):,} orders • {date_range[0] if len(date_range)==2 else min_date} → {date_range[1] if len(date_range)==2 else max_date}")

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

total_rev   = completed["total"].sum()
total_orders = len(completed)
avg_order   = completed["total"].mean() if total_orders > 0 else 0
avg_rating  = df["customer_rating"].mean() if len(df) > 0 else 0
refund_rate = (len(df[df["status"]=="Refunded"]) / len(df) * 100) if len(df) > 0 else 0

k1.metric("Total Revenue",   f"${total_rev:,.0f}")
k2.metric("Completed Orders", f"{total_orders:,}")
k3.metric("Avg Order Value",  f"${avg_order:,.2f}")
k4.metric("Avg Rating",       f"{avg_rating:.1f} / 5")
k5.metric("Refund Rate",      f"{refund_rate:.1f}%")

st.markdown("---")

# ── Row 1: Revenue over time + Revenue by category ─────────────────────────
col1, col2 = st.columns([0.65, 0.35])

with col1:
    st.markdown('<div class="section-title">Revenue over time</div>', unsafe_allow_html=True)
    rev_time = completed.groupby("month")["total"].sum().reset_index()
    rev_time.columns = ["Month", "Revenue"]
    fig1 = px.area(
        rev_time, x="Month", y="Revenue",
        color_discrete_sequence=["#4361ee"],
        template="plotly_white",
    )
    fig1.update_traces(fill="tozeroy", line_width=2)
    fig1.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=280,
        xaxis_title="",
        yaxis_title="Revenue ($)",
        xaxis=dict(tickangle=-35),
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown('<div class="section-title">Revenue by category</div>', unsafe_allow_html=True)
    rev_cat = completed.groupby("category")["total"].sum().reset_index()
    fig2 = px.pie(
        rev_cat, values="total", names="category",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.45,
        template="plotly_white",
    )
    fig2.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=280,
        legend=dict(orientation="h", y=-0.1),
        showlegend=True,
    )
    fig2.update_traces(textinfo="percent", hovertemplate="%{label}: $%{value:,.0f}")
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Top products + Region breakdown ────────────────────────────────
col3, col4 = st.columns([0.5, 0.5])

with col3:
    st.markdown('<div class="section-title">Top 8 products by revenue</div>', unsafe_allow_html=True)
    top_prod = (
        completed.groupby("product")["total"].sum()
        .sort_values(ascending=True).tail(8).reset_index()
    )
    fig3 = px.bar(
        top_prod, x="total", y="product", orientation="h",
        color="total",
        color_continuous_scale="Blues",
        template="plotly_white",
        labels={"total": "Revenue ($)", "product": ""},
    )
    fig3.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=300,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown('<div class="section-title">Orders by region</div>', unsafe_allow_html=True)
    reg_data = df.groupby("region").agg(
        Orders=("order_id", "count"),
        Revenue=("total", "sum"),
    ).reset_index()
    fig4 = px.bar(
        reg_data, x="region", y="Revenue",
        color="Orders",
        color_continuous_scale="Teal",
        template="plotly_white",
        labels={"region": "Region"},
        text="Orders",
    )
    fig4.update_traces(texttemplate="%{text} orders", textposition="outside")
    fig4.update_layout(
        margin=dict(l=0, r=0, t=10, b=40),
        height=300,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: Data table ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">Order details</div>', unsafe_allow_html=True)

c_search, c_sort, c_dl = st.columns([0.5, 0.3, 0.2])
search = c_search.text_input("Search product or order ID", placeholder="e.g. Headphones")
sort_by = c_sort.selectbox("Sort by", ["date", "total", "quantity", "customer_rating"], index=1)

display_df = df.copy()
if search:
    mask = (
        display_df["product"].str.contains(search, case=False, na=False) |
        display_df["order_id"].str.contains(search, case=False, na=False)
    )
    display_df = display_df[mask]

display_df = display_df.sort_values(sort_by, ascending=False)

st.dataframe(
    display_df[["order_id", "date", "product", "category", "region",
                "quantity", "unit_price", "total", "status", "customer_rating"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "order_id":        st.column_config.TextColumn("Order ID"),
        "date":            st.column_config.DateColumn("Date"),
        "total":           st.column_config.NumberColumn("Total ($)", format="$%.2f"),
        "unit_price":      st.column_config.NumberColumn("Unit Price", format="$%.2f"),
        "customer_rating": st.column_config.NumberColumn("Rating", format="%.0f ⭐"),
        "status":          st.column_config.TextColumn("Status"),
    },
    height=350,
)

col_info, col_dl = st.columns([0.8, 0.2])
col_info.caption(f"Showing {len(display_df):,} of {len(df):,} orders")
col_dl.download_button(
    "⬇ Export CSV",
    display_df.to_csv(index=False),
    "filtered_sales.csv",
    "text/csv",
    use_container_width=True,
)
