import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page config
st.set_page_config(page_title="Portfolio Dashboard", page_icon="📊", layout="wide")

st.title("📊 My Portfolio Dashboard")
st.markdown(f"**Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('/Users/geon/.openclaw/workspace/portfolio_full.csv')
    return df

df = load_data()

# Clean and convert data
def parse_value(val):
    if pd.isna(val):
        return 0
    val = str(val).replace('₩', '').replace('$', '').replace(',', '').replace('+', '').strip()
    try:
        return float(val)
    except:
        return 0

# Convert KRW values
df['가치_원화'] = df['자산가치'].apply(lambda x: parse_value(x) if '₩' in str(x) else 0)
df['가치_USD'] = df['자산가치'].apply(lambda x: parse_value(x) if '$' in str(x) else 0)

# Total portfolio value (convert USD to KRW ~1450)
usd_to_krw = 1450
total_krw = df['가치_원화'].sum() + (df['가치_USD'].sum() * usd_to_krw)

# Display total value
col1, col2, col3 = st.columns(3)
col1.metric("Total Portfolio Value", f"₩{total_krw:,.0f}", f"${total_krw/usd_to_krw:,.0f}")
col2.metric("Total Assets", f"{len(df)}")
col3.metric("Asset Classes", f"{df['분류'].nunique()}")

st.divider()

# Asset Allocation by Category
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Asset Allocation by Category")
    category_value = df.groupby('분류')['가치_원화'].sum().reset_index()
    fig_pie = px.pie(category_value, values='가치_원화', names='분류', 
                     color_discrete_sequence=px.colors.qualitative.Set3)
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

# Top Holdings
with col2:
    st.subheader("🏆 Top Holdings")
    top_holdings = df.nlargest(10, '가치_원화')[['자산', '분류', '가치_원화']].copy()
    top_holdings['가치_원화'] = top_holdings['가치_원화'].apply(lambda x: f"₩{x:,.0f}")
    st.dataframe(top_holdings, hide_index=True, use_container_width=True)

st.divider()

# All Holdings Table
st.subheader("📋 All Holdings")
display_df = df[['자산', '분류', '수량', '자산가치', '손익']].copy()
st.dataframe(display_df, use_container_width=True)

# Performance by Category
st.divider()
st.subheader("📊 Performance by Asset Class")
category_perf = df.groupby('분류')['가치_원화'].sum().reset_index()
fig_bar = px.bar(category_perf, x='분류', y='가치_원화', color='분류',
                  color_discrete_sequence=px.colors.qualitative.Bold)
fig_bar.update_layout(yaxis_title="Value (KRW)")
st.plotly_chart(fig_bar, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Portfolio Dashboard | Data source: portfolio_full.csv")
