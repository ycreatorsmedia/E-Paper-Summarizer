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
    html_content = markdown.markdown(md_text)
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
    pdf_buffer = BytesIO()
    pisa.CreatePDF(BytesIO(styled_html.encode("utf-8")), dest=pdf_buffer)
    return pdf_buffer.getvalue()

# --- Streamlit UI ---
st.set_page_config(page_title="E-Paper Summarizer", page_icon="📰", layout="wide")

st.title("📰 Daily E-Paper Political Summarizer")
st.markdown("Upload multiple PDFs or Images of news clippings to generate a master summary.")

# Sidebar for options
st.sidebar.header("Settings")
party_focus = st.sidebar.selectbox("Primary Focus Party:", ["TDP", "YSRCP", "Janasena", "General"])

# NEW: File Uploader now accepts multiple files AND images!
uploaded_files = st.file_uploader(
    "Upload Newspaper PDFs or Images (Select multiple!)", 
    type=["pdf", "png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

# Check if the list of uploaded files is not empty
if uploaded_files:
    st.info(f"Uploading {len(uploaded_files)} file(s) directly to Gemini's vision engine...")
    
    with st.spinner('Analyzing political content across all files... This may take a moment.'):
        
        gemini_uploaded_files = []
        temp_file_paths = []
        
        try:
            # 1. Loop through ALL uploaded files to save and upload them to Gemini
            for file in uploaded_files:
                temp_path = f"temp_{file.name}"
                with open(temp_path, "wb") as f:
                    f.write(file.getbuffer())
                
                gemini_file = genai.upload_file(temp_path)
                gemini_uploaded_files.append(gemini_file)
                temp_file_paths.append(temp_path)
            
            # 2. Create the instructions
            prompt = f"""
            You are an expert political analyst. Read all the attached newspaper files/images.
            Please summarize the combined content focusing on the {party_focus} party. 
            
            Structure your response EXACTLY like this:
            ### 1. Development & Investments
            (Summarize any news related to projects, governance, and welfare)
            
            ### 2. Leaders on Media (Press Meets & Statements)
            (List which leaders spoke and the gist of their statements)
            
            ### 3. Attacking Points on Opposition
            (Summarize the main political attacks, criticism, and allegations made)
            """
            
            # 3. Generate the summary using ALL files + the prompt
            request_content = gemini_uploaded_files + [prompt]
            response = model.generate_content(request_content)
            summary = response.text
            
            # Display Results on Screen
            st.divider()
            st.subheader(f"📊 Master Summary Report: Focus on {party_focus}")
            st.markdown(summary)
            
            # 4. Generate Download Buttons
            st.divider()
            st.write("### Download Options")
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📄 Download Summary as TXT",
                    data=summary,
                    file_name=f"{party_focus}_master_summary.txt",
                    mime="text/plain"
                )
            
            with col2:
                pdf_bytes = create_pdf(summary)
                st.download_button(
                    label="🗄️ Download Summary as PDF",
                    data=pdf_bytes,
                    file_name=f"{party_focus}_master_summary.pdf",
                    mime="application/pdf"
                )
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
            
        finally:
            # 5. Clean up ALL temporary files (runs even if there's an error)
            for temp_path in temp_file_paths:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            for g_file in gemini_uploaded_files:
                genai.delete_file(g_file.name)
