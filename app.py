#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Beer Consumption Analytics Dashboard",
    layout="wide"
)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("Beer_Consumed_Guest_For_Dashboard.xlsx")

    df['Date'] = pd.to_datetime(df['Date'])
    df['Customer Mobile No'] = df['Customer Mobile No'].astype(str)
    df['Day'] = df['Date'].dt.day_name()
    df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.hour

    return df

df = load_data()

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
st.sidebar.title("🔎 Filters")

centre = st.sidebar.multiselect(
    "Select Business Unit",
    options=df['POSDescription'].unique(),
    default=df['POSDescription'].unique()
)

month = st.sidebar.multiselect(
    "Select Reporting Period",
    options=df['Bill Month'].unique(),
    default=df['Bill Month'].unique()
)

filtered_df = df[
    (df['POSDescription'].isin(centre)) &
    (df['Bill Month'].isin(month))
]

# -------------------------------------------------
# TITLE
# -------------------------------------------------
st.title("🍺 Beer Consumption Analytics Dashboard")
st.caption("Customer Segmentation • Revenue Insights • Retention • Brand Performance")

# -------------------------------------------------
# KPI METRICS
# -------------------------------------------------
total_revenue = filtered_df['Gross Amount'].sum()
unique_guests = filtered_df['Customer Mobile No'].nunique()

repeat_counts = filtered_df['Customer Mobile No'].value_counts()
repeat_pct = (repeat_counts[repeat_counts > 1].count() / unique_guests) * 100

col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"₹{total_revenue:,.0f}")
col2.metric("Unique Guests", unique_guests)
col3.metric("Repeat Guest %", f"{repeat_pct:.1f}%")

st.divider()

# -------------------------------------------------
# CUSTOMER SEGMENTATION
# -------------------------------------------------
st.subheader("👥 Guest Segmentation")

guest_metrics = filtered_df.groupby('Customer Mobile No').agg(
    visits=('Bill No', 'nunique'),
    spend=('Gross Amount', 'sum')
).reset_index()

def segment(row):
    if row['spend'] > 10000 or row['visits'] >= 6:
        return 'VIP'
    elif row['visits'] >= 3:
        return 'Regular'
    else:
        return 'Occasional'

guest_metrics['Segment'] = guest_metrics.apply(segment, axis=1)

seg_counts = guest_metrics['Segment'].value_counts()
st.bar_chart(seg_counts)

st.write("### Revenue Contribution by Segment")
seg_rev = guest_metrics.merge(
    filtered_df[['Customer Mobile No','Gross Amount']],
    on='Customer Mobile No'
).groupby('Segment')['Gross Amount'].sum()

st.bar_chart(seg_rev)

st.divider()

# -------------------------------------------------
# CENTRE-WISE BEER PREFERENCE
# -------------------------------------------------
st.subheader("🏢 Centre-wise Beer Preference")

heatmap_data = pd.pivot_table(
    filtered_df,
    index='POSDescription',
    columns='MenuGroupDescription',
    values='Customer Mobile No',
    aggfunc=pd.Series.nunique,
    fill_value=0
)

st.dataframe(heatmap_data, use_container_width=True)

st.divider()

# -------------------------------------------------
# VISIT FREQUENCY
# -------------------------------------------------
st.subheader("📊 Visit Frequency Distribution")

visit_freq = filtered_df.groupby('Customer Mobile No')['Bill No'].nunique()
visit_dist = visit_freq.value_counts().sort_index()

st.bar_chart(visit_dist)

st.divider()

# -------------------------------------------------
# PEAK DAY & TIME
# -------------------------------------------------
st.subheader("⏰ Peak Consumption Insights")

col1, col2 = st.columns(2)

with col1:
    st.write("Revenue by Day")
    day_sales = filtered_df.groupby('Day')['NetAmount'].sum()
    st.bar_chart(day_sales)

with col2:
    st.write("Revenue by Hour")
    hour_sales = filtered_df.groupby('Hour')['NetAmount'].sum()
    st.bar_chart(hour_sales)

st.divider()

# -------------------------------------------------
# CUSTOMER LIFETIME VALUE
# -------------------------------------------------
st.subheader("💰 Customer Lifetime Value")

clv = filtered_df.groupby('Customer Mobile No').agg(
    visits=('Bill No', 'nunique'),
    total_spend=('NetAmount', 'sum')
)

st.metric("Average CLV", f"₹{clv['total_spend'].mean():,.0f}")

st.write("Top 10 Customers by CLV")
st.dataframe(
    clv.sort_values(by='total_spend', ascending=False).head(10),
    use_container_width=True
)

st.divider()

# -------------------------------------------------
# RETENTION INSIGHTS
# -------------------------------------------------
st.subheader("🔁 Retention Insights")

last_visit = filtered_df.groupby('Customer Mobile No')['Date'].max().reset_index()

inactive = last_visit[
    last_visit['Date'] < filtered_df['Date'].max() - pd.Timedelta(days=30)
]

recent = last_visit[
    last_visit['Date'] >= filtered_df['Date'].max() - pd.Timedelta(days=7)
]

st.write("Inactive Guests (30+ days)")
st.dataframe(inactive, use_container_width=True)

st.write("Guests Likely to Return Soon")
st.dataframe(recent, use_container_width=True)

st.divider()

# -------------------------------------------------
# BEER BRAND INSIGHTS
# -------------------------------------------------
st.subheader("🍻 Beer Brand Insights")

brand_summary = filtered_df.groupby('MenuGroupDescription').agg(
    Unique_Guests=('Customer Mobile No', 'nunique'),
    Quantity_Sold=('Quantity', 'sum'),
    Revenue=('Gross Amount', 'sum')
).reset_index().sort_values(by='Revenue', ascending=False)

st.dataframe(brand_summary, use_container_width=True)

st.write("### Revenue Contribution by Brand")
st.bar_chart(brand_summary.set_index('MenuGroupDescription')['Revenue'])

st.write("### Unique Guests by Brand")
st.bar_chart(brand_summary.set_index('MenuGroupDescription')['Unique_Guests'])

top_brand = brand_summary.iloc[0]['MenuGroupDescription']
low_brand = brand_summary.iloc[-1]['MenuGroupDescription']

st.success(f"🏆 Most Preferred Category: {top_brand}")
st.warning(f"⚠ Low Performing Category: {low_brand}")

st.divider()

# -------------------------------------------------
# GUEST BRAND PREFERENCE
# -------------------------------------------------
st.subheader("👤 Guest Beer Brand Preference")

guest_pref = filtered_df.groupby(
    ['Customer Mobile No','MenuGroupDescription']
).size().reset_index(name='Orders')

st.dataframe(
    guest_pref.sort_values(by='Orders', ascending=False).head(20),
    use_container_width=True
)