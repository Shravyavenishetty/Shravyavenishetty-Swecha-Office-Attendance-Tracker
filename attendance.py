import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import qrcode
from PIL import Image
import io

# File to store attendance data
DATA_FILE = "attendance.csv"

# Initialize CSV file with headers if it doesn't exist
if not os.path.exists(DATA_FILE):
    headers = ["Date", "Student_Name", "College", "Mobile_Number", "Email", "Present"]
    pd.DataFrame(columns=headers).to_csv(DATA_FILE, index=False)

# Function to load data
def load_data():
    try:
        return pd.read_csv(DATA_FILE)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=["Date", "Student_Name", "College", "Mobile_Number", "Email", "Present"])

# Function to save data
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Generate QR code for the app URL
def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    return img_byte_arr.getvalue()

# Check query parameters to determine mode
query_params = st.query_params
mode = query_params.get("mode", [None])[0]

if mode == "attendance":
    # Hide title and show only the attendance form
    with st.form(key="attendance_form"):
        st.write("**Log Attendance**")
        student_name = st.text_input("Student Name")
        college = st.selectbox("College", ["College A", "College B", "College C"])  # Add more colleges as needed
        mobile_number = st.text_input("Mobile Number")
        email = st.text_input("Email Address")
        date = datetime.today().strftime("%Y-%m-%d")
        submit_button = st.form_submit_button(label="Submit Attendance")
        
        if submit_button:
            if student_name and mobile_number and email:
                # Basic email and mobile number validation
                if "@" not in email or not mobile_number.isdigit() or len(mobile_number) < 10:
                    st.error("Please enter a valid email address and mobile number (at least 10 digits).")
                else:
                    df = load_data()
                    # Check for duplicate entry (same email and date)
                    if not df[(df["Date"] == date) & (df["Email"] == email)].empty:
                        st.error("Attendance already recorded for this email today.")
                    else:
                        new_entry = pd.DataFrame({
                            "Date": [date],
                            "Student_Name": [student_name],
                            "College": [college],
                            "Mobile_Number": [mobile_number],
                            "Email": [email],
                            "Present": ["Y"]
                        })
                        df = pd.concat([df, new_entry], ignore_index=True)
                        save_data(df)
                        st.success(f"Attendance recorded for {student_name} from {college}!")
            else:
                st.error("Please fill in all fields.")
else:
    # Show full app with title and navigation for admins
    st.title("Swecha Office Attendance Tracker")
    
    st.sidebar.header("Navigation")
    option = st.sidebar.selectbox("Choose an option", ["Generate QR Code", "View Analytics"])

    if option == "Generate QR Code":
        st.header("Generate QR Code for Attendance")
        app_url = st.text_input("Enter Deployed App URL (e.g., https://your-app.streamlit.app)", value="https://your-app.streamlit.app")
        qr_url = f"{app_url}?mode=attendance"
        if app_url:
            qr_image = generate_qr_code(qr_url)
            st.image(qr_image, caption="Scan this QR Code to Log Attendance", width=300)
            st.write("Display this QR code at the office entrance or print it for students to scan.")

    elif option == "View Analytics":
        st.header("Attendance Analytics")
        
        # Load data
        df = load_data()
        
        if not df.empty:
            # Filter for present students
            df_present = df[df["Present"] == "Y"]
            
            # Date filter
            selected_date = st.date_input("Select Date for Analysis", value=datetime.today())
            selected_date_str = selected_date.strftime("%Y-%m-%d")
            df_date = df_present[df_present["Date"] == selected_date_str]
            
            # Total attendance for the selected date
            total_attendees = len(df_date)
            st.write(f"**Total Attendees on {selected_date_str}:** {total_attendees}")
            
            # Display all details
            st.write("**Detailed Attendance Records:**")
            if not df_date.empty:
                st.dataframe(df_date[["Date", "Student_Name", "College", "Mobile_Number", "Email", "Present"]])
            else:
                st.write(f"No attendance data for {selected_date_str}.")
            
            # College-wise breakdown
            college_counts = df_date["College"].value_counts().reset_index()
            college_counts.columns = ["College", "Count"]
            
            if not college_counts.empty:
                st.write("**College-Wise Attendance Summary:**")
                st.dataframe(college_counts)
                
                # Bar chart for college-wise attendance
                fig = px.bar(
                    college_counts,
                    x="College",
                    y="Count",
                    title=f"Attendance by College on {selected_date_str}",
                    color="College",
                    color_discrete_sequence=px.colors.qualitative.Plotly
                )
                fig.update_layout(
                    yaxis_title="Number of Students",
                    showlegend=True,
                    template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white"
                )
                st.plotly_chart(fig)
            
            # Daily attendance trend
            st.write("**Daily Attendance Trend:**")
            daily_counts = df_present.groupby("Date").size().reset_index(name="Count")
            fig_trend = px.line(
                daily_counts,
                x="Date",
                y="Count",
                title="Daily Attendance Trend",
                markers=True
            )
            fig_trend.update_layout(
                yaxis_title="Number of Students",
                template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white"
            )
            st.plotly_chart(fig_trend)
        else:
            st.write("No attendance data available.")

    # Instructions for admins
    st.sidebar.markdown("**Instructions**")
    st.sidebar.markdown("- Select 'Generate QR Code' to create a QR code for the attendance form (admin only).")
    st.sidebar.markdown("- Students scan the QR code to access the attendance form.")
    st.sidebar.markdown("- Use 'View Analytics' to see detailed attendance records and summaries.")
    st.sidebar.markdown(f"- Data is stored in '{DATA_FILE}'.")
