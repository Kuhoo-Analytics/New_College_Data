from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import re
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json

# Configure the Gemini API
genai.configure(api_key="AIzaSyD0OnFiXExV4ef8v8BqF_Y6agvdphgmDHM")

# Initialize the Flask app
app = Flask(__name__)

# Google Sheets API Setup
SHEET_ID = '12zBvHQEa25ifLOvmC0HWKhoID3qEMVe9Ul6Q5Krr1kA'  # Replace with your actual Sheet ID
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Use environment variable to handle the Google Service Account JSON file
SERVICE_ACCOUNT_CONTENT = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')  # JSON as an env variable

if SERVICE_ACCOUNT_CONTENT:
    # Load credentials from the environment variable
    service_account_info = json.loads(SERVICE_ACCOUNT_CONTENT)
    credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
else:
    raise FileNotFoundError("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable is not set!")

# Function to update the Google Sheet
def update_google_sheet(college_name, college_city, course_type, result):
    try:
        # Initialize Sheets API
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()
        
        # Data to append
        values = [[college_name, college_city, course_type, result]]
        body = {'values': values}
        
        # Append data to the Google Sheet (start from the 2nd row)
        sheet.values().append(
            spreadsheetId=SHEET_ID,
            range='Sheet1!A2:D',  # Start appending from row 2 (columns A to D)
            valueInputOption='RAW',
            body=body
        ).execute()
    except Exception as e:
        print(f"Failed to update Google Sheet: {e}")

# Function to extract and clean numeric placement percentage
def extract_numeric_value(text):
    range_pattern = r'(\d+)\s*[-to]+\s*(\d+)'
    single_number_pattern = r'\b(\d+)(?:%?)\b'
    match = re.search(range_pattern, text)
    if match:
        low, high = int(match.group(1)), int(match.group(2))
        return high if abs(high - low) <= 50 else (low + high) // 2
    match = re.search(single_number_pattern, text)
    return int(match.group(1)) if match else None

# Function to determine preferred product based on placement percentage
def determine_preferred_product(placement_percentage):
    if placement_percentage >= 90:
        return "Kuhoo Scholar"
    elif 70 <= placement_percentage < 90:
        return "Kuhoo Talent"
    else:
        return "Kuhoo Professional"

# Define the function to fetch and process placement info
def get_placement_info(college_name, college_city, course_type):
    prompt = f"""
    What is the placement rate, i.e., out of total students admitted those that got placed 
    (from any relevant source, for the most recent year): for {course_type} at {college_name}, {college_city}.
    In case no data can be retrieved, then return 'No relevant data is present' but only if no data point is available at all.
    If any or multiple varying data points are available, then kindly provide the best estimate possible.
    The response should be only a specific number.
    """
    response = genai.GenerativeModel('models/gemini-1.5-flash').generate_content(prompt, tools='google_search_retrieval')
    result_text = response.text
    placement_percentage = extract_numeric_value(result_text)
    if placement_percentage is not None:
        preferred_product = determine_preferred_product(placement_percentage)
        return f"Expected placement percentage: {placement_percentage}%, Preferred product: {preferred_product}"
    else:
        return "No valid placement percentage could be extracted from the response."

# Define a route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Define a route to process the API call
@app.route('/get_college_info', methods=['POST'])
def get_college_info():
    data = request.json
    college_name = data.get('college_name')
    college_city = data.get('college_city')
    course_type = data.get('course_type')
    if not college_name or not college_city or not course_type:
        return jsonify({"details": "Please fill all fields to fetch result"}), 200
    try:
        # Get placement details and clean result
        details = get_placement_info(college_name, college_city, course_type)
        
        # Update Google Sheet with the inputs and result
        update_google_sheet(college_name, college_city, course_type, details)
        
        return jsonify({"details": details}), 200
    except Exception as e:
        return jsonify({"details": f"An error occurred: {str(e)}"}), 500

# Run the app with proper binding for Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
