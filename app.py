import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os

# Initialize session state for warranty data
if 'warranty_data' not in st.session_state:
    st.session_state.warranty_data = pd.DataFrame({
        'Warranty ID': [],
        'Project ID': [],
        'Item': [],
        'Category': [],
        'Start Date': [],
        'Expiration Date': [],
        'Terms': [],
        'Status': []
    })

if 'requests' not in st.session_state:
    st.session_state.requests = pd.DataFrame({
        'Request ID': [],
        'Warranty ID': [],
        'Client Name': [],
        'Issue': [],
        'Date Submitted': [],
        'Status': []
    })

# Scheduler for reminders
scheduler = BackgroundScheduler()
scheduler.start()

def check_warranty_expirations():
    today = datetime.now().date()
    warranties = st.session_state.warranty_data
    expiring_soon = warranties[warranties['Expiration Date'].apply(lambda x: (x - today).days <= 30)]
    if not expiring_soon.empty:
        st.session_state['notifications'] = expiring_soon[['Warranty ID', 'Item', 'Expiration Date']].to_dict('records')
    else:
        st.session_state['notifications'] = []

if 'notifications' not in st.session_state:
    st.session_state['notifications'] = []
scheduler.add_job(check_warranty_expirations, 'interval', days=1)

# Streamlit App
st.title("Construction Warranty Management Tool")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Warranty Database", "Client Portal", "Reports"])

# Dashboard
if page == "Dashboard":
    st.header("Warranty Management Dashboard")
    
    # Display notifications
    if st.session_state['notifications']:
        st.subheader("Expiring Warranties")
        for notif in st.session_state['notifications']:
            st.warning(f"Warranty {notif['Warranty ID']} for {notif['Item']} expires on {notif['Expiration Date']}.")
    
    # Warranty status visualization
    warranty_counts = st.session_state.warranty_data['Status'].value_counts().reset_index()
    warranty_counts.columns = ['Status', 'Count']
    fig = px.pie(warranty_counts, names='Status', values='Count', title="Warranty Status Distribution")
    st.plotly_chart(fig)

    # Recent warranty requests
    st.subheader("Recent Warranty Requests")
    if not st.session_state.requests.empty:
        st.dataframe(st.session_state.requests.tail(5))
    else:
        st.write("No recent requests.")

# Warranty Database
elif page == "Warranty Database":
    st.header("Warranty Database")
    
    # Add new warranty
    with st.form("add_warranty_form"):
        st.subheader("Add New Warranty")
        warranty_id = st.text_input("Warranty ID")
        project_id = st.text_input("Project ID")
        item = st.text_input("Item")
        category = st.selectbox("Category", ["Materials", "Equipment", "Workmanship"])
        start_date = st.date_input("Start Date")
        duration = st.number_input("Warranty Duration (days)", min_value=1, step=1)
        terms = st.text_area("Terms")
        submitted = st.form_submit_button("Add Warranty")
        
        if submitted:
            expiration_date = start_date + timedelta(days=duration)
            new_warranty = pd.DataFrame({
                'Warranty ID': [warranty_id],
                'Project ID': [project_id],
                'Item': [item],
                'Category': [category],
                'Start Date': [start_date],
                'Expiration Date': [expiration_date],
                'Terms': [terms],
                'Status': ['Active' if expiration_date >= datetime.now().date() else 'Expired']
            })
            st.session_state.warranty_data = pd.concat([st.session_state.warranty_data, new_warranty], ignore_index=True)
            st.success("Warranty added successfully!")
    
    # Display and edit warranties
    st.subheader("Existing Warranties")
    st.dataframe(st.session_state.warranty_data)
    
    # Delete warranty
    warranty_to_delete = st.text_input("Enter Warranty ID to Delete")
    if st.button("Delete Warranty"):
        st.session_state.warranty_data = st.session_state.warranty_data[st.session_state.warranty_data['Warranty ID'] != warranty_to_delete]
        st.success("Warranty deleted!")

# Client Portal
elif page == "Client Portal":
    st.header("Client Warranty Request Portal")
    
    with st.form("warranty_request_form"):
        st.subheader("Submit a Warranty Request")
        request_id = f"REQ{len(st.session_state.requests) + 1:04d}"
        warranty_id = st.text_input("Warranty ID")
        client_name = st.text_input("Client Name")
        issue = st.text_area("Issue Description")
        submitted = st.form_submit_button("Submit Request")
        
        if submitted:
            new_request = pd.DataFrame({
                'Request ID': [request_id],
                'Warranty ID': [warranty_id],
                'Client Name': [client_name],
                'Issue': [issue],
                'Date Submitted': [datetime.now().date()],
                'Status': ['Pending']
            })
            st.session_state.requests = pd.concat([st.session_state.requests, new_request], ignore_index=True)
            st.success("Request submitted successfully!")
    
    # Display submitted requests
    st.subheader("Your Submitted Requests")
    if not st.session_state.requests.empty:
        st.dataframe(st.session_state.requests)
    else:
        st.write("No requests submitted yet.")

# Reports
elif page == "Reports":
    st.header("Warranty Reports")
    
    # Filter warranties
    status_filter = st.multiselect("Filter by Status", options=['Active', 'Expired'], default=['Active', 'Expired'])
    category_filter = st.multiselect("Filter by Category", options=['Materials', 'Equipment', 'Workmanship'], default=['Materials', 'Equipment', 'Workmanship'])
    
    filtered_data = st.session_state.warranty_data[
        (st.session_state.warranty_data['Status'].isin(status_filter)) &
        (st.session_state.warranty_data['Category'].isin(category_filter))
    ]
    
    st.dataframe(filtered_data)
    
    # Export report
    if not filtered_data.empty:
        csv = filtered_data.to_csv(index=False)
        st.download_button(
            label="Download Report as CSV",
            data=csv,
            file_name="warranty_report.csv",
            mime="text/csv"
        )
    else:
        st.write("No data to export.")

# Save data to disk (optional for persistence)
if not st.session_state.warranty_data.empty:
    st.session_state.warranty_data.to_csv("warranty_data.csv", index=False)
if not st.session_state.requests.empty:
    st.session_state.requests.to_csv("requests_data.csv", index=False)
