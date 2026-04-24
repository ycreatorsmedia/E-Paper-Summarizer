import streamlit as st
import google.generativeai as genai
import requests

# --- Configuration ---
# Safely pull keys from Streamlit's secret vault!
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
NEWSDATA_API_KEY = st.secrets["NEWSDATA_API_KEY"]

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash') 

# --- Streamlit UI ---
st.set_page_config(page_title="AP Political Intelligence", page_icon="📡")

st.title("📡 Andhra Pradesh Live Political Intelligence Hub")
st.markdown("This tool delivers a unified, real-time view of all political activity and media coverage in one place.")

# Dropdown for topic selection
search_query = st.selectbox(
    "Instantly track and analyze the latest narrative, sentiment, and coverage trends:", 
    ["YSRCP", "TDP", "JSP", "BJP", "Overall"]
)

if st.button("Scan the Web & Summarize", type="primary"):
    with st.spinner("Scanning global news databases for the latest updates..."):
        
        # SMART SEARCH LOGIC: If they pick 'Overall', search for AP Politics generally.
        api_query = "Andhra Pradesh politics" if search_query == "Overall" else search_query
        
        url = f"https://newsdata.io/api/1/latest?apikey={NEWSDATA_API_KEY}&q={api_query}&country=in&language=en,te"
        
        try:
            response = requests.get(url).json()
            
            if response.get("status") == "success":
                articles = response.get("results", [])
                
                if len(articles) == 0:
                    st.warning(f"No recent news found for '{search_query}'. Try a different keyword.")
                else:
                    st.success(f"Found {len(articles)} recent articles! Sending to Gemini for analysis...")
                    
                    compiled_news = ""
                    for article in articles:
                        compiled_news += f"- Source: {article.get('source_id')}\n"
                        compiled_news += f"  Title: {article.get('title')}\n"
                        compiled_news += f"  Description: {article.get('description')}\n"
                        compiled_news += f"  Published: {article.get('pubDate')}\n\n"
                    
                    prompt = f"""
                    You are an expert political analyst. Read the following news snippets regarding '{search_query}'.
                    
                    Please provide a highly structured and professional summary of the major events, statements, and criticisms found in these snippets.
                    Use clear headings and bullet points.
                    
                    Here is the raw news data from the API:
                    {compiled_news}
                    """
                    
                    gemini_response = model.generate_content(prompt)
                    
                    st.divider()
                    st.subheader(f"📊 Live Summary for: {search_query}")
                    st.markdown(gemini_response.text)
                    
                    with st.expander("Click to see the raw API data we fed to Gemini"):
                        st.text(compiled_news)
                        
            else:
                error_msg = response.get('message', 'Unknown API Error')
                st.error(f"NewsData API Error: {error_msg}")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
