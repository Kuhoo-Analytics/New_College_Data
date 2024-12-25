from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import re
import os  # For accessing environment variables

# Configure the Gemini API
genai.configure(api_key="AIzaSyD0OnFiXExV4ef8v8BqF_Y6agvdphgmDHM")

# Initialize the Flask app
app = Flask(__name__)

# Function to extract and clean numeric placement percentage
def extract_numeric_value(text):
    # Pattern to match numeric ranges or standalone numbers
    range_pattern = r'(\d+)\s*[-to]+\s*(\d+)'  # Matches ranges like "40-45" or "50 to 65"
    single_number_pattern = r'\b(\d+)(?:%?)\b'  # Matches standalone numbers like "86" or "98%"

    # Check for numeric range
    match = re.search(range_pattern, text)
    if match:
        low, high = int(match.group(1)), int(match.group(2))
        if abs(high - low) <= 50:  # If the range difference is <=50, use the higher value
            return high
        else:  # If the range difference is >50, return the average
            return (low + high) // 2

    # Check for standalone numbers
    match = re.search(single_number_pattern, text)
    if match:
        return int(match.group(1))

    # Default case: No numeric value found
    return None

# Function to determine preferred product based on placement percentage
def determine_preferred_product(placement_percentage):
    if placement_percentage >= 90:  # 90 and above
        return "Kuhoo Scholar"
    elif 70 <= placement_percentage < 90:  # Between 70 (inclusive) and 90 (exclusive)
        return "Kuhoo Talent"
    else:  # Below 70
        return "Kuhoo Professional"

# Define the function to fetch and process placement info
def get_placement_info(college_name, college_city, course_type):
    # Prompt for the Gemini API
    prompt = f"What is the placement rate, i.e., out of total students admitted those that got placed (from any relevant source, for the most recent year):\
for {course_type} at {college_name}, {college_city}.\ 
In case no data can be retrieved, then return 'No relevant data is present' but only if no data point is available at all.\ 
If any or multiple varying data points are available, then kindly provide the best estimate possible.\ 
The response should be only a specific number."
    
    # Call the Gemini API
    response = genai.GenerativeModel('models/gemini-1.5-flash').generate_content(prompt, tools='google_search_retrieval')
    result_text = response.text

    # Extract numeric value for placement percentage
    placement_percentage = extract_numeric_value(result_text)

    # Determine the preferred product
    if placement_percentage is not None:
        preferred_product = determine_preferred_product(placement_percentage)
        return f"Expected placement percentage: {placement_percentage}%, Preferred product: {preferred_product}"
    else:
        return "No valid placement percentage could be extracted from the response."

# Define a route for the home page
@app.route('/')
def home():
    return render_template('index.html')  # Serves an HTML page for input

# Define a route to process the API call
@app.route('/get_college_info', methods=['POST'])
def get_college_info():
    data = request.json

    # Get input fields
    college_name = data.get('college_name')
    college_city = data.get('college_city')
    course_type = data.get('course_type')

    # Validate input fields
    if not college_name or not college_city or not course_type:
        return jsonify({"details": "Please fill all fields to fetch result"}), 200

    try:
        # Get placement details and clean result
        details = get_placement_info(college_name, college_city, course_type)
        return jsonify({"details": details}), 200
    except Exception as e:
        return jsonify({"details": f"An error occurred: {str(e)}"}), 500

# Run the app with proper binding for Render
if __name__ == '__main__':
    # Bind to the environment-provided port or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
