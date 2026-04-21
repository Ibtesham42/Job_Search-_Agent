import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="Job Extraction System", page_icon="🔍", layout="wide")

st.title("🔍 Job Extraction System")
st.markdown("Extract job listings from URLs automatically using AI")

with st.sidebar:
    st.header("⚙️ Configuration")
    api_url = st.text_input("API URL", value="http://localhost:8000")
    
    st.header("ℹ️ About")
    st.info("""
    **How it works:**
    1. Enter job board URLs
    2. System crawls and parses content
    3. AI extracts job details
    4. Results saved to CSV/JSON
    
    **Supported sources:**
    - Job boards (Indeed, LinkedIn, Naukri, Monster)
    - Company career pages
    - PDF job descriptions
    """)
    
    st.header("📝 Quick Examples")
    st.code("""
https://www.naukri.com/python-jobs
https://www.linkedin.com/jobs/search/?keywords=software+engineer
https://www.monsterindia.com/srp/results?q=developer
    """)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📎 URLs to Extract")
    
    urls_text = st.text_area(
        "Enter one URL per line",
        height=200,
        placeholder="https://example.com/jobs\nhttps://company.com/careers.pdf",
        help="Paste job board URLs or company career pages"
    )
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        extract_btn = st.button("🚀 Extract Jobs", type="primary", use_container_width=True)
    
    with col_btn2:
        if st.button("🧹 Clear All", use_container_width=True):
            st.session_state['extracted_jobs'] = None
            st.rerun()
    
    with col_btn3:
        if st.button("📋 Sample URL", use_container_width=True):
            st.session_state['sample_url'] = "https://www.naukri.com/software-engineer-jobs"
            st.rerun()

with col2:
    st.subheader("📊 Status")
    status_placeholder = st.empty()

# Initialize session state for storing jobs
if 'extracted_jobs' not in st.session_state:
    st.session_state['extracted_jobs'] = None
if 'extraction_time' not in st.session_state:
    st.session_state['extraction_time'] = None

# Handle sample URL
if 'sample_url' in st.session_state:
    current_text = urls_text
    if not current_text:
        urls_text = st.session_state['sample_url']
    del st.session_state['sample_url']
    st.rerun()

if extract_btn:
    url_list = [u.strip() for u in urls_text.split("\n") if u.strip()]
    
    if not url_list:
        st.error("❌ Please enter at least one URL")
    else:
        with st.spinner(f"🔄 Processing {len(url_list)} URL(s)... This may take a moment"):
            try:
                response = requests.post(
                    f"{api_url}/extract-jobs/",
                    json={"urls": url_list},
                    timeout=180
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Store in session state
                    st.session_state['extracted_jobs'] = data['jobs']
                    st.session_state['extraction_time'] = datetime.now()
                    
                    status_placeholder.success(f"✅ Found {data['total_jobs']} jobs")
                    
                    # Show success message
                    st.toast(f"Successfully extracted {data['total_jobs']} jobs!", icon="✅")
                    
                else:
                    st.error(f"❌ API Error {response.status_code}: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Make sure FastAPI is running:\n\n`cd backend && python main.py`")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# Display extracted jobs if available
if st.session_state['extracted_jobs'] and len(st.session_state['extracted_jobs']) > 0:
    jobs = st.session_state['extracted_jobs']
    
    st.markdown("---")
    st.subheader(f"📋 Extracted Jobs ({len(jobs)})")
    
    # Display jobs in expandable cards
    for idx, job in enumerate(jobs, 1):
        title = job.get("job_title", "Unknown Position")
        company = job.get("company", "Unknown Company")
        
        with st.expander(f"**{idx}. {title}** at *{company}*", expanded=(idx == 1)):
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.markdown("**🏢 Company**")
                st.write(job.get('company', 'N/A'))
                
                st.markdown("**📍 Location**")
                st.write(job.get('location', 'N/A'))
            
            with col_b:
                st.markdown("**📅 Posted Date**")
                st.write(job.get('posted_date', 'N/A'))
                
                st.markdown("**⏰ Apply By**")
                st.write(job.get('apply_by', 'N/A'))
            
            with col_c:
                st.markdown("**🔗 Source**")
                st.write(job.get('source', 'N/A'))
                
                if job.get('apply_link'):
                    st.markdown("**🔗 Apply Link**")
                    st.markdown(f"[Click to Apply]({job['apply_link']})")
            
            if job.get('description'):
                st.markdown("**📝 Description**")
                desc = job['description']
                if len(desc) > 300:
                    desc = desc[:300] + "..."
                st.info(desc)
    
    # Download section
    st.markdown("---")
    st.subheader("💾 Download Results")
    
    col_d1, col_d2, col_d3 = st.columns(3)
    
    with col_d1:
        try:
            df = pd.DataFrame(jobs)
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"CSV error: {e}")
    
    with col_d2:
        try:
            json_str = json.dumps(jobs, indent=2, default=str)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"JSON error: {e}")
    
    with col_d3:
        if st.button("🗑️ Clear Results", use_container_width=True):
            st.session_state['extracted_jobs'] = None
            st.rerun()

elif extract_btn and st.session_state['extracted_jobs'] is not None:
    st.warning("⚠️ No jobs found in the extracted content. Try different URLs or check if the website requires login.")

# Show recent extractions from CSV
st.markdown("---")
st.subheader("📚 Recent Extractions")

try:
    if os.path.exists("data/jobs.csv"):
        df_existing = pd.read_csv("data/jobs.csv")
        if len(df_existing) > 0:
            st.dataframe(df_existing.tail(10), use_container_width=True)
        else:
            st.info("No jobs extracted yet. Run extraction to see results here.")
    else:
        st.info("No data file found. Run extraction first.")
except Exception as e:
    st.info("No data file found. Run extraction first.")