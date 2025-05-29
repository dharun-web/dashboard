import streamlit as st
import pandas as pd
import plotly.express as px

# Define known states and a replacement map for standardizing state names
# These can be expanded as needed
KNOWN_STATES = sorted([
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya',
    'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim',
    'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
    'West Bengal', 'Foreign', 'Unknown', 'Telangana/Andhra Pradesh'
    # Add Union Territories if they are common in your data:
    # 'Andaman and Nicobar Islands', 'Chandigarh',
    # 'Dadra and Nagar Haveli and Daman and Diu', 'Delhi',
    # 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry',
])

REPLACEMENT_MAP = {
    'AndhraPradesh': 'Andhra Pradesh',
    'TamilNadu': 'Tamil Nadu',
    'Telagana': 'Telangana',
    'India (State Undetermined)': 'Unknown',
    'Overseas': 'Foreign',
    'LKDFJAKLD': 'Unknown',  # Example of handling garbage data
    'India': 'Unknown',  # Ambiguous entry
    'Telengana': 'Telangana',
    'Telangana State': 'Telangana',
    'Andhra Pradesh / Telangana': 'Telangana/Andhra Pradesh',
    'Andhra Pradesh /Telangana': 'Telangana/Andhra Pradesh',
    'Andhra Pradesh / Telangana ': 'Telangana/Andhra Pradesh'
    # Add more specific replacements if you find common typos or alternative names
    # e.g. 'AP' : 'Andhra Pradesh' (but be careful with short acronyms if they could be college codes)
}


def determine_state_logic(college_val, replacement_map, known_states_list):
    """Determines the state based on the college entry string."""
    if pd.isna(college_val):
        return 'Unknown'

    college_str = str(college_val).strip()

    # Rule 1: If '-' is present, it's highly likely a Telangana college based on 'CODE - NAME' format
    if '-' in college_str:
        # This implies Telangana. College name will be extracted later.
        # Could add further checks here if non-Telangana entries also use hyphens.
        return 'Telangana'

    # Rule 2: Apply explicit replacements from the map
    # This handles common misspellings, alternative names, or direct mappings like 'Overseas'.
    potential_state = replacement_map.get(college_str, college_str)

    # Rule 3: Check if the (original or replaced) string is a known state
    if potential_state in known_states_list:
        return potential_state

    # Rule 4: If not recognized after above checks, classify as 'Unknown'
    # This will catch entries like emails, company names, student names, etc., used in 'college' field.
    return 'Unknown'


def load_data(uploaded_file):
    """Load and process the student data"""
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        return pd.DataFrame()  # Return empty DataFrame

    if 'college' not in df.columns:
        st.error("CSV must contain a 'college' column.")
        return pd.DataFrame()

    # Determine state using the refined logic
    df['state'] = df['college'].apply(lambda x: determine_state_logic(x, REPLACEMENT_MAP, KNOWN_STATES))

    # Extract college names for Telangana entries that match the 'CODE - NAME' format
    df['college_name'] = df.apply(
        lambda row: str(row['college']).split('-', 1)[1].strip()
        if row['state'] == 'Telangana' and isinstance(row['college'], str) and '-' in str(row['college'])
        else None,
        axis=1
    )

    return df


def main():
    st.set_page_config(page_title="College-State Analytics", layout="wide")

    st.title("🎓 College & State Analytics Dashboard")

    # File upload
    uploaded_file = st.file_uploader("Add student data in the form of csv", type=["csv"])

    if uploaded_file:
        df_processed = load_data(uploaded_file)

        if df_processed.empty:
            # load_data would have already shown an error or the file is genuinely empty
            st.warning("No data to display. The file might be empty or couldn't be processed.")
            return

        # Sidebar filters
        st.sidebar.header("Filters")

        # Ensure 'state' column exists and has unique values for the selectbox
        if 'state' in df_processed.columns and not df_processed['state'].empty:
            state_options = sorted([s for s in df_processed['state'].unique() if pd.notna(s)])
        else:
            state_options = []  # Default to empty if no states found

        selected_state = st.sidebar.selectbox(
            "Select State",
            ["All"] + state_options
        )

        # Filter data based on selection
        if selected_state == "All":
            filtered_df = df_processed
        else:
            filtered_df = df_processed[df_processed['state'] == selected_state]

        # Dashboard metrics (calculated on the full, valid dataset)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Students", len(df_processed))

        if 'state' in df_processed.columns:
            col2.metric("States Represented", df_processed['state'].nunique())
            telangana_count = len(df_processed[df_processed['state'] == 'Telangana'])
            col3.metric("Telangana Students", telangana_count)
        else:
            col2.metric("States Represented", 0)
            col3.metric("Telangana Students", 0)

        # Tab layout
        tab1, tab2, tab3 = st.tabs(["State Analytics", "College Details", "Raw Data"])

        with tab1:
            st.subheader("Student Distribution by State")
            if 'state' in df_processed.columns and not df_processed['state'].empty:
                # State distribution pie chart
                fig_pie = px.pie(df_processed, names='state', hole=0.3, title="Overall Student Distribution by State")
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)

                # State-wise bar chart
                state_counts_series = df_processed['state'].value_counts()
                state_counts_df = state_counts_series.reset_index()
                state_counts_df.columns = ['state_name', 'count']  # Explicitly name columns

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
                if 'college_name' in filtered_df.columns and not filtered_df[filtered_df['state'] == 'Telangana'][
                    'college_name'].isnull().all():
                    telangana_colleges_df = filtered_df[filtered_df['state'] == 'Telangana']

                    college_counts_series = telangana_colleges_df['college_name'].value_counts()
                    college_counts_df = college_counts_series.reset_index()
                    college_counts_df.columns = ['college', 'student_count']  # Explicitly name columns

                    # Filter out entries where college name might be an empty string after processing
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
                        st.info("No valid college names found to plot for Telangana.")
                else:
                    st.info(
                        "No specific college name data available to display for Telangana. This could be due to formatting in the 'college' column (expected: 'CODE - COLLEGE NAME') or no Telangana students in the filter.")
            elif selected_state != "All":
                st.info(f"Showing student list from {selected_state}")
                # Display relevant columns for other states
                st.dataframe(filtered_df[['email', 'college', 'state']])  # Assuming 'email' column exists
            else:  # selected_state == "All"
                st.info(
                    "Select a specific state from the sidebar for more details, or 'Telangana' for college-specific analytics.")
                st.dataframe(filtered_df[['email','state']].head(20),
                             help="Showing first 20 rows of all students.")  # Assuming 'email'

        with tab3:
            st.subheader("Processed Student Data Inspector")
            st.dataframe(df_processed)

            if st.button("Export Full Processed Data"):
                csv = df_processed.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Processed Data as CSV",
                    data=csv,
                    file_name="student_data_processed_export.csv",
                    mime="text/csv"
                )

    else:
        st.info("👋 Welcome! Please upload a student data CSV file to begin analysis.")
        st.markdown("""
        **Expected CSV Data Format:**
        - A CSV file with at least two columns. One column must be named `college`. An `email` column (or similar student identifier) is recommended for data display.
        - **For Telangana colleges:** The `college` column should ideally follow the format `CODE - COLLEGE NAME` (e.g., `VJIT - VIDYAJYOTHI INSTITUTE OF TECHNOLOGY`). The presence of a hyphen `-` is key for identifying these.
        - **For other states/entries:** The `college` column should contain the state name (e.g., `Andhra Pradesh`, `Karnataka`), a known alias (e.g., `Overseas`), or it will be categorized as 'Unknown' if not recognized.

        The application will parse state information and, for Telangana, attempt to extract specific college names.
        """)


if __name__ == "__main__":
    main()