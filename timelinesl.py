import streamlit as st
import plotly.express as px
import pandas as pd
import os
import io
import random
from datetime import datetime

# ── Page setup ──
st.set_page_config(layout="wide")
st.title("📆 TNB Tariff Communication Timeline (Gantt + Matrix View)")
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

# ── Sidebar Settings ──
st.sidebar.header("⚙️ Settings")
view_mode = st.sidebar.radio("View Mode", ["Gantt Chart", "Matrix View"])
show_save = st.sidebar.checkbox("Show Save Button", value=True)
show_download = st.sidebar.checkbox("Show Download Button", value=True)

# ── Editable Table ──
st.subheader("📝 Edit Task Dates Inline")
df_edit = st.data_editor(
    df,
    num_rows="fixed",
    column_config={
        "Start": st.column_config.DateColumn("Start"),
        "Finish": st.column_config.DateColumn("Finish"),
        "Duration (days)": st.column_config.NumberColumn("Duration (days)", disabled=True),
    }
)

# ── Save Button ──
if show_save:
    if st.button("💾 Save Timeline", type="primary"):
        df_edit["Duration (days)"] = (df_edit["Finish"] - df_edit["Start"]).dt.days
        df_edit.to_csv(SAVE_PATH, index=False)
        st.success("✅ Timeline saved successfully!")

# ── Download Excel Button ──
if show_download:
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        df_edit.to_excel(writer, index=False, sheet_name="Timeline")
    st.download_button(
        label="📥 Download Timeline as Excel",
        data=excel_buffer,
        file_name="tnb_timeline.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ── View Selection ──
st.subheader(f"📊 {view_mode}")

if not df_edit["Start"].isna().all():

    chart_df = df_edit.dropna(subset=["Start", "Finish"]).copy()

    # 🛠 Force correct task order
    chart_df["Task"] = pd.Categorical(chart_df["Task"], categories=topics, ordered=True)
    chart_df = chart_df.sort_values("Task")

    if view_mode == "Gantt Chart":
        fig = px.timeline(
            chart_df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Task"
        )
        fig.update_traces(width=0.9, offset=0)
        fig.update_yaxes(
            categoryorder='array',
            categoryarray=topics[::-1],  # 🛠 Manual y-axis task order
            showgrid=True
        )
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
            showgrid=True
        )
        today = datetime.today()
        fig.add_vline(x=today, line_width=2, line_dash="dash", line_color="red")

        st.plotly_chart(fig, use_container_width=True)

    elif view_mode == "Matrix View":
        def month_week_label(date):
            if pd.isnull(date):
                return None
            month_start = pd.Timestamp(date.year, date.month, 1)
            week_count = 0
            for d in pd.date_range(start=month_start, end=date):
                if d.weekday() < 5:  # Mon-Fri only
                    if d == date:
                        break
                    if d.weekday() == 0 and (d - month_start).days != 0:
                        week_count += 1
            return f"{date.strftime('%b')} W{week_count + 1}"

        task_week_mapping = {}
        for idx, row in chart_df.iterrows():
            start_date = row["Start"]
            finish_date = row["Finish"]
            all_dates = pd.date_range(start=start_date, end=finish_date, freq="D")
            working_days = all_dates[all_dates.weekday < 5]
            week_labels = working_days.map(month_week_label).unique()
            task_week_mapping[row["Task"]] = week_labels

        ordered_tasks = [task for task in topics if task in chart_df["Task"].values]
        all_weeks = sorted(set(label for labels in task_week_mapping.values() for label in labels))
        grid = pd.DataFrame("", index=ordered_tasks, columns=all_weeks)

        for task, weeks in task_week_mapping.items():
            for week in weeks:
                grid.at[task, week] = "active"

        # 🎨 Random colors for each task
        task_colors = {}
        for task in topics:
            r = random.randint(100, 255)
            g = random.randint(100, 255)
            b = random.randint(100, 255)
            task_colors[task] = f'rgb({r},{g},{b})'

        def style_matrix(val, task=None):
            if val == "active" and task:
                return f'background-color: {task_colors.get(task, "lightcoral")}; color: black; text-align: center; font-weight: bold;'
            return 'text-align: center;'

        styled_grid = grid.copy()
        for task in grid.index:
            styled_grid.loc[task] = grid.loc[task].apply(lambda val: style_matrix(val, task=task))

        st.dataframe(styled_grid, use_container_width=True)

else:
    st.info("⏳ Please add Start and Finish dates to see the timeline.")
import streamlit as st
import plotly.express as px
import pandas as pd
import os
import io
import random
from datetime import datetime

# ── Page setup ──
st.set_page_config(layout="wide")
st.title("📆 TNB Tariff Communication Timeline (Gantt + Matrix View)")
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

# ── Sidebar Settings ──
st.sidebar.header("⚙️ Settings")
view_mode = st.sidebar.radio("View Mode", ["Gantt Chart", "Matrix View"])
show_save = st.sidebar.checkbox("Show Save Button", value=True)
show_download = st.sidebar.checkbox("Show Download Button", value=True)

# ── Editable Table ──
st.subheader("📝 Edit Task Dates Inline")
df_edit = st.data_editor(
    df,
    num_rows="fixed",
    column_config={
        "Start": st.column_config.DateColumn("Start"),
        "Finish": st.column_config.DateColumn("Finish"),
        "Duration (days)": st.column_config.NumberColumn("Duration (days)", disabled=True),
    }
)

# ── Save Button ──
if show_save:
    if st.button("💾 Save Timeline", type="primary"):
        df_edit["Duration (days)"] = (df_edit["Finish"] - df_edit["Start"]).dt.days
        df_edit.to_csv(SAVE_PATH, index=False)
        st.success("✅ Timeline saved successfully!")

# ── Download Excel Button ──
if show_download:
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        df_edit.to_excel(writer, index=False, sheet_name="Timeline")
    st.download_button(
        label="📥 Download Timeline as Excel",
        data=excel_buffer,
        file_name="tnb_timeline.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ── View Selection ──
st.subheader(f"📊 {view_mode}")

if not df_edit["Start"].isna().all():

    chart_df = df_edit.dropna(subset=["Start", "Finish"]).copy()

    # 🛠 Force correct task order
    chart_df["Task"] = pd.Categorical(chart_df["Task"], categories=topics, ordered=True)
    chart_df = chart_df.sort_values("Task")

    if view_mode == "Gantt Chart":
        fig = px.timeline(
            chart_df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Task"
        )
        fig.update_traces(width=0.9, offset=0)
        fig.update_yaxes(
            categoryorder='array',
            categoryarray=topics[::-1],  # 🛠 Manual y-axis task order
            showgrid=True
        )
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
            showgrid=True
        )
        today = datetime.today()
        fig.add_vline(x=today, line_width=2, line_dash="dash", line_color="red")

        st.plotly_chart(fig, use_container_width=True)

    elif view_mode == "Matrix View":
        def month_week_label(date):
            if pd.isnull(date):
                return None
            month_start = pd.Timestamp(date.year, date.month, 1)
            week_count = 0
            for d in pd.date_range(start=month_start, end=date):
                if d.weekday() < 5:  # Mon-Fri only
                    if d == date:
                        break
                    if d.weekday() == 0 and (d - month_start).days != 0:
                        week_count += 1
            return f"{date.strftime('%b')} W{week_count + 1}"

        task_week_mapping = {}
        for idx, row in chart_df.iterrows():
            start_date = row["Start"]
            finish_date = row["Finish"]
            all_dates = pd.date_range(start=start_date, end=finish_date, freq="D")
            working_days = all_dates[all_dates.weekday < 5]
            week_labels = working_days.map(month_week_label).unique()
            task_week_mapping[row["Task"]] = week_labels

        ordered_tasks = [task for task in topics if task in chart_df["Task"].values]
        all_weeks = sorted(set(label for labels in task_week_mapping.values() for label in labels))
        grid = pd.DataFrame("", index=ordered_tasks, columns=all_weeks)

        for task, weeks in task_week_mapping.items():
            for week in weeks:
                grid.at[task, week] = "active"

        # 🎨 Random colors for each task
        task_colors = {}
        for task in topics:
            r = random.randint(100, 255)
            g = random.randint(100, 255)
            b = random.randint(100, 255)
            task_colors[task] = f'rgb({r},{g},{b})'

        def style_matrix(val, task=None):
            if val == "active" and task:
                return f'background-color: {task_colors.get(task, "lightcoral")}; color: black; text-align: center; font-weight: bold;'
            return 'text-align: center;'

        styled_grid = grid.copy()
        for task in grid.index:
            styled_grid.loc[task] = grid.loc[task].apply(lambda val: style_matrix(val, task=task))

        st.dataframe(styled_grid, use_container_width=True)

else:
    st.info("⏳ Please add Start and Finish dates to see the timeline.")
