"""
app.py — Production-ready Streamlit UI for the Financial Advisor Chatbot.
Pure UI layer — all business logic delegated to gemini_client.py and prompts.py.
"""

import os
import streamlit as st
from loguru import logger

from gemini_client import GeminiChatClient, ChatResponse
from prompts import GREETING_MESSAGE, ERROR_MESSAGES

# ── Page Configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinBot — AI Financial Advisor",
    page_icon="💹",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── App background ── */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1528 50%, #0a1020 100%);
    min-height: 100vh;
}

/* ── Header banner ── */
.fin-header {
    background: linear-gradient(90deg, #00d4aa 0%, #0080ff 100%);
    padding: 18px 28px;
    border-radius: 16px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: 0 4px 24px rgba(0, 212, 170, 0.25);
}
.fin-header h1 {
    color: #ffffff;
    font-size: 1.7rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.3px;
}
.fin-header p {
    color: rgba(255,255,255,0.85);
    font-size: 0.85rem;
    margin: 2px 0 0 0;
}

/* ── Chat messages ── */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-bottom: 8px;
}

.msg-user {
    background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
    border: 1px solid rgba(0, 128, 255, 0.3);
    border-radius: 16px 16px 4px 16px;
    padding: 14px 18px;
    margin-left: 60px;
    color: #e2e8f0;
    font-size: 0.93rem;
    line-height: 1.6;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}

.msg-bot {
    background: linear-gradient(135deg, #0d2137 0%, #0a1a2e 100%);
    border: 1px solid rgba(0, 212, 170, 0.25);
    border-radius: 16px 16px 16px 4px;
    padding: 14px 18px;
    margin-right: 60px;
    color: #e2e8f0;
    font-size: 0.93rem;
    line-height: 1.6;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}

.msg-bot strong { color: #00d4aa; }
.msg-bot code {
    background: rgba(0, 212, 170, 0.12);
    color: #00d4aa;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.85em;
}

.role-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 6px;
    opacity: 0.7;
}
.role-user { color: #60a5fa; text-align: right; }
.role-bot  { color: #00d4aa; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1528 0%, #0a0e1a 100%);
    border-right: 1px solid rgba(0, 212, 170, 0.15);
}

.stat-card {
    background: rgba(0, 212, 170, 0.07);
    border: 1px solid rgba(0, 212, 170, 0.18);
    border-radius: 12px;
    padding: 14px;
    margin: 8px 0;
    text-align: center;
}
.stat-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #00d4aa;
    display: block;
}
.stat-label {
    font-size: 0.75rem;
    color: rgba(226, 232, 240, 0.6);
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

/* ── Input area ── */
.stTextInput > div > div > input {
    background: rgba(13, 25, 50, 0.95) !important;
    border: 1px solid rgba(0, 212, 170, 0.35) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    padding: 12px 16px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #00d4aa !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 170, 0.2) !important;
}
.stTextInput > div > div > input::placeholder { color: rgba(226,232,240,0.35) !important; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #00d4aa 0%, #0080ff 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 10px 20px !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* ── Topic pills ── */
.topic-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 12px 0;
}
.topic-pill {
    background: rgba(0, 212, 170, 0.08);
    border: 1px solid rgba(0, 212, 170, 0.25);
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 0.8rem;
    color: #00d4aa;
    cursor: pointer;
}

/* ── Dividers ── */
hr { border-color: rgba(0, 212, 170, 0.12) !important; }

/* ── Scrollable chat history ── */
.chat-scroll {
    max-height: 520px;
    overflow-y: auto;
    padding-right: 4px;
    scrollbar-width: thin;
    scrollbar-color: rgba(0, 212, 170, 0.3) transparent;
}
</style>
""", unsafe_allow_html=True)


# ── Session State Initialization ───────────────────────────────────────────────

def init_session_state() -> None:
    """Initialize all Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []  # List of {"role": str, "content": str}

    if "client" not in st.session_state:
        st.session_state.client = None
        st.session_state.client_error = None
        try:
            st.session_state.client = GeminiChatClient()
            logger.info("GeminiChatClient initialized in session state.")
        except EnvironmentError as e:
            st.session_state.client_error = str(e)
            logger.error(f"Client init error: {e}")
        except Exception as e:
            st.session_state.client_error = ERROR_MESSAGES["general"]
            logger.error(f"Unexpected client init error: {e}")

    if "greeted" not in st.session_state:
        st.session_state.greeted = False

    if "input_key" not in st.session_state:
        st.session_state.input_key = 0  # Used to reset input field


# ── Helper: Render a single chat message ──────────────────────────────────────

def render_message(role: str, content: str) -> None:
    if role == "user":
        st.markdown(f"""
        <div class="role-label role-user">You</div>
        <div class="msg-user">{content}</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="role-label role-bot">💹 FinBot</div>
        <div class="msg-bot">{content}</div>
        """, unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## 💹 FinBot")
        st.markdown("<p style='color:rgba(226,232,240,0.5); font-size:0.8rem;'>AI Financial Advisor</p>", unsafe_allow_html=True)
        st.divider()

        # Session stats
        if st.session_state.client:
            stats = st.session_state.client.stats
            st.markdown("### 📊 Session Stats")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""<div class="stat-card">
                    <span class="stat-value">{stats.total_turns}</span>
                    <span class="stat-label">Turns</span>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class="stat-card">
                    <span class="stat-value">{stats.total_tokens:,}</span>
                    <span class="stat-label">Tokens</span>
                </div>""", unsafe_allow_html=True)

            st.markdown(f"""<div class="stat-card">
                <span class="stat-value">{stats.session_duration_mins}m</span>
                <span class="stat-label">Session Duration</span>
            </div>""", unsafe_allow_html=True)

            if stats.total_errors > 0:
                st.markdown(f"⚠️ **Errors:** {stats.total_errors}", unsafe_allow_html=True)

        st.divider()

        # Quick topic starters
        st.markdown("### 💡 Quick Topics")
        topics = [
            ("💰", "Budget Planning", "How do I create a monthly budget on ₹50,000 salary?"),
            ("📈", "Start Investing", "I'm 25 and want to start investing. Where do I begin?"),
            ("🏦", "Retirement", "How much should I save for retirement by age 30?"),
            ("💳", "Pay Off Debt", "Best strategy to pay off credit card debt fast?"),
            ("🏠", "Real Estate", "Is it better to buy or rent a home right now?"),
            ("🧾", "Save on Taxes", "What are common ways to reduce my income tax legally?"),
        ]

        for icon, label, prompt in topics:
            if st.button(f"{icon} {label}", use_container_width=True, key=f"topic_{label}"):
                st.session_state["quick_prompt"] = prompt
                st.rerun()

        st.divider()

        # Reset button
        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.greeted = False
            if st.session_state.client:
                st.session_state.client.reset_session()
            st.rerun()

        st.markdown("""
        <p style='color:rgba(226,232,240,0.35); font-size:0.72rem; margin-top:16px;'>
        ⚠️ For educational purposes only.<br>
        Not a substitute for professional financial advice.
        </p>
        """, unsafe_allow_html=True)


# ── Main App ───────────────────────────────────────────────────────────────────

def main() -> None:
    init_session_state()
    render_sidebar()

    # ── Header ──
    st.markdown("""
    <div class="fin-header">
        <div style="font-size:2rem">💹</div>
        <div>
            <h1>FinBot</h1>
            <p>Your AI-Powered Personal Financial Advisor</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── API Key Error ──
    if st.session_state.client_error:
        st.error(st.session_state.client_error)
        st.info("👉 Create a `.env` file in the project directory and add:\n```\nGEMINI_API_KEY=your_key_here\n```")
        st.stop()

    # ── Greeting (first load) ──
    if not st.session_state.greeted:
        st.session_state.messages.append({"role": "assistant", "content": GREETING_MESSAGE})
        st.session_state.greeted = True

    # ── Chat History ──
    st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        render_message(msg["role"], msg["content"])
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ── Handle quick topic button ──
    quick_prompt = st.session_state.pop("quick_prompt", None)

    # ── Input Area ──
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            label="Message",
            label_visibility="collapsed",
            placeholder="Ask me anything about personal finance, investing, taxes...",
            key=f"chat_input_{st.session_state.input_key}",
            value=quick_prompt or "",
        )
    with col_send:
        send_clicked = st.button("Send ➤", use_container_width=True)

    # ── Process Message ──
    message_to_send = None
    if send_clicked and user_input.strip():
        message_to_send = user_input.strip()
    elif quick_prompt:
        message_to_send = quick_prompt

    if message_to_send:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": message_to_send})

        # Clear input by incrementing key
        st.session_state.input_key += 1

        # Show spinner while calling API
        with st.spinner("FinBot is analyzing your question..."):
            response: ChatResponse = st.session_state.client.send_message(message_to_send)

        # Add bot response to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response.text,
        })

        if not response.success:
            logger.warning(f"Failed response returned to user: {response.error}")
            with st.expander("🔍 Debug info (click to expand)", expanded=True):
                st.code(f"Error type : {response.error}\nLatency    : {response.latency_ms}ms\n\nCheck logs/chatbot.log for the full traceback.")

        st.rerun()


if __name__ == "__main__":
    main()
