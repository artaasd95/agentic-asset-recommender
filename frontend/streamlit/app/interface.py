import streamlit as st
import requests
import uuid
import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"  # Replace with your FastAPI server URL

# Streamlit App Title
st.title("Financial Asset Recommender Chatbot")

# Sidebar for /perform_calculations endpoint
st.sidebar.title("Perform Calculations")

# Input fields for /perform_calculations
ticker = st.sidebar.text_input("Ticker Symbol", value="AAPL")
start_date = st.sidebar.text_input("Start Date (YYYY-MM-DD)", value="2022-01-01")
end_date = st.sidebar.text_input("End Date (YYYY-MM-DD)", value="2023-01-01")
store_raw = st.sidebar.checkbox("Store Raw Data", value=False)
store_features = st.sidebar.checkbox("Store Computed Features", value=False)

# Button to send request to /perform_calculations
if st.sidebar.button("Perform Calculations"):
    try:
        # Prepare the request payload
        payload = {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "store_raw": store_raw,
            "store_features": store_features,
        }

        # Send the request to the API
        response = requests.post(f"{API_BASE_URL}/perform_calculations", json=payload)

        # Display the response
        if response.status_code == 200:
            st.sidebar.success("Calculations performed successfully!")
            st.sidebar.json(response.json())
        else:
            st.sidebar.error(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.sidebar.error(f"An error occurred: {str(e)}")

# Main section for /v1/query endpoint
st.header("Chat with the Financial Asset Recommender")

# Input fields for /v1/query
user_id = st.text_input("User ID", value=str(uuid.uuid4()))
session_id = st.text_input("Session ID", value=str(uuid.uuid4()))
query = st.text_area("Enter your query", placeholder="Ask me anything about financial assets...")

# Button to send query to /v1/query
if st.button("Send Query"):
    if not query:
        st.error("Please enter a query.")
    else:
        try:
            # Prepare the request payload
            payload = {
                "query": query,
                "user_id": user_id,
                "session_id": session_id,
            }

            # Send the request to the API
            response = requests.post(f"{API_BASE_URL}/v1/query", json=payload)

            # Display the response
            if response.status_code == 200:
                st.success("Query processed successfully!")
                st.json(response.json())
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")