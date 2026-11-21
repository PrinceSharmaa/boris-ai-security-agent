"""BORIS — bright, chat-first Streamlit interface for the existing Phase 5 API."""
import os
from datetime import datetime
import requests
import streamlit as st

st.set_page_config(page_title="BORIS | Security Intelligence", page_icon="🔷", layout="wide", initial_sidebar_state="expanded")
API = os.getenv("BORIS_API_URL", "http://localhost:8000").rstrip("/")
KEY = os.getenv("BORIS_API_KEY", "change-this-for-local-use")
HEADERS = {"X-API-Key": KEY}

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
:root {color-scheme: light;}
html, body, [class*="css"], [data-testid="stApp"] {font-family:'DM Sans',sans-serif;}
.stApp {background:linear-gradient(135deg,#f4f9ff 0%,#f9fbff 55%,#eef7ff 100%);color:#163353;}
[data-testid="stHeader"] {background:transparent;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#ffffff 0%,#eef6ff 100%);border-right:1px solid #d9e8f8;}
[data-testid="stSidebar"] * {color:#173958;}
.block-container {padding-top:1.5rem;max-width:1500px;padding-bottom:3rem;}
h1,h2,h3,p,li,label {color:#173958;}
.hero {padding:25px 29px;border-radius:23px;background:linear-gradient(112deg,#1762d5 0%,#2385ed 55%,#4db9f2 100%);color:white;box-shadow:0 14px 36px rgba(30,101,198,.19);margin-bottom:20px;position:relative;overflow:hidden;}
.hero:after {content:'';position:absolute;width:270px;height:270px;border-radius:50%;border:44px solid rgba(255,255,255,.08);right:-65px;top:-125px;}
.hero .eyebrow {font-size:12px;font-weight:800;letter-spacing:2px;color:#d7f0ff;}
.hero h1 {color:white;font-size:38px;font-weight:800;margin:4px 0 5px;}
.hero p {color:#eaf6ff;font-size:15px;margin:0;max-width:780px;}
.boris-brand {font-size:26px;font-weight:800;color:#1768d9;letter-spacing:1px;margin:3px 0 0;}
.brand-sub {font-size:12px;color:#6786a5;margin:0 0 20px;}
.section-head {font-size:21px;font-weight:800;color:#153d67;margin:15px 0 10px;}
.note {background:#eaf5ff;border:1px solid #cce7ff;border-radius:13px;padding:11px 15px;color:#235781;font-size:13px;margin:12px 0;}
.cardline {background:white;border:1px solid #dfecfa;border-radius:17px;padding:15px 18px;margin:10px 0;box-shadow:0 5px 15px rgba(30,91,161,.04);}
.kicker {font-size:11px;font-weight:800;color:#3680c8;text-transform:uppercase;letter-spacing:1px;}
[data-testid="stMetric"] {background:white;border:1px solid #dceafa;border-radius:18px;padding:15px 18px;box-shadow:0 5px 16px rgba(28,90,160,.06);}
[data-testid="stMetricValue"] {color:#1669d3;}
[data-testid="stChatMessage"] {background:white;border:1px solid #e1ecfa;border-radius:18px;margin-bottom:12px;box-shadow:0 4px 15px rgba(20,80,140,.04);}
[data-testid="stChatInput"] {border:1px solid #a9cef5;border-radius:15px;background:white;}
.stButton>button[kind="primary"] {background:linear-gradient(95deg,#176cde,#3296f1);border:0;color:white;border-radius:11px;font-weight:700;box-shadow:0 5px 15px rgba(20,109,222,.18);}
.stButton>button {border-radius:11px;border-color:#c4def9;color:#195a9c;font-weight:600;}
.stButton>button:hover {border-color:#1674df;color:#1369d5;}
[data-testid="stToggle"] {color:#173958;}
[data-testid="stFileUploader"] {background:white;border-radius:16px;padding:10px;}
[data-testid="stExpander"] {background:white;border:1px solid #dfebf9;border-radius:12px;}
[data-testid="stDataFrame"] {border-radius:12px;overflow:hidden;}
div[data-baseweb="select"]>div {background:white;border-radius:11px;}
@media(max-width:720px){.hero{padding:20px}.hero h1{font-size:29px}.block-container{padding-top:.7rem}}

/* FINAL READABILITY PATCH — force light Streamlit controls in every browser theme. */
:root { --boris-blue:#1768d9; --boris-navy:#153d67; }
[data-testid="stAppViewContainer"], [data-testid="stMain"], .stApp { color:#153d67 !important; }
.brand-lockup { display:flex; align-items:center; gap:12px; margin:4px 0 3px; }
.brand-symbol { display:inline-flex; width:44px; height:44px; filter:drop-shadow(0 5px 8px rgba(27,110,210,.15)); }
.brand-symbol svg { width:100%; height:100%; }
.brand-lockup .boris-brand { margin:0; font-size:29px; letter-spacing:.6px; }
/* Fix the screenshot's black quick-action buttons and nearly invisible labels. */
.stButton > button,
.stButton > button[kind="secondary"],
.stButton > button[kind="tertiary"],
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-tertiary"] {
  background:#fff !important;
  color:#17538c !important;
  border:1.5px solid #bddbfa !important;
  border-radius:14px !important;
  box-shadow:0 5px 14px rgba(27,106,204,.07) !important;
  min-height:48px;
  transition:background .18s,transform .18s,box-shadow .18s;
}
.stButton > button *, [data-testid="stBaseButton-secondary"] * { color:inherit !important; }
.stButton > button:hover, [data-testid="stBaseButton-secondary"]:hover {
  background:#e8f3ff !important; color:#0759b5 !important;
  border-color:#4399ee !important; box-shadow:0 8px 20px rgba(27,106,204,.14) !important;
  transform:translateY(-1px);
}
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] {
  background:linear-gradient(105deg,#1767d8,#3297ef) !important;
  color:#fff !important; border:1px solid #1767d8 !important;
}
.stButton > button[kind="primary"] *, [data-testid="stBaseButton-primary"] * {color:#fff !important;}
/* Modern bright chat composer: Streamlit versions use either of these containers. */
[data-testid="stChatInput"], [data-testid="stChatInputContainer"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] [data-baseweb="textarea"] {
  background:#fff !important;
  border-color:#a8d1fa !important;
  border-radius:19px !important;
  color:#173958 !important;
}
[data-testid="stChatInput"] {
  border:1.5px solid #9ac9fa !important;
  box-shadow:0 8px 28px rgba(32,108,203,.12) !important;
  overflow:hidden;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea::placeholder {
  color:#1b4d78 !important;
  -webkit-text-fill-color:#1b4d78 !important;
  opacity:1 !important;
}
[data-testid="stChatInput"] button {
  background:#1768d9 !important;
  color:#fff !important;
  border-radius:12px !important;
}
[data-testid="stChatInput"] button svg { fill:none; stroke:#fff !important; color:#fff !important; }
[data-testid="stChatInput"]:focus-within {border-color:#207de8 !important;box-shadow:0 0 0 3px rgba(45,141,245,.12),0 8px 28px rgba(32,108,203,.12) !important;}
/* Readable navigation and controls regardless of dark OS preference. */
[data-testid="stSidebar"] [role="radiogroup"] label,
[data-testid="stSidebar"] [role="radiogroup"] label *,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
[data-testid="stSidebar"] .stButton button {color:#173958 !important;}
[data-testid="stSidebar"] [role="radiogroup"] label {padding:5px 7px;border-radius:10px;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background:#e9f4ff;}
[data-testid="stSidebar"] [data-testid="stToggle"] label * {color:#173958 !important;}
[data-testid="stSidebar"] [data-testid="stAlert"] {border-radius:14px;}
[data-testid="stSidebar"] [data-testid="stAlert"] * {color:#0f513f !important;}
[data-testid="stChatMessage"] {background:#fff !important;}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {color:#173958 !important;}

</style>""", unsafe_allow_html=True)


def request(method, path, **kwargs):
    response = requests.request(method, API + path, headers=HEADERS, timeout=kwargs.pop("timeout", 30), **kwargs)
    response.raise_for_status()
    return response.json()


def error_text(exc):
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        try:
            return f"HTTP {exc.response.status_code}: {exc.response.json().get('detail', exc.response.text)}"
        except ValueError:
            return f"HTTP {exc.response.status_code}: {exc.response.text[:250]}"
    return str(exc)


def safe_api(method, path, **kwargs):
    try:
        return request(method, path, **kwargs)
    except requests.RequestException as exc:
        st.error(f"Backend request failed: {error_text(exc)}")
        return None


def render_agent_detail(data):
    with st.expander("🔎 Investigation trace & evidence", expanded=st.session_state.show_trace):
        c1,c2,c3=st.columns(3)
        c1.caption(f"Agent: {data.get('selected_agent', '—')}")
        c2.caption(f"Intent: {data.get('intent', '—')}")
        c3.caption(f"Model: {data.get('model', '—')}")
        if data.get("plan"):
            st.markdown("**Execution plan**")
            st.write(" → ".join(data["plan"]))
        if data.get("tool_trace"):
            st.markdown("**Executed tools**")
            st.dataframe(data["tool_trace"], use_container_width=True, hide_index=True)
        if data.get("event_filters"):
            st.caption(f"Event filters: {data['event_filters']}")
        if data.get("triage"):
            st.markdown("**Priority assessments**")
            st.dataframe(data["triage"], use_container_width=True, hide_index=True)
        if data.get("correlations"):
            st.markdown("**Correlation hypotheses**")
            st.json(data["correlations"])
        if data.get("ticket_drafts"):
            st.markdown("**Ticket drafts (manual ServiceNow copy)**")
            st.json(data["ticket_drafts"])
        if data.get("citations"):
            st.markdown("**Retrieved runbook sources**")
            for item in data["citations"]:
                st.caption(f"[{item.get('index')}] {item.get('filename')} · page {item.get('page')} · similarity {item.get('score',0):.2f}")
        if data.get("approval_requests"):
            st.warning(f"{len(data['approval_requests'])} advisory human-review request(s) created")


for key, default in {"messages":[],"show_trace":False,"show_monitor":False,"compact":False,"severity":"all","pending_prompt":None}.items():
    if key not in st.session_state:
        st.session_state[key]=default

with st.sidebar:
    st.markdown('''<div class="brand-lockup"><span class="brand-symbol"><svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-label="BORIS security emblem" role="img"><defs><linearGradient id="shieldGradient" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#56b5ff"/><stop offset="1" stop-color="#0755cf"/></linearGradient></defs><path d="M24 3 43 10v13c0 12-7 19-19 23C12 42 5 35 5 23V10L24 3Z" fill="url(#shieldGradient)"/><path d="M24 8 38 13v10c0 9-5 15-14 18C15 38 10 32 10 23V13L24 8Z" fill="none" stroke="#fff" stroke-width="2.5"/><path d="m17 24 5 5 10-12" fill="none" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span class="boris-brand">BORIS</span></div><div class="brand-sub">SECURITY INTELLIGENCE WORKSPACE</div>''',unsafe_allow_html=True)
    page=st.radio("Workspace",["💬  AI Assistant","📊  Security Overview","📚  Knowledge Hub","✅  Human Review","⚙️  Settings"],label_visibility="collapsed")
    st.divider()
    st.markdown("**Workspace controls**")
    st.toggle("Show agent reasoning trace",key="show_trace",help="Displays tool execution and evidence, not private model reasoning.")
    st.toggle("Show monitoring details",key="show_monitor",help="Show raw event records and correlation groups on the overview page.")
    st.toggle("Compact responses",key="compact",help="Ask BORIS to keep its answer concise. Does not modify the backend model settings.")
    if st.button("＋  New conversation",use_container_width=True):
        st.session_state.messages=[]
        st.session_state.pending_prompt=None
        st.rerun()
    st.divider()
    try:
        health=request("GET","/api/health",timeout=3)
        st.success("● Backend connected" if health.get("status")=="ok" else "Backend responded")
    except requests.RequestException:
        st.warning("● Backend offline")
    st.caption("Local prototype · Synthetic alerts · No automatic remediation")

st.markdown('''<div class="hero"><div class="eyebrow">SECURITY OPERATIONS · AI-POWERED</div><h1>BORIS</h1><p>One workspace to investigate alerts, correlate evidence, retrieve playbooks and prepare incident notes.</p></div>''',unsafe_allow_html=True)

if page.startswith("💬"):
    left,right=st.columns([3,1],gap="large")
    with left:
        st.markdown('<div class="section-head">Security copilot</div>',unsafe_allow_html=True)
        if not st.session_state.messages:
            st.markdown('<div class="note">Ask a question or select a quick action below. BORIS executes available local tools and returns an evidence-based response.</div>',unsafe_allow_html=True)
            prompts=[
                ("🔍 Investigate alerts","Investigate the latest critical synthetic alerts, correlate related events and explain their priorities."),
                ("📝 Draft ServiceNow notes","Find the latest low-priority synthetic security event and generate a complete ServiceNow draft with category, description, investigation findings, impact and recommended next steps."),
                ("📖 Retrieve a runbook","Find the relevant malware investigation runbook and summarize the required investigation and escalation steps."),
                ("🛡️ Review high-risk incidents","Identify synthetic P1/P2 incidents, explain the priority rationale and indicate which need human review."),
            ]
            for i in range(0,len(prompts),2):
                cols=st.columns(2)
                for col,(label,prompt) in zip(cols,prompts[i:i+2]):
                    if col.button(label,key=f"quick_{i}_{label}",use_container_width=True):
                        st.session_state.pending_prompt=prompt
                        st.rerun()
        for i,msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"],avatar="🔷" if msg["role"]=="assistant" else "👤"):
                st.markdown(msg["content"])
                if msg.get("data"):
                    render_agent_detail(msg["data"])
        prompt=st.chat_input("Ask BORIS anything… e.g., investigate a security alert")
        if st.session_state.pending_prompt:
            prompt=st.session_state.pending_prompt
            st.session_state.pending_prompt=None
        if prompt:
            st.session_state.messages.append({"role":"user","content":prompt})
            with st.chat_message("user",avatar="👤"):
                st.markdown(prompt)
            actual_prompt=prompt + ("\nPlease keep the response concise and structured." if st.session_state.compact else "")
            with st.chat_message("assistant",avatar="🔷"):
                with st.spinner("BORIS is investigating…"):
                    try:
                        data=request("POST","/api/chat",json={"message":actual_prompt},timeout=240)
                        answer=data.get("answer","No response returned.")
                    except requests.RequestException as exc:
                        data=None
                        answer=f"Unable to complete investigation: {error_text(exc)}"
                st.markdown(answer)
                if data:
                    render_agent_detail(data)
            st.session_state.messages.append({"role":"assistant","content":answer,"data":data})
    with right:
        st.markdown('<div class="section-head">At a glance</div>',unsafe_allow_html=True)
        try:
            s=request("GET","/api/events/summary",timeout=5)
            st.metric("Synthetic alerts",s.get("total",0))
            st.metric("Critical",s.get("by_severity",{}).get("critical",0))
            st.metric("High",s.get("by_severity",{}).get("high",0))
        except requests.RequestException:
            st.info("Start FastAPI to load event metrics.")
        st.markdown('<div class="cardline"><div class="kicker">Workflow</div><b>Ask → Investigate → Validate → Draft</b><p style="font-size:12px;color:#607e9e;margin:8px 0 0">Runbook retrieval and scoring are advisory. ServiceNow submission remains manual.</p></div>',unsafe_allow_html=True)
        st.caption("Incident IDs must exist in the local data source. This build does not connect to ServiceNow.")

elif page.startswith("📊"):
    st.markdown('<div class="section-head">Security overview</div>',unsafe_allow_html=True)
    st.caption("Demo data only — synthetic events are not live MDE, SentinelOne or SIEM telemetry.")
    toolbar=st.columns([1.3,1.3,1.5,1.3])
    if toolbar[0].button("＋ Seed demo data",use_container_width=True):
        data=safe_api("POST","/api/demo/seed")
        if data:st.toast(f"Inserted {data['inserted']} synthetic alerts")
    if toolbar[1].button("⚡ Generate 10 alerts",use_container_width=True):
        data=safe_api("POST","/api/demo/generate",json={"count":10})
        if data:st.toast("Generated 10 synthetic alerts")
    severity=toolbar[2].selectbox("Severity",["all","critical","high","medium","low"],label_visibility="collapsed",key="severity")
    if toolbar[3].button("↻ Refresh",use_container_width=True):st.rerun()
    summary=safe_api("GET","/api/events/summary")
    if summary:
        cols=st.columns(5)
        cols[0].metric("All alerts",summary.get("total",0))
        for i,sev in enumerate(["critical","high","medium","low"],1):
            cols[i].metric(sev.title(),summary.get("by_severity",{}).get(sev,0))
    params={"limit":100}
    if severity!="all":params["severity"]=severity
    events=safe_api("GET","/api/events",params=params)
    if events:
        records=events.get("events",[])
        st.markdown('<div class="section-head">Recent alerts</div>',unsafe_allow_html=True)
        if records:
            st.dataframe([{k:r.get(k) for k in ["observed_at","severity","source","title","hostname","status","id"]} for r in records],use_container_width=True,hide_index=True)
        else:st.info("No alerts match the selected filter.")
    if st.session_state.show_monitor:
        st.markdown('<div class="section-head">Correlation hypotheses</div>',unsafe_allow_html=True)
        corr=safe_api("GET","/api/incidents/correlations")
        if corr:
            groups=corr.get("correlations",[])
            if groups:st.dataframe(groups,use_container_width=True,hide_index=True)
            else:st.info("No correlated event groups found in the last 24 hours.")
        with st.expander("Score or draft from an event ID"):
            event_id=st.text_input("Synthetic event ID",placeholder="Paste an event UUID from the table")
            c1,c2=st.columns(2)
            if c1.button("Calculate priority",disabled=not event_id):
                data=safe_api("GET",f"/api/incidents/{event_id.strip()}/score")
                if data:st.json(data)
            if c2.button("Draft ticket notes",disabled=not event_id):
                data=safe_api("POST",f"/api/tickets/{event_id.strip()}/draft")
                if data:st.json(data)

elif page.startswith("📚"):
    st.markdown('<div class="section-head">Knowledge hub</div>',unsafe_allow_html=True)
    st.markdown('<div class="note">Upload security runbooks and policies. BORIS uses these documents for retrieval-augmented responses.</div>',unsafe_allow_html=True)
    uploads=st.file_uploader("Choose documents",type=["pdf","docx","txt","md","csv"],accept_multiple_files=True)
    if st.button("⬆️ Ingest documents",type="primary",disabled=not uploads):
        for f in uploads:
            try:
                data=request("POST","/api/documents/upload",files={"file":(f.name,f.getvalue())},timeout=240)
                st.success(f"Indexed {f.name}: {data.get('chunks','?')} chunks")
            except requests.RequestException as exc:st.error(f"{f.name}: {error_text(exc)}")
    st.markdown('<div class="section-head">Indexed documents</div>',unsafe_allow_html=True)
    docs=safe_api("GET","/api/documents",timeout=60)
    if docs is not None:
        if not docs:st.info("No documents indexed yet.")
        for doc in docs:
            c1,c2=st.columns([6,1])
            c1.markdown(f"📄 **{doc.get('filename','Document')}**")
            if c2.button("Delete",key=f"delete_{doc['document_id']}"):
                if safe_api("DELETE",f"/api/documents/{doc['document_id']}") is not None:st.rerun()

elif page.startswith("✅"):
    st.markdown('<div class="section-head">Human review queue</div>',unsafe_allow_html=True)
    st.markdown('<div class="note">P1/P2 review decisions are advisory records only. No security actions or ServiceNow updates are executed.</div>',unsafe_allow_html=True)
    pending=safe_api("GET","/api/approvals",params={"status":"pending"})
    if pending:
        items=pending.get("approvals",[])
        st.metric("Pending reviews",len(items))
        if not items:st.success("No pending review requests.")
        for item in items[:40]:
            with st.expander(f"🛡️ {item['event_id']} · {item.get('payload',{}).get('priority','Unknown')}"):
                st.json(item.get("payload",{}))
                reviewer=st.text_input("Reviewer",key=f"reviewer_{item['id']}")
                reason=st.text_input("Decision reason",key=f"reason_{item['id']}")
                a,b=st.columns(2)
                for col,decision in [(a,"approved"),(b,"rejected")]:
                    if col.button(decision.title(),key=f"{decision}_{item['id']}",use_container_width=True):
                        if not reviewer.strip():st.warning("Enter reviewer name first.")
                        else:
                            result=safe_api("POST",f"/api/approvals/{item['id']}/decision",json={"decision":decision,"reviewer":reviewer.strip(),"reason":reason})
                            if result:st.rerun()

else:
    st.markdown('<div class="section-head">System settings</div>',unsafe_allow_html=True)
    st.markdown('<div class="note">Appearance and toggles are managed in the sidebar. Backend configuration is read-only here.</div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        st.markdown("**Backend health**")
        data=safe_api("GET","/api/health",timeout=5)
        if data:st.json(data)
    with b:
        st.markdown("**Model configuration**")
        data=safe_api("GET","/api/models",timeout=5)
        if data:st.json(data)
    st.caption("Stack: Streamlit · FastAPI · LangGraph · Ollama · ChromaDB · SQLite · Sentence Transformers")
    st.warning("No live vendor connector, real ServiceNow incident lookup, automatic ticket submission, or production-grade RBAC is included.")
