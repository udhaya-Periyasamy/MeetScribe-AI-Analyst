import os
import re
import json
import google.generativeai as genai
import base64
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from fpdf import FPDF

# --- Configuration ---
print("Starting MeetScribe server (v2 with PDF)...")
load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 1. Configure the Gemini API
try:
    api_key = os.environ["GEMINI_API_KEY"]
    if not api_key:
        raise KeyError
    genai.configure(api_key=api_key)
    print("Gemini API configured successfully.")
except KeyError:
    print("\n" + "="*50)
    print("FATAL ERROR: GEMINI_API_KEY not found.")
    print("Please create a file named '.env' in this directory and add:")
    print("GEMINI_API_KEY=your_api_key_here")
    print("="*50 + "\n")
    exit()

# 2. Master Prompt
MEETING_ANALYSIS_PROMPT = """
You are "MeetScribe," an expert meeting analyst. You will be given a video file of a meeting.
Your task is to analyze the entire video and audio and return a clean, valid JSON object.
Do not, under any circumstances, wrap the JSON in markdown (```json ... ```).
The JSON object must have exactly these three top-level keys:

1.  "summary": A concise, one-paragraph summary of the meeting's purpose, key discussions, and final outcomes.
2.  "action_items": A list of objects. Each object must have:
    - "task": (string) The specific action item.
    - "owner": (string) The person or group assigned. Default to "Unassigned" if not mentioned.
    - "deadline": (string) The due date. Default to "Not specified" if not mentioned.
3.  "sentiment": A brief, 2-3 sentence analysis of the team's overall sentiment (e.g., optimistic, concerned, collaborative), based on tone of voice and language.
"""

def clean_gemini_output(text_response):
    """Cleans the raw text output from Gemini to extract the JSON."""
    match = re.search(r'```json\s*(\{.*?\})\s*```', text_response, re.DOTALL | re.IGNORECASE)
    if match:
        print("Cleaning markdown from Gemini output.")
        return match.group(1)
    return text_response.strip()

# --- THIS IS THE JSON-TO-PDF FUNCTION (FIXED) ---
def create_pdf_report(data):
    """Generates a PDF report from the analysis data and returns it as a Base64 string."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- ✅ THE FIX IS HERE ---
    # We are REMOVING the code that tried to add the "DejaVu" font.
    # We will just use the default "Arial" font, which is always available.
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, "MeetScribe Analysis Report", 0, 1, 'C')
    pdf.ln(10)

    # --- Summary ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Summary", 0, 1)
    pdf.set_font("Arial", '', 12)
    # Encode the string to 'latin-1' with 'replace' for the PDF library
    summary_text = data.get('summary', 'No summary provided.').encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, summary_text)
    pdf.ln(5)

    # --- Sentiment ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Sentiment", 0, 1)
    pdf.set_font("Arial", '', 12)
    sentiment_text = data.get('sentiment', 'No sentiment analysis provided.').encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, sentiment_text)
    pdf.ln(5)

    # --- Action Items ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Action Items", 0, 1)
    pdf.set_font("Arial", '', 12)
    
    action_items = data.get('action_items', [])
    if not action_items:
        pdf.multi_cell(0, 5, "- No action items were identified.")
    else:
        for item in action_items:
            task = item.get('task', 'No task specified').encode('latin-1', 'replace').decode('latin-1')
            owner = item.get('owner', 'Unassigned').encode('latin-1', 'replace').decode('latin-1')
            deadline = item.get('deadline', 'N/A').encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, f"Task: {task}\nOwner: {owner} | Deadline: {deadline}\n")
            pdf.ln(2)
            
    # Get the PDF data as bytes
    pdf_bytes = pdf.output(dest='S') 
    
    # Encode the bytes to Base64
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    return pdf_base64

# --- Routes ---

@app.route('/')
def index():
    """Serves the main HTML page."""
    print("Serving index.html")
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_meeting():
    """Handles the video upload and analysis."""
    print("\nReceived new /analyze request.")
    if 'video' not in request.files:
        print("Error: No video file in request.")
        return jsonify({"error": "No video file provided"}), 400

    file = request.files['video']
    if file.filename == '':
        print("Error: No selected file.")
        return jsonify({"error": "No selected file"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    video_file_gemini = None

    try:
        # 1. Save File
        print(f"Saving temporary file: {filepath}")
        file.save(filepath)

        # 2. Upload to Gemini
        print(f"Uploading file to Gemini API: {filepath}...")
        video_file_gemini = genai.upload_file(path=filepath)
        
        # 3. Wait for Processing
        print(f"Waiting for file '{video_file_gemini.name}' to be processed...")
        while video_file_gemini.state.name == "PROCESSING":
            print("...")
            import time
            time.sleep(5)
            video_file_gemini = genai.get_file(video_file_gemini.name)

        if video_file_gemini.state.name == "FAILED":
            print(f"Error: File processing failed. {video_file_gemini.state}")
            raise Exception("File processing failed on the server.")
        
        print("File is now ACTIVE and ready for analysis.")

        # 4. Call the Gemini API
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        
        print("Sending prompt and video to Gemini 2.5 Flash...")
        response = model.generate_content(
            [MEETING_ANALYSIS_PROMPT, video_file_gemini],
            request_options={"timeout": 1000}
        )
        print("Received response from Gemini.")

        # 5. Process the JSON response
        cleaned_json_string = clean_gemini_output(response.text)
        analysis_data = json.loads(cleaned_json_string)
        
        # 6. --- PDF STEP ---
        print("Generating PDF report...")
        pdf_base64_string = create_pdf_report(analysis_data)
        print("PDF generated successfully.")

        # 7. Send the correct JSON structure
        return jsonify({
            "report_data": analysis_data,
            "pdf_data": pdf_base64_string
        })

    except Exception as e:
        print(f"\n--- An Error Occurred ---")
        print(f"Error: {e}")
        print(f"---------------------------\n")
        return jsonify({"error": str(e)}), 500
    
    finally:
        # 8. Clean up
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted local file: {filepath}")
        if video_file_gemini:
            genai.delete_file(video_file_gemini.name)
            print(f"Deleted remote file: {video_file_gemini.name}")

if __name__ == '__main__':
    print("MeetScribe server (v2 with PDF) starting on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)