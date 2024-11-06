from dotenv import load_dotenv
import base64
import streamlit as st
import os
import io
from PIL import Image
import pdf2image
import google.generativeai as genai
from fpdf import FPDF
import matplotlib.pyplot as plt
import re

# Load environment variables
load_dotenv()

# Configure Google API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to get response from Gemini model
def get_gemini_response(input_text, pdf_content, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input_text, pdf_content[0], prompt])
    return response.text

# Function to convert PDF to image and return base64 encoded data
def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Function to create PDF report
def create_pdf_report(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(200, 10, txt=content, align='L')
    
    # Output PDF content to a byte array instead of a file
    return pdf.output(dest='S').encode('latin1')  # 'S' sends the PDF to a string and encode it to bytes

# Function to plot match percentage as a pie chart
def plot_match_percentage(match_percentage):
    labels = ['Match', 'Gap']
    sizes = [match_percentage, 100 - match_percentage]
    colors = ['#4CAF50', '#FF6F61']
    explode = (0.1, 0)
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
    ax1.axis('equal')
    st.pyplot(fig1)

# Function to extract percentage match from response using regex
def extract_percentage(response_text):
    # Look for a number followed by a percentage sign
    match = re.search(r"(\d+)%", response_text)
    if match:
        return int(match.group(1))  # Extract the matched number and convert to integer
    else:
        raise ValueError("No percentage found in the response.")

# Streamlit App
st.set_page_config(page_title="HireSense")
st.header("HireSense")
input_text = st.text_area("Job Description: ", key="input")
uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])

if uploaded_file is not None:
    st.write("PDF Uploaded Successfully")

# Button triggers
submit1 = st.button("Tell Me About the Resume")
submit2 = st.button("Skill Extraction and Recommendation")
submit3 = st.button("Percentage match")
submit4 = st.button("Evaluate Soft Skills")
download_report = st.button("Download Evaluation Report")

# Prompts for different functionalities
input_prompt1 = """
You are an experienced Technical Human Resource Manager. Review the provided resume against the job description. 
Share a professional evaluation on whether the candidate's profile aligns with the role, highlighting strengths and weaknesses.
"""

input_prompt2 = """
You are an ATS scanner. Extract the key skills and technologies from the job description and resume, and provide recommendations for the candidate to add or improve their resume.
"""

input_prompt3 = """
You are a skilled ATS scanner with knowledge of data science. Evaluate the resume against the job description, giving a percentage match, followed by missing keywords, and final thoughts.
"""

input_prompt4 = """
You are a human resources expert. Based on the job description, evaluate the candidate's resume for soft skills. Provide a score and comments.
"""

# Processing the user requests
if submit1:
    if uploaded_file is not None:
        pdf_content = input_pdf_setup(uploaded_file)
        response = get_gemini_response(input_text, pdf_content, input_prompt1)
        st.subheader("The Response is")
        st.write(response)
    else:
        st.write("Please upload the resume")

elif submit2:
    if uploaded_file is not None:
        pdf_content = input_pdf_setup(uploaded_file)
        response = get_gemini_response(input_text, pdf_content, input_prompt2)
        st.subheader("Skill Extraction and Recommendations")
        st.write(response)
    else:
        st.write("Please upload the resume")

elif submit3:
    if uploaded_file is not None:
        pdf_content = input_pdf_setup(uploaded_file)
        response = get_gemini_response(input_text, pdf_content, input_prompt3)
        st.subheader("Percentage Match")
        st.write(response)
        
        # Extract percentage from response text
        try:
            match_percentage = extract_percentage(response)  # Extract the percentage using regex
            plot_match_percentage(match_percentage)  # Plot the match percentage
        except ValueError as e:
            st.error(f"Error: {e}")
    else:
        st.write("Please upload the resume")

elif submit4:
    if uploaded_file is not None:
        pdf_content = input_pdf_setup(uploaded_file)
        response = get_gemini_response(input_text, pdf_content, input_prompt4)
        st.subheader("Soft Skills Evaluation")
        st.write(response)
    else:
        st.write("Please upload the resume")

# Option to download the evaluation report as a PDF
if download_report:
    if uploaded_file is not None:
        pdf_content = input_pdf_setup(uploaded_file)
        response = get_gemini_response(input_text, pdf_content, input_prompt1)  # Default report for now
        pdf_data = create_pdf_report(response)  # Get the PDF as bytes
        st.download_button(label="Download PDF", data=pdf_data, file_name="evaluation_report.pdf", mime="application/pdf")
    else:
        st.write("Please upload the resume")
