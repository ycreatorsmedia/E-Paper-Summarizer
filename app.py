import streamlit as st
import google.generativeai as genai
import os
import markdown
from xhtml2pdf import pisa
from io import BytesIO

# --- Configuration ---
# This safely pulls the key from Streamlit's secret vault!
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') 

# --- Helper Function for PDF ---
def create_pdf(md_text):
    # Convert AI text formatting (Markdown) to HTML
    html_content = markdown.markdown(md_text)
    
    # Add some professional styling for the PDF
    styled_html = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Helvetica, Arial, sans-serif; line-height: 1.6; color: #2c3e50; }}
        h1, h2, h3 {{ color: #2980b9; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }}
        strong {{ color: #34495e; }}
    </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert the styled HTML into a PDF file
    pdf_buffer = BytesIO()
    pisa.CreatePDF(BytesIO(styled_html.encode("utf-8")), dest=pdf_buffer)
    return pdf_buffer.getvalue()

# --- Streamlit UI ---
st.set_page_config(page_title="E-Paper Summarizer", page_icon="📰", layout="wide")

st.title("📰 Daily E-Paper Political Summarizer")
st.markdown("Upload a PDF of a daily e-paper to get a structured political summary.")

# Sidebar for options
st.sidebar.header("Settings")
party_focus = st.sidebar.selectbox("Primary Focus Party:", ["TDP", "YSRCP", "Janasena", "General"])

# File Uploader
uploaded_file = st.file_uploader("Upload Newspaper PDF", type="pdf")

if uploaded_file is not None:
    st.info("Uploading PDF directly to Gemini's vision engine...")
    
    with st.spinner('Analyzing political content... This takes a moment for full PDFs.'):
        try:
            # 1. Save the file temporarily
            temp_pdf_path = "temp_newspaper.pdf"
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 2. Upload the file to Gemini
            gemini_file = genai.upload_file(temp_pdf_path)
            
            # 3. Create the instructions
            prompt = f"""
            You are an expert political analyst. Read the attached newspaper PDF.
            Please summarize the content focusing on the {party_focus} party. 
            
            Structure your response EXACTLY like this:
            ### 1. Development & Investments
            (Summarize any news related to projects, governance, and welfare)
            
            ### 2. Leaders on Media (Press Meets & Statements)
            (List which leaders spoke and the gist of their statements)
            
            ### 3. Attacking Points on Opposition
            (Summarize the main political attacks, criticism, and allegations made)
            """
            
            # 4. Generate the summary using the PDF
            response = model.generate_content([gemini_file, prompt])
            summary = response.text
            
            # Display Results on Screen
            st.divider()
            st.subheader(f"📊 Summary Report: Focus on {party_focus}")
            st.markdown(summary)
            
            # 5. Generate Download Buttons
            st.divider()
            st.write("### Download Options")
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📄 Download Summary as TXT",
                    data=summary,
                    file_name=f"{party_focus}_daily_summary.txt",
                    mime="text/plain"
                )
            
            with col2:
                pdf_bytes = create_pdf(summary)
                st.download_button(
                    label="🗄️ Download Summary as PDF",
                    data=pdf_bytes,
                    file_name=f"{party_focus}_daily_summary.pdf",
                    mime="application/pdf"
                )
            
            # 6. Clean up the temporary files
            os.remove(temp_pdf_path)
            genai.delete_file(gemini_file.name)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")