import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
import pandas as pd

# -------------------------------
# Google Sheets setup
# -------------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Use Streamlit Secrets instead of local file
creds_dict = json.loads(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open master spreadsheet
SHEET_NAME = "College Feedback Master"
spreadsheet = client.open(SHEET_NAME)

# -------------------------------
# Role selection
# -------------------------------
role = st.sidebar.selectbox("Select Role", ["Student", "Admin"])

# Optional password for Admin
if role == "Admin":
    admin_pass = st.sidebar.text_input("Enter Admin Password", type="password")
    if admin_pass != "user123":
        st.warning("Access denied.")
        st.stop()

# -------------------------------
# Student Form
# -------------------------------
if role == "Student":
    st.title("📋 Student Feedback Form")

    # Ensure worksheet exists
    event_name = st.text_input("📌 Event Name (e.g., TechFest_2025)")
    if event_name:
        try:
            sheet = spreadsheet.worksheet(event_name)
        except:
            sheet = spreadsheet.add_worksheet(title=event_name, rows="1000", cols="20")
            sheet.append_row([
                "Name", "Email", "Course", "Section",
                "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Suggestions"
            ])

    # Multi-step form
    if "form_stage" not in st.session_state:
        st.session_state.form_stage = "info"

    course_options = [
        "COMPUTER SCIENCE ENGINEERING(CSE)", "COMPUTER SCIENCE AND BUSINESS SYSTEMS(CS-BS)",
        "ELECTRICAL AND ELECTRONICS ENGINEERING(EEE)", "ELECTRONICS AND COMMUNICATION ENGINEERING(ECE)",
        "APPLIED ELECTRONICS AND INSTRUMENTATION ENGINEERING(AE)", "MECHANICAL ENGINEERING(ME)",
        "CIVIL ENGINEERING(CE)", "INFORMATION TECHNOLOGY(IT)", "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE(AD)"
    ]
    section_options = ["ALPHA", "BETA", "GAMMA", "DELTA", "NIL"]
    year_options = ["1st year", "2nd year", "3rd year", "4th year"]

    if st.session_state.form_stage == "info":
        with st.form("student_info"):
            name = st.text_input("Your Name")
            email = st.text_input("Email ID")
            course = st.selectbox("Course Taken", course_options)
            year = st.selectbox("Year", year_options)
            section = st.selectbox("Section", section_options)
            next_btn = st.form_submit_button("Next")

        if next_btn and name and email and course and section:
            st.session_state.name = name
            st.session_state.email = email
            st.session_state.course = course
            st.session_state.section = section
            st.session_state.form_stage = "feedback"
            st.rerun()

    elif st.session_state.form_stage == "feedback":
        with st.form("feedback_form"):
            q1 = st.radio("How did you find the overall organization of the event?", ["Excellent", "Good", "Average", "Poor"])
            q2 = st.radio("Was the program relevant?", ["Yes", "Somewhat", "No"])
            q3 = st.radio("Were the speakers/presenters engaging?", ["Yes, very engaging", "Somewhat engaging", "Not engaging"])
            q4 = st.radio("How was the event duration?", ["Too Long", "Just Right", "Too Short"])
            q5 = st.radio("How would you rate the event's organisation (scheduling, coordination, communication)", ["Excellent", "Good", "Fair", "Poor"])
            q6 = st.radio("How effective were the speakers?", ["Very effective", "Effective", "Neutral", "Ineffective"])
            q7 = st.radio("How likely are you to attend such similar events in the future?", ["Very likely", "Likely", "Not likely", "Never"])
            q8 = st.radio("How satisfied were you with the venue/facilities?", ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied"])
            q9 = st.radio("Would you recommend this program to others?", ["Definitely", "Maybe", "No"])
            suggestion = st.text_area("Any suggestions you'd like to share?")
            submit_btn = st.form_submit_button("Submit")

        if submit_btn:
            row = [
                st.session_state.name,
                st.session_state.email,
                st.session_state.course,
                st.session_state.section,
                q1, q2, q3, q4, q5, q6, q7, q8, q9, suggestion
            ]
            sheet.append_row(row)
            st.success("✅ Thank you for your feedback!")
            # Reset
            st.session_state.form_stage = "info"
            st.session_state.pop("name", None)
            st.session_state.pop("email", None)
            st.session_state.pop("course", None)
            st.session_state.pop("section", None)

# -------------------------------
# Admin Dashboard
# -------------------------------
if role == "Admin":
    st.title("📊 Feedback Summary Dashboard")

    event_name = st.text_input("📌 Enter Event Name to View Responses")

    if event_name:
        try:
            sheet = spreadsheet.worksheet(event_name)
            data = sheet.get_all_records()
            df = pd.DataFrame(data)

            if not df.empty:
                mcq_questions = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9"]
                for q in mcq_questions:
                    if q in df.columns:
                        st.subheader(f"{q} Responses")
                        response_counts = df[q].value_counts()
                        if not response_counts.empty:
                            fig, ax = plt.subplots()
                            ax.pie(response_counts.values, labels=response_counts.index, autopct='%1.1f%%', startangle=90)
                            ax.axis('equal')
                            st.pyplot(fig)
                        else:
                            st.info(f"No responses yet for {q}")

                if "Suggestions" in df.columns:
                    st.subheader("💬 Student Suggestions")
                    suggestions = df["Suggestions"].dropna()
                    if not suggestions.empty:
                        for i, suggestion in enumerate(suggestions, 1):
                            st.write(f"{i}. {suggestion}")
                    else:
                        st.info("No suggestions submitted yet.")
            else:
                st.info("No responses yet for this event.")
        except:
            st.error("⚠️ Event not found. Please check the event name.")
