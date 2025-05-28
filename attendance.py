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
    pd.DataFrame(columns=["Date", "Student_Name", "College", "Mobile_Number", "Email", "Present"]).to_csv(DATA_FILE, index=False)

# Function to load data
def load_data():
    return pd.read_csv(DATA_FILE)

# Function to save data
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Generate QR code for the app URL
def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    # Convert PIL image to bytes for Streamlit display
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    return img_byte_arr.getvalue()

# Streamlit app
st.title("Swecha Office Attendance Tracker")

# Sidebar for navigation
st.sidebar.header("Navigation")
option = st.sidebar.selectbox("Choose an option", ["Scan QR to Log Attendance", "View Analytics"])

if option == "Scan QR to Log Attendance":
    st.header("Log Attendance")
    
    # Display QR code
    app_url = st.text_input("Enter App URL (e.g., http://localhost:8501)", value="http://localhost:8501", key="app_url")
    if app_url:
        qr_image = generate_qr_code(app_url)
        st.image(qr_image, caption="Scan this QR Code to Log Attendance", width=300)
        st.write("Students: Scan the QR code with your smartphone to open the attendance form.")
    
    # Form for attendance input
    with st.form(key="attendance_form"):
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
        
        # College-wise breakdown
        college_counts = df_date["College"].value_counts().reset_index()
        college_counts.columns = ["College", "Count"]
        
        if not college_counts.empty:
            st.write("**College-Wise Attendance:**")
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
            
            # Daily attendance trend (for all dates)
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
            st.write(f"No attendance data for {selected_date_str}.")
    else:
        st.write("No attendance data available.")

# Instructions
st.sidebar.write("Instructions")
st.sidebar.write("- Select 'Scan QR to Log Attendance' to display the QR code and log attendance.")
st.sidebar.write("- Students scan the QR code and enter their name, college, mobile number, and email.")
st.sidebar.write("- Use 'View Analytics' to see daily and college-wise attendance.")
st.sidebar.write("- Data is stored in 'attendance.csv'.")
