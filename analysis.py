# -*- coding: utf-8 -*-
"""Reusable analysis logic for the Nassau Candy Distributor shipment data.

Refactored from unifiedmentorproject.py so the same computations can be
called from a Streamlit app (or anywhere else) on an in-memory DataFrame
instead of reading/writing files on disk.
"""

import pandas as pd
import numpy as np

# ==============================
# CONFIGURATION
# ==============================
DELAY_THRESHOLD_DAYS = 5

# Dataset columns
COL_ORDER_DATE = "Order Date"
COL_SHIP_DATE = "Ship Date"
COL_SHIP_MODE = "Ship Mode"
COL_COUNTRY = "Country/Region"
COL_CITY = "City"
COL_STATE = "State/Province"
COL_REGION = "Region"
COL_DIVISION = "Division"
COL_CUSTOMER_ID = "Customer ID"

REQUIRED_COLS = [
    COL_ORDER_DATE, COL_SHIP_DATE, COL_SHIP_MODE,
    COL_COUNTRY, COL_CITY, COL_STATE, COL_REGION,
    COL_DIVISION, COL_CUSTOMER_ID
]

# Output filenames, kept for download-button labels so they match what the
# original script would have written to disk.
OUTPUT_CLEAN_FILE = "cleaned_shipments.csv"
OUTPUT_ROUTE_STATE_FILE = "route_state_summary.csv"
OUTPUT_ROUTE_REGION_FILE = "route_region_summary.csv"
OUTPUT_STATE_FILE = "state_summary.csv"
OUTPUT_REGION_FILE = "region_summary.csv"
OUTPUT_SHIPMODE_FILE = "shipmode_summary.csv"
OUTPUT_KPI_FILE = "kpi_summary.csv"
OUTPUT_TOP10_FILE = "top_10_routes.csv"
OUTPUT_BOTTOM10_FILE = "bottom_10_routes.csv"
OUTPUT_BOTTLENECK_FILE = "bottleneck_routes.csv"


def load_and_validate(uploaded_file):
    df = pd.read_csv(uploaded_file)
    df.columns = [c.strip() for c in df.columns]
    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    return df


def clean_data(df):
    df = df.copy()
    df[COL_ORDER_DATE] = pd.to_datetime(df[COL_ORDER_DATE], errors="coerce")
    df[COL_SHIP_DATE] = pd.to_datetime(df[COL_SHIP_DATE], errors="coerce")

    df = df.dropna(subset=REQUIRED_COLS).copy()
    df = df.dropna(subset=[COL_ORDER_DATE, COL_SHIP_DATE]).copy()

    for col in [COL_SHIP_MODE, COL_COUNTRY, COL_CITY, COL_STATE, COL_REGION, COL_DIVISION]:
        df[col] = df[col].astype(str).str.strip().str.title()

    df["Shipping Lead Time"] = (df[COL_SHIP_DATE] - df[COL_ORDER_DATE]).dt.days
    df = df[df["Shipping Lead Time"].notna()].copy()
    df = df[df["Shipping Lead Time"] >= 0].copy()

    df["Delayed"] = (df["Shipping Lead Time"] > DELAY_THRESHOLD_DAYS).astype(int)
    return df


def add_route_features(df):
    df = df.copy()
    df["Route_State"] = df[COL_DIVISION].astype(str) + " -> " + df[COL_STATE].astype(str)
    df["Route_Region"] = df[COL_DIVISION].astype(str) + " -> " + df[COL_REGION].astype(str)
    return df


def summarize_routes(df, group_col):
    summary = (
        df.groupby(group_col)
          .agg(
              Total_Shipments=("Shipping Lead Time", "size"),
              Avg_Lead_Time=("Shipping Lead Time", "mean"),
              Lead_Time_Variability=("Shipping Lead Time", "std"),
              Delay_Frequency=("Delayed", "mean")
          )
          .reset_index()
    )
    summary["Lead_Time_Variability"] = summary["Lead_Time_Variability"].fillna(0)

    lt_norm = 1 - (summary["Avg_Lead_Time"] - summary["Avg_Lead_Time"].min()) / (
        summary["Avg_Lead_Time"].max() - summary["Avg_Lead_Time"].min() + 1e-9
    )
    var_norm = 1 - (summary["Lead_Time_Variability"] - summary["Lead_Time_Variability"].min()) / (
        summary["Lead_Time_Variability"].max() - summary["Lead_Time_Variability"].min() + 1e-9
    )
    vol_norm = (summary["Total_Shipments"] - summary["Total_Shipments"].min()) / (
        summary["Total_Shipments"].max() - summary["Total_Shipments"].min() + 1e-9
    )

    summary["Route_Efficiency_Score"] = 0.5 * lt_norm + 0.3 * var_norm + 0.2 * vol_norm
    return summary.sort_values(
        by=["Avg_Lead_Time", "Lead_Time_Variability", "Delay_Frequency"],
        ascending=[True, True, True]
    )


def summarize_geo(df, group_col):
    summary = (
        df.groupby(group_col)
          .agg(
              Total_Shipments=("Shipping Lead Time", "size"),
              Avg_Lead_Time=("Shipping Lead Time", "mean"),
              Lead_Time_Variability=("Shipping Lead Time", "std"),
              Delay_Frequency=("Delayed", "mean")
          )
          .reset_index()
          .sort_values(by=["Avg_Lead_Time", "Total_Shipments"], ascending=[False, False])
    )
    summary["Lead_Time_Variability"] = summary["Lead_Time_Variability"].fillna(0)
    return summary


def compute_bottlenecks(route_state_summary):
    volume_threshold = route_state_summary["Total_Shipments"].quantile(0.75)
    leadtime_threshold = route_state_summary["Avg_Lead_Time"].quantile(0.75)

    return route_state_summary[
        (route_state_summary["Total_Shipments"] >= volume_threshold) &
        (route_state_summary["Avg_Lead_Time"] >= leadtime_threshold)
    ].copy()


def summarize_shipmode(df):
    shipmode_summary = (
        df.groupby(COL_SHIP_MODE)
          .agg(
              Total_Shipments=("Shipping Lead Time", "size"),
              Avg_Lead_Time=("Shipping Lead Time", "mean"),
              Lead_Time_Variability=("Shipping Lead Time", "std"),
              Delay_Frequency=("Delayed", "mean")
          )
          .reset_index()
          .sort_values(by="Avg_Lead_Time", ascending=True)
    )
    shipmode_summary["Lead_Time_Variability"] = shipmode_summary["Lead_Time_Variability"].fillna(0)

    common_labels = {"Standard Class", "Second Class", "First Class", "Same Day"}
    if common_labels.intersection(set(df[COL_SHIP_MODE].unique())):
        shipmode_note = "Ship mode comparison available."
    else:
        shipmode_note = (
            "Ship mode values may differ from common labels "
            "(Standard Class, Second Class, First Class, Same Day)."
        )
    return shipmode_summary, shipmode_note


def build_kpi_summary(df, route_state_summary):
    return pd.DataFrame({
        "KPI": [
            "Shipping Lead Time",
            "Average Lead Time",
            "Route Volume",
            "Delay Frequency",
            "Route Efficiency Score"
        ],
        "Description": [
            "Ship Date - Order Date",
            "Mean shipping duration per route",
            "Number of orders per route",
            "% of shipments exceeding threshold",
            "Normalized lead-time performance"
        ],
        "Value": [
            df["Shipping Lead Time"].mean(),
            route_state_summary["Avg_Lead_Time"].mean(),
            route_state_summary["Total_Shipments"].sum(),
            df["Delayed"].mean(),
            route_state_summary["Route_Efficiency_Score"].mean()
        ]
    })


def run_analysis(df):
    """Run the full pipeline on a raw (already loaded/validated) DataFrame.

    Returns a dict of all result tables, matching the CSVs the original
    script writes to disk.
    """
    df = clean_data(df)
    df = add_route_features(df)

    route_state_summary = summarize_routes(df, "Route_State")
    route_region_summary = summarize_routes(df, "Route_Region")

    top_10_routes = route_state_summary.head(10).copy()
    bottom_10_routes = route_state_summary.tail(10).copy()

    state_summary = summarize_geo(df, COL_STATE)
    region_summary = summarize_geo(df, COL_REGION)

    bottleneck_routes = compute_bottlenecks(route_state_summary)

    shipmode_summary, shipmode_note = summarize_shipmode(df)

    kpi_summary = build_kpi_summary(df, route_state_summary)

    return {
        "cleaned": df,
        "route_state_summary": route_state_summary,
        "route_region_summary": route_region_summary,
        "top_10_routes": top_10_routes,
        "bottom_10_routes": bottom_10_routes,
        "state_summary": state_summary,
        "region_summary": region_summary,
        "shipmode_summary": shipmode_summary,
        "shipmode_note": shipmode_note,
        "kpi_summary": kpi_summary,
        "bottleneck_routes": bottleneck_routes,
    }
