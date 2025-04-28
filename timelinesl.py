import streamlit as st
import plotly.express as px
import pandas as pd
import os
from datetime import datetime

# Page config
st.set_page_config(layout="wide")
st.title("📆 TNB Tariff Communication Timeline")
st.markdown("Use the editor below to update task dates directly. Duration will update automatically.")

SAVE_PATH = "saved_timeline.csv"

# Full topic list
topics = [
    "1. Majority of Households Are Not Affected",
    "2. The Tariff Hike is Targeted and Fair",
    "3. Necessary for Grid Reliability, Better Service and Future Growth",
    "4. Reinvestment into Public Goods",
    "5. Still Among the Lowest Rates in the Region",
    "6. Tied to Global Fuel Prices – Not Arbitrary",
    "7. Protects Malaysia’s Financial Stability",
    "8. Encourages Energy Efficiency",
    "9. Supports Malaysia’s Green Transition",
    "10. Backed by Transparent Regulatory Process",
    "11. Minimal Impact on Inflation",
    "12. Businesses Are Being Engaged and Supported",
    "13. Successful International Models Show This Works",
    "14. Proactive Communication & Crisis Planning",
    "15. Tariff Hike Covers Real Costs – Not Profit",
    "16. Strict Government Oversight",
    "17. Past Hikes Have Been Gradual & Well Cushioned",
    "18. Misconceptions Must Be Cleared",
    "19. Energy Efficiency = Empowerment",
    "A. Blackout Cases in Malaysia",
    "B. Case Studies on Tariff Increases for Modernization",
    "C. Comparison ASEAN Tariff",
    "D. Effects of the New Tariff Hike to SMEs",
    "E. Overall Sentiment Toward TNB Tariff Hike",
    "F. Overview of TNB’s RM42.8B Investment for RP4",
    "G. Regulatory or Auditing Bodies Monitor Spending",
    "H. Targeted Subsidies to Support Low-Income Users"
]

# ——— Robust CSV loading ———
if os.path.exists(SAVE_PATH):
    try:
        df = pd.read_csv(SAVE_PATH, parse_dates=["Start", "Finish"])
        if not {"Task", "Start", "Finish"}.issubset(df.columns):
            raise ValueError("Invalid columns")
    except Exception:
        df = pd.DataFrame({"Task": topics})
        df["Start"] = pd.NaT
        df["Finish"] = pd.NaT
else:
    df = pd.DataFrame({"Task": topics})
    df["Start"] = pd.NaT
    df["Finish"] = pd.NaT
# ————————————————————————

# Calculate Duration
df["Duration (days)"] = (df["Finish"] - df["Start"]).dt.days

# Sidebar settings
st.sidebar.header("⚙️ Graph Settings")
show_grid       = st.sidebar.checkbox("Show X and Y Axis Grid", value=True)
show_border     = st.sidebar.checkbox("Show Task Bar Borders (Timeline only)", value=False)
add_today_line  = st.sidebar.checkbox("Add Vertical Line for Today (Timeline only)", value=False)
view_mode       = st.sidebar.radio("View Mode", ["Gantt Chart (Timeline)", "Gantt Chart (Bar Chart)", "Table View"])

# Editable table
st.subheader("📝 Edit Dates Inline")
df_edit = st.data_editor(
    df,
    num_rows="fixed",
    column_config={
        "Start": st.column_config.DateColumn("Start"),
        "Finish": st.column_config.DateColumn("Finish"),
        "Duration (days)": st.column_config.NumberColumn("Duration (days)", disabled=True),
    }
)

# Recalculate and save
df_edit["Duration (days)"] = (df_edit["Finish"] - df_edit["Start"]).dt.days
df_edit.to_csv(SAVE_PATH, index=False)

# Render View
st.subheader("📊 Timeline View")

if view_mode == "Gantt Chart (Timeline)":
    if not df_edit["Start"].isna().all():
        chart_df = df_edit.dropna(subset=["Start", "Finish"])
        fig = px.timeline(chart_df, x_start="Start", x_end="Finish", y="Task", color="Task")
        fig.update_traces(width=0.6)
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            showlegend=False,
            height=1000,
            margin=dict(l=50, r=50, t=50, b=50),
            bargap=0
        )
        fig.update_yaxes(
            categoryorder="total ascending",
            showgrid=show_grid
        )
        fig.update_xaxes(
            dtick="D3",
            tickformat="%d %b",
            tickangle=30,
            showgrid=show_grid
        )

        if show_border:
            fig.update_traces(marker_line_color='black', marker_line_width=1)
        if add_today_line:
            fig.add_vline(x=datetime.today(), line_width=2, line_dash="dash", line_color="red")

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("⏳ Add dates above to display the Gantt chart.")

elif view_mode == "Gantt Chart (Bar Chart)":
    if not df_edit["Start"].isna().all():
        chart_df = df_edit.dropna(subset=["Start", "Finish"])
        chart_df["Duration (days)"] = (chart_df["Finish"] - chart_df["Start"]).dt.days

        fig = px.bar(
            chart_df,
            x="Duration (days)",
            y="Task",
            orientation="h",
            color="Task",
            height=40 * len(chart_df),
        )
        fig.update_traces(texttemplate="%{x}d", textposition="inside")
        fig.update_layout(
            yaxis=dict(autorange="reversed", title=""),
            xaxis=dict(title="Duration (days)", showgrid=show_grid),
            bargap=0.0,
            margin=dict(l=50, r=50, t=50, b=50),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("⏳ Add dates above to display the bar Gantt chart.")

else:  # Table View
    st.dataframe(df_edit, use_container_width=True)
