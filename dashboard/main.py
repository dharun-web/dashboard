import streamlit as st
import pandas as pd
import plotly.express as px

# Define known states and a replacement map for standardizing state names
KNOWN_STATES = sorted([
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya',
    'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim',
    'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
    'West Bengal', 'Foreign', 'Unknown', 'Telangana/Andhra Pradesh'
])

REPLACEMENT_MAP = {
    'AndhraPradesh': 'Andhra Pradesh',
    'TamilNadu': 'Tamil Nadu',
    'Telagana': 'Telangana',
    'India (State Undetermined)': 'Unknown',
    'Overseas': 'Foreign',
    'LKDFJAKLD': 'Unknown',
    'India': 'Unknown',
    'Telengana': 'Telangana',
    'Telangana State': 'Telangana',
    'Andhra Pradesh / Telangana': 'Telangana/Andhra Pradesh',
    'Andhra Pradesh /Telangana': 'Telangana/Andhra Pradesh',
    'Andhra Pradesh / Telangana ': 'Telangana/Andhra Pradesh'
}


def determine_state_logic(college_val, replacement_map, known_states_list):
    """Determines the state based on the college entry string."""
    if pd.isna(college_val):
        return 'Unknown'
    college_str = str(college_val).strip()
    if '-' in college_str:
        return 'Telangana'
    potential_state = replacement_map.get(college_str, college_str)
    if potential_state in known_states_list:
        return potential_state
    return 'Unknown'


def load_data(uploaded_file):
    """Load and process the student data"""
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        return pd.DataFrame()

    if 'college' not in df.columns:
        st.error("CSV must contain a 'college' column.")
        return pd.DataFrame()

    # Ensure 'email' column exists, if not, it won't be used in displays later
    # No error is raised here as 'email' is "recommended", not "required" by instructions

    df['state'] = df['college'].apply(lambda x: determine_state_logic(x, REPLACEMENT_MAP, KNOWN_STATES))
    df['college_name'] = df.apply(
        lambda row: str(row['college']).split('-', 1)[1].strip()
        if row['state'] == 'Telangana' and isinstance(row['college'], str) and '-' in str(row['college'])
        else None,
        axis=1
    )
    return df


def get_displayable_columns(df, desired_cols):
    """
    Filters a list of desired column names to include only those
    that actually exist in the DataFrame.
    """
    return [col for col in desired_cols if col in df.columns]


def main():
    st.set_page_config(page_title="College-State Analytics", layout="wide")
    st.title("🎓 College & State Analytics Dashboard")

    uploaded_file = st.file_uploader("Add student data in the form of csv", type=["csv"])

    if uploaded_file:
        df_processed = load_data(uploaded_file)

        if df_processed.empty and not ('college' in df_processed.columns):  # Handles error from load_data
            return  # Error messages are shown in load_data
        if df_processed.empty:
            st.warning("No data to display. The file might be empty or processed with no valid records.")
            return

        st.sidebar.header("Filters")
        if 'state' in df_processed.columns and not df_processed['state'].empty:
            state_options = sorted([s for s in df_processed['state'].unique() if pd.notna(s)])
        else:
            state_options = []

        selected_state = st.sidebar.selectbox("Select State", ["All"] + state_options)

        if selected_state == "All":
            filtered_df = df_processed
        else:
            filtered_df = df_processed[df_processed['state'] == selected_state]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Students", len(df_processed))
        if 'state' in df_processed.columns:
            col2.metric("States Represented", df_processed['state'].nunique())
            telangana_count = len(df_processed[df_processed['state'] == 'Telangana'])
            col3.metric("Telangana Students", telangana_count)
        else:
            col2.metric("States Represented", 0)
            col3.metric("Telangana Students", 0)

        tab1, tab2, tab3 = st.tabs(["State Analytics", "College Details", "Raw Data"])

        with tab1:
            st.subheader("Student Distribution by State")
            if 'state' in df_processed.columns and not df_processed['state'].empty:
                fig_pie = px.pie(df_processed, names='state', hole=0.3, title="Overall Student Distribution by State")
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)

                state_counts_series = df_processed['state'].value_counts()
                state_counts_df = state_counts_series.reset_index()
                state_counts_df.columns = ['state_name', 'count']
                fig_bar_state = px.bar(state_counts_df, x='state_name', y='count', color='state_name',
                                       title="Student Count by State",
                                       labels={'state_name': 'State', 'count': 'Number of Students'})
                fig_bar_state.update_layout(xaxis_title="State", yaxis_title="Number of Students")
                st.plotly_chart(fig_bar_state, use_container_width=True)
            else:
                st.info("No state data available to display charts.")

        with tab2:
            st.subheader(f"Details for: {selected_state}")
            if selected_state == "Telangana":
                # Ensure 'college_name' column exists and is not all NaN for Telangana students
                if 'college_name' in filtered_df.columns and \
                        not filtered_df.loc[filtered_df['state'] == 'Telangana', 'college_name'].isnull().all():

                    telangana_colleges_df = filtered_df[filtered_df['state'] == 'Telangana']
                    college_counts_series = telangana_colleges_df['college_name'].value_counts()
                    college_counts_df = college_counts_series.reset_index()
                    college_counts_df.columns = ['college', 'student_count']
                    college_counts_df_display = college_counts_df[college_counts_df['college'].str.strip() != '']

                    st.dataframe(college_counts_df_display.rename(
                        columns={'college': 'College Name', 'student_count': 'Student Count'}))

                    if not college_counts_df_display.empty:
                        fig_bar_college = px.bar(college_counts_df_display.head(10),
                                                 x='college', y='student_count', color='college',
                                                 title="Top 10 Telangana Colleges by Student Count",
                                                 labels={'college': 'College Name',
                                                         'student_count': 'Number of Students'})
                        fig_bar_college.update_layout(xaxis_title="College Name", yaxis_title="Number of Students")
                        st.plotly_chart(fig_bar_college, use_container_width=True)
                    else:
                        st.info("No valid college names found to plot for Telangana for the current selection.")
                else:
                    st.info(
                        "No specific college name data available to display for Telangana. This could be due to data formatting or no Telangana students in the current filter.")

            elif selected_state != "All":
                st.info(f"Showing student list from {selected_state}")
                desired_cols = ['email', 'college', 'state']
                cols_to_display = get_displayable_columns(filtered_df, desired_cols)
                if cols_to_display:
                    st.dataframe(filtered_df[cols_to_display])
                else:
                    st.warning(
                        f"No standard columns (e.g., 'email', 'college', 'state') found to display for {selected_state}.")

            else:  # selected_state == "All"
                st.info(
                    "Select a specific state from the sidebar for more details, or 'Telangana' for college-specific analytics.")
                desired_cols_preview = ['email', 'college', 'state']  # Show these key columns if they exist
                cols_to_preview = get_displayable_columns(filtered_df, desired_cols_preview)
                if cols_to_preview:
                    st.dataframe(filtered_df[cols_to_preview].head(20),
                                 help="Showing first 20 rows of all students (relevant columns).")
                else:
                    st.warning("No standard columns (e.g., 'email', 'college', 'state') found for preview.")

        with tab3:
            st.subheader("Processed Student Data Inspector")
            st.dataframe(df_processed)  # Displays all columns from the processed DataFrame

            if st.button("Export Full Processed Data"):
                csv_export = df_processed.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Processed Data as CSV",
                    data=csv_export,
                    file_name="student_data_processed_export.csv",
                    mime="text/csv"
                )
    else:
        st.info("👋 Welcome! Please upload a student data CSV file to begin analysis.")
        st.markdown("""
        **Expected CSV Data Format:**
        - A CSV file with at least two columns. One column must be named `college`.
        - An `email` column (or similar student identifier) is **recommended** for data display but not strictly required by the application logic.
        - **For Telangana colleges:** The `college` column should ideally follow the format `CODE - COLLEGE NAME` (e.g., `VJIT - VIDYAJYOTHI INSTITUTE OF TECHNOLOGY`). The presence of a hyphen `-` is key for identifying these.
        - **For other states/entries:** The `college` column should contain the state name (e.g., `Andhra Pradesh`, `Karnataka`), a known alias (e.g., `Overseas`), or it will be categorized as 'Unknown' if not recognized.

        The application will parse state information and, for Telangana, attempt to extract specific college names.
        """)


if __name__ == "__main__":
    main()