from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

# Configure the Gemini API
genai.configure(api_key="AIzaSyD0OnFiXExV4ef8v8BqF_Y6agvdphgmDHM")

# Initialize the Flask app
app = Flask(__name__)

# Define the function to fetch college placement info
def get_placement_info(college_name):
    prompt = f"What are the following data points (from any relevant source, for the most recent year):\
1. MBA Placement Rate for {college_name}\
2. Median or Average package for MBA at {college_name}\
3. Heighest package for MBA at {college_name}\
The response should be with as minimum words as possible and only specific numbers."
    response = genai.GenerativeModel('models/gemini-1.5-flash').generate_content(prompt, tools='google_search_retrieval')
    return response.text

# Define a route for the home page
@app.route('/')
def home():
    return render_template('index.html')  # Serves an HTML page for input

# Define a route to process the API call
@app.route('/get_college_info', methods=['POST'])
def get_college_info():
    data = request.json
    college_name = data.get('college_name')
    if not college_name:
        return jsonify({"error": "College name is required"}), 400

    try:
        details = get_placement_info(college_name)
        return jsonify({"details": details})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the app locally
if __name__ == '__main__':
    app.run(debug=True)
