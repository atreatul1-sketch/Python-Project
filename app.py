# -*- coding: utf-8 -*-
"""Streamlit app for the Nassau Candy Distributor shipment logistics analysis.

Always reads analysis.INPUT_FILE ("Nassau Candy Distributor.csv") from the
project directory and shows the same route / geography / ship-mode summaries
and KPIs that unifiedmentorproject.py produces, plus charts and CSV
downloads. See analysis.py for the underlying computations and
doc/explanation.md for a plain-language walkthrough.
"""

import os

import streamlit as st

import analysis

st.set_page_config(page_title="Candy Distributor Shipment Analysis", layout="wide")

st.title("Candy Distributor Shipment Logistics Analysis")
st.write(
    f"Shipping lead-time, route efficiency, geography, and ship-mode "
    f"performance summaries for `{analysis.INPUT_FILE}`."
)

if not os.path.exists(analysis.INPUT_FILE):
    st.error(
        f"Could not find `{analysis.INPUT_FILE}` in the project folder. "
        "Place the file there and reload the app."
    )
    st.stop()


@st.cache_data(show_spinner="Running analysis...")
def run_pipeline(path, mtime):
    raw_df = analysis.load_and_validate(path)
    return analysis.run_analysis(raw_df)


try:
    results = run_pipeline(analysis.INPUT_FILE, os.path.getmtime(analysis.INPUT_FILE))
except ValueError as e:
    st.error(str(e))
    st.stop()

route_cols = [
    "Route_State", "Total_Shipments", "Avg_Lead_Time",
    "Lead_Time_Variability", "Delay_Frequency", "Route_Efficiency_Score"
]


def download_button(df, filename, key):
    st.download_button(
        "Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


st.header("Top 10 Most Efficient Routes")
st.dataframe(results["top_10_routes"][route_cols], use_container_width=True)
st.bar_chart(results["top_10_routes"].set_index("Route_State")["Route_Efficiency_Score"])
download_button(results["top_10_routes"], analysis.OUTPUT_TOP10_FILE, "dl_top10")

st.header("Bottom 10 Least Efficient Routes")
st.dataframe(results["bottom_10_routes"][route_cols], use_container_width=True)
st.bar_chart(results["bottom_10_routes"].set_index("Route_State")["Route_Efficiency_Score"])
download_button(results["bottom_10_routes"], analysis.OUTPUT_BOTTOM10_FILE, "dl_bottom10")

st.header("State Summary")
st.dataframe(results["state_summary"], use_container_width=True)
st.bar_chart(results["state_summary"].head(10).set_index(analysis.COL_STATE)["Avg_Lead_Time"])
download_button(results["state_summary"], analysis.OUTPUT_STATE_FILE, "dl_state")

st.header("Region Summary")
st.dataframe(results["region_summary"], use_container_width=True)
st.bar_chart(results["region_summary"].set_index(analysis.COL_REGION)["Avg_Lead_Time"])
download_button(results["region_summary"], analysis.OUTPUT_REGION_FILE, "dl_region")

st.header("Ship Mode Summary")
st.dataframe(results["shipmode_summary"], use_container_width=True)
st.bar_chart(results["shipmode_summary"].set_index(analysis.COL_SHIP_MODE)["Avg_Lead_Time"])
st.info(results["shipmode_note"])
download_button(results["shipmode_summary"], analysis.OUTPUT_SHIPMODE_FILE, "dl_shipmode")

st.header("KPI Summary")
st.dataframe(results["kpi_summary"], use_container_width=True)
download_button(results["kpi_summary"], analysis.OUTPUT_KPI_FILE, "dl_kpi")

st.header("Bottleneck Routes")
st.write("High-volume routes with above-average lead time (75th percentile on both).")
st.dataframe(results["bottleneck_routes"][route_cols], use_container_width=True)
download_button(results["bottleneck_routes"], analysis.OUTPUT_BOTTLENECK_FILE, "dl_bottleneck")

with st.expander("Download all results"):
    download_button(results["cleaned"], analysis.OUTPUT_CLEAN_FILE, "dl_clean")
    download_button(results["route_state_summary"], analysis.OUTPUT_ROUTE_STATE_FILE, "dl_route_state")
    download_button(results["route_region_summary"], analysis.OUTPUT_ROUTE_REGION_FILE, "dl_route_region")
    download_button(results["state_summary"], analysis.OUTPUT_STATE_FILE, "dl_state_all")
    download_button(results["region_summary"], analysis.OUTPUT_REGION_FILE, "dl_region_all")
    download_button(results["shipmode_summary"], analysis.OUTPUT_SHIPMODE_FILE, "dl_shipmode_all")
    download_button(results["kpi_summary"], analysis.OUTPUT_KPI_FILE, "dl_kpi_all")
    download_button(results["top_10_routes"], analysis.OUTPUT_TOP10_FILE, "dl_top10_all")
    download_button(results["bottom_10_routes"], analysis.OUTPUT_BOTTOM10_FILE, "dl_bottom10_all")
    download_button(results["bottleneck_routes"], analysis.OUTPUT_BOTTLENECK_FILE, "dl_bottleneck_all")
