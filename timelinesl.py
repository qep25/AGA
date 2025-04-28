import streamlit as st
import plotly.express as px
import pandas as pd
import os
import io
from datetime import datetime

# ── Page setup ──
st.set_page_config(layout="wide")
st.title("📆 TNB Tariff Communication Timeline")
st.markdown("Use the editor below to update task dates directly. Duration will update automatically.")

SAVE_PATH = "saved_timeline.csv"

# ── Full topic list ──
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

# ── Load or Create DataFrame safely ──
if os.path.exists(SAVE_PATH):
    try:
        df = pd.read_csv(SAVE_PATH)
        if not {"Task", "Start", "Finish"}.issubset(df.columns):
            raise ValueError("Missing required columns.")
        df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
        df["Finish"] = pd.to_datetime(df["Finish"], errors="coerce")
    except Exception:
        df = pd.DataFrame({"Task": topics})
        df["Start"] = pd.NaT
        df["Finish"] = pd.NaT
else:
    df = pd.DataFrame({"Task": topics})
    df["Start"] = pd.NaT
    df["Finish"] = pd.NaT

# ── Calculate Duration ──
df["Duration (days)"] = (df["Finish"] - df["Start"]).dt.days

# ── Sidebar settings ──
st.sidebar.header("⚙️ Graph Settings")
show_grid = st.sidebar.checkbox("Show X and Y Axis Grid", value=True)
show_border = st.sidebar.checkbox("Show Task Bar Borders", value=False)
add_today_line = st.sidebar.checkbox("Add Vertical Line for Today", value=False)
view_mode = st.sidebar.radio("View Mode", ["Gantt Chart", "Table View"])
time_view = st.sidebar.radio("Timeline X-axis Type", ["Date View", "Week View (5 days)"])

# ── Editable table ──
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

# ── Unsaved warning ──
edited = not df_edit.equals(df)
if edited:
    st.warning("⚠️ You have unsaved changes. Don't forget to click '💾 Save Timeline'!")

# ── Save button ──
if st.button("💾 Save Timeline", type="primary"):
    df_edit["Duration (days)"] = (df_edit["Finish"] - df_edit["Start"]).dt.days
    df_edit.to_csv(SAVE_PATH, index=False)
    st.success("✅ Timeline saved successfully!")

# ── Download Excel button ──
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    df_edit.to_excel(writer, index=False, sheet_name="Timeline")

st.download_button(
    label="📥 Download Timeline as Excel",
    data=excel_buffer,
    file_name="tnb_timeline.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ── Gantt Chart or Table View ──
st.subheader("📊 Timeline View")

if view_mode == "Gantt Chart":
    if not df_edit["Start"].isna().all():
        chart_df = df_edit.dropna(subset=["Start", "Finish"]).copy()

        if time_view == "Week View (5 days)":
            start_reference = pd.Timestamp("2025-03-10")  # Monday

            # Custom working days calculation
            def working_days_since_start(date):
                if pd.isnull(date):
                    return None
                days = (date - start_reference).days
                full_weeks = days // 7
                extra_days = days % 7
                weekdays_count = full_weeks * 5
                if extra_days > 4:
                    weekdays_count += 5
                else:
                    weekdays_count += extra_days
                return weekdays_count // 5 + 1

            # Apply custom week calculation
            chart_df["Start Week"] = chart_df["Start"].apply(working_days_since_start)
            chart_df["Finish Week"] = chart_df["Finish"].apply(working_days_since_start)

            chart_df["Start"] = chart_df["Start Week"]
            chart_df["Finish"] = chart_df["Finish Week"]

            fig = px.timeline(
                chart_df,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Task"
            )

            fig.update_traces(width=0.9, offset=0)
            fig.update_yaxes(autorange="reversed", showgrid=show_grid)
            fig.update_layout(
                showlegend=False,
                height=1000,
                margin=dict(l=50, r=50, t=50, b=50),
                bargap=0
            )

            max_week = int(chart_df["Finish"].max()) + 1
            fig.update_xaxes(
                tickvals=list(range(1, max_week)),
                ticktext=[f"Week {i}" for i in range(1, max_week)],
                tickangle=0,
                showgrid=show_grid
            )

            if add_today_line:
                today = pd.Timestamp(datetime.today())
                today_working_days = working_days_since_start(today)
                fig.add_vline(x=today_working_days, line_width=2, line_dash="dash", line_color="red")

        else:  # Normal Date View
            fig = px.timeline(
                chart_df,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Task"
            )
            fig.update_traces(width=0.9, offset=0)
            fig.update_yaxes(autorange="reversed", showgrid=show_grid)
            fig.update_layout(
                showlegend=False,
                height=1000,
                margin=dict(l=50, r=50, t=50, b=50),
                bargap=0
            )
            fig.update_xaxes(
                dtick="D3",
                tickformat="%d %b",
                tickangle=30,
                showgrid=show_grid
            )

            if add_today_line:
                today = datetime.today()
                fig.add_vline(x=today, line_width=2, line_dash="dash", line_color="red")

        if show_border:
            fig.update_traces(marker_line_color='black', marker_line_width=1)

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("⏳ Add Start and Finish dates to tasks to generate Gantt chart.")

elif view_mode == "Table View":
    st.dataframe(df_edit, use_container_width=True)
