import streamlit as st
import json
import os
import re
from anthropic import Anthropic
from openai import OpenAI
from pypdf import PdfReader
from docx import Document
from fpdf import FPDF

# ==============================================================================
# 🧠 SHARP-STANDARDS PROTOCOL (Talent v1.0)
# ==============================================================================
# 1. DOMAIN: HR & Recruitment (Interview Analysis).
# 2. UI: Exact Match to Sales v3.3 (Neon/Black).
# 3. OUTPUT: Candidate Intelligence Report (PDF).
# ==============================================================================

APP_VERSION = "v1.0 (Talent)"
st.set_page_config(page_title="Sharp Talent", page_icon="🤝", layout="wide")

# --- CSS: SHARP PALETTE (Standardized) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    [data-testid="stSidebarNav"] {
        background-image: url("https://placehold.co/200x80/0e1117/00e5ff?text=SHARP+SUITE&font=roboto");
        background-repeat: no-repeat;
        background-position: 20px 20px;
        padding-top: 100px; 
    }
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #1c1c1c !important;
        color: #00e5ff !important;
        border: 1px solid #333 !important;
    }
    h1, h2, h3 {
        background: -webkit-linear-gradient(45deg, #00e5ff, #d500f9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
    }
    div[data-testid="stButton"] button {
        background: linear-gradient(45deg, #00e5ff, #00ffab) !important;
        color: #000000 !important;
        border: none !important;
        font-weight: 800 !important;
        text-transform: uppercase;
    }
    /* SUITE STANDARD CARDS */
    .insight-card {
        background-color: #161b22;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .insight-title { color: #fff; font-weight: 600; margin-bottom: 8px; font-size: 1.1rem; }
    .insight-body { color: #ccc; margin-bottom: 10px; line-height: 1.5; }
    .status-box {
        background-color: #1c1c1c;
        border-left: 3px solid #00e5ff;
        padding: 10px;
        font-family: monospace;
        color: #aaa;
        font-size: 0.9rem;
    }
    /* HEADER TILE */
    .lead-header-container {
        display: flex;
        justify-content: space-between;
        background-color: #161b22;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 25px;
        align-items: center;
    }
    .lead-item { text-align: center; flex: 1; border-right: 1px solid #333; }
    .lead-item:last-child { border-right: none; }
    .lead-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .lead-value { font-size: 1.2rem; color: #fff; font-weight: 700; }
    .lead-score { font-size: 1.5rem; color: #00e5ff; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE & SECRETS ---
if 'analysis_result' not in st.session_state: st.session_state.analysis_result = None
if 'transcript_text' not in st.session_state: st.session_state.transcript_text = ""
if 'processing_log' not in st.session_state: st.session_state.processing_log = "System Ready."
if 'total_cost' not in st.session_state: st.session_state.total_cost = 0.0

try:
    ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
except:
    st.error("❌ Missing AI API Keys.")
    st.stop()

def update_status(msg): st.session_state.processing_log = msg
def track_cost(amount): st.session_state.total_cost += amount

def extract_text(file):
    # (Same extraction logic as Sales App)
    try:
        if file.name.endswith('.pdf'): return "\n".join([page.extract_text() for page in PdfReader(file).pages])
        elif file.name.endswith('.txt'): return file.read().decode("utf-8")
        elif file.name.endswith('.docx'): return "\n".join([para.text for para in Document(file).paragraphs])
        return "Unsupported format."
    except Exception as e: return str(e)

def repair_json(text):
    text = text.strip()
    if "```json" in text: text = text.split("```json")[1].split("```")[0]
    try: return json.loads(text)
    except: return None

# --- INTELLIGENCE ENGINE (HR MODE) ---
def analyze_interview(transcript, candidate, role):
    system_prompt = f"""
    You are an elite Technical Recruiter & Behavioral Psychologist.
    Analyze this interview transcript for the role of {role}.

    **SCORING CRITERIA (STAR METHOD):**
    1. Technical Competence: Depth of specific domain knowledge.
    2. Communication: Clarity, structure, and conciseness.
    3. Cultural Fit: Alignment with high-performance teams.
    4. Problem Solving: Approach to ambiguity and blockers.

    **OUTPUT JSON STRUCTURE:**
    {{
      "meta": {{ "candidate": "{candidate}", "role": "{role}" }},
      "scores": {{ 
        "technical": 0, "communication": 0, "culture": 0, "problem_solving": 0, "total": 0 
      }},
      "key_insights": {{
        "strengths": ["..."],
        "red_flags": ["..."],
        "hiring_recommendation": "HIRE / NO HIRE / LEAN HIRE"
      }},
      "skill_analysis": [
         {{ "skill": "Skill Name", "level": "High/Med/Low", "evidence": "Quote" }}
      ]
    }}
    """
    try:
        msg = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620", max_tokens=2500, temperature=0.2, 
            system=system_prompt, messages=[{"role": "user", "content": transcript[:50000]}]
        )
        track_cost(0.02) 
        return repair_json(msg.content[0].text)
    except Exception as e: return {"error": str(e)}

# --- PDF GENERATOR (HR VERSION) ---
def safe_text(text):
    return text.encode('latin-1', 'ignore').decode('latin-1') if text else ""

class SharpTalentPDF(FPDF):
    def header(self):
        self.set_fill_color(14, 17, 23)
        self.rect(0, 0, 210, 35, 'F')
        self.set_font('Arial', 'B', 18)
        self.set_text_color(0, 229, 255)
        self.cell(0, 15, 'SHARP TALENT | CANDIDATE REPORT', 0, 1, 'C')
        self.ln(10)

def generate_hr_pdf(data):
    pdf = SharpTalentPDF()
    pdf.add_page()
    
    # Context Strip
    pdf.set_fill_color(230, 230, 230)
    pdf.rect(10, 45, 190, 20, 'F')
    pdf.set_y(48)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0,0,0)
    
    # Info Columns
    pdf.set_x(15)
    pdf.cell(60, 6, f"CANDIDATE: {safe_text(data['meta']['candidate'])}", 0, 0)
    pdf.cell(60, 6, f"ROLE: {safe_text(data['meta']['role'])}", 0, 0)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(50, 6, f"SCORE: {data['scores']['total']}/40", 0, 1)
    
    pdf.ln(15)
    
    # Recommendation
    rec = data['key_insights']['hiring_recommendation']
    color = (0, 200, 0) if "HIRE" in rec and "NO" not in rec else (200, 0, 0)
    pdf.set_text_color(*color)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"RECOMMENDATION: {rec}", 0, 1, 'C')
    pdf.ln(5)
    
    # Skills Table
    pdf.set_text_color(0,0,0)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "SKILL ANALYSIS", 0, 1)
    pdf.set_font('Arial', '', 10)
    
    for s in data['skill_analysis']:
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(10, pdf.get_y(), 190, 15, 'F')
        pdf.cell(40, 6, safe_text(s['skill']), 0, 0)
        pdf.cell(30, 6, safe_text(s['level']), 0, 0)
        pdf.multi_cell(0, 6, safe_text(f"Evidence: {s['evidence']}"))
        pdf.ln(2)

    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- MAIN UI ---
c_title, c_meta = st.columns([3, 1])
with c_title:
    st.title("🤝 Sharp Talent")
    st.caption("Interview & Candidate Intelligence")
with c_meta:
    st.markdown(f"<div style='text-align: right; color: #666;'>{APP_VERSION}</div>", unsafe_allow_html=True)
    st.metric("Session Cost", f"${st.session_state.total_cost:.4f}")
    st.markdown(f"<div class='status-box'><span style='color: #00e5ff;'>● ENGINE ACTIVE</span><br>{st.session_state.processing_log}</div>", unsafe_allow_html=True)

# INPUTS
st.markdown("### 👤 Candidate Context")
c1, c2, c3 = st.columns(3)
with c1: candidate_name = st.text_input("Candidate Name", "John Smith")
with c2: role_name = st.text_input("Role Applying For", "Senior Python Dev")
with c3: interviewer = st.text_input("Interviewer", "Hiring Manager")

uploaded_file = st.file_uploader("Upload Interview Transcript or Resume (PDF/TXT)", type=['pdf','txt','docx'])
analyze_btn = st.button("Analyze Candidate", type="primary", use_container_width=True)

if analyze_btn and uploaded_file:
    with st.status("🚀 Analyzing Talent...", expanded=True) as status:
        update_status("Reading File...")
        text = extract_text(uploaded_file)
        update_status("Psychometric Profiling...")
        res = analyze_interview(text, candidate_name, role_name)
        st.session_state.analysis_result = res
        update_status("Done.")
        status.update(label="✅ Assessment Complete", state="complete", expanded=False)

# RESULTS DISPLAY
if st.session_state.analysis_result:
    r = st.session_state.analysis_result
    if "error" in r:
        st.error(r['error'])
    else:
        # HEADER TILE
        rec = r['key_insights']['hiring_recommendation']
        rec_color = "#39ff14" if "HIRE" in rec and "NO" not in rec else "#ff4b4b"
        
        st.markdown(f"""
        <div class="lead-header-container">
            <div class="lead-item"><div class="lead-label">CANDIDATE</div><div class="lead-value">{r['meta']['candidate']}</div></div>
            <div class="lead-item"><div class="lead-label">ROLE</div><div class="lead-value">{r['meta']['role']}</div></div>
            <div class="lead-item"><div class="lead-label">RECOMMENDATION</div><div class="lead-value" style="color: {rec_color};">{rec}</div></div>
            <div class="lead-item"><div class="lead-label">FIT SCORE</div><div class="lead-score">{r['scores']['total']}/40</div></div>
        </div>
        """, unsafe_allow_html=True)

        t1, t2 = st.tabs(["🧠 Analysis", "📄 Report"])
        
        with t1:
            c_str, c_red = st.columns(2)
            with c_str:
                st.markdown("### ✅ Strengths")
                for s in r['key_insights']['strengths']: st.success(s)
            with c_red:
                st.markdown("### 🚩 Red Flags")
                for f in r['key_insights']['red_flags']: st.error(f)
            
            st.markdown("### 🛠 Skill Analysis")
            for skill in r['skill_analysis']:
                st.markdown(f"""
                <div class="insight-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="color:#fff; font-weight:bold;">{skill['skill']}</span>
                        <span style="color:#00e5ff;">{skill['level']}</span>
                    </div>
                    <div style="color:#888; font-size:0.9em; margin-top:5px;">Evidence: "{skill['evidence']}"</div>
                </div>
                """, unsafe_allow_html=True)

        with t2:
            pdf_data = generate_hr_pdf(r)
            st.download_button("⬇️ Download Candidate Report", pdf_data, "candidate_report.pdf", "application/pdf", use_container_width=True)
