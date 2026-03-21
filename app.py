import streamlit as st
import requests
from dotenv import load_dotenv
import os, re

load_dotenv()

API = os.getenv("BACKEND_URL")

st.set_page_config(page_title="GitRAG", page_icon="◈", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600&family=Geist:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
section[data-testid="stMain"] { background: #080808 !important; }

[data-testid="stHeader"]       { background: #080808 !important; border-bottom: 1px solid #161616; }
[data-testid="stBottom"]       { background: #080808 !important; border-top: 1px solid #161616 !important; }
[data-testid="stBottom"] > div { background: #080808 !important; }

.block-container { max-width: 760px !important; padding: 2.5rem 1.5rem 6rem !important; }

.brand {
    font-family: 'Geist Mono', monospace;
    font-size: 1.1rem; font-weight: 600;
    color: #f0f0f0; letter-spacing: -0.01em;
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 0.3rem;
}
.brand-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #4ade80; display: inline-block;
    box-shadow: 0 0 8px #4ade8066;
}
.brand-sub {
    font-family: 'Geist Mono', monospace;
    font-size: 0.72rem; color: #333;
    letter-spacing: 0.14em; text-transform: uppercase;
    margin-bottom: 2.8rem;
}

.repo-pill {
    display: inline-flex; align-items: center; gap: 8px;
    background: #0f0f0f; border: 1px solid #1f1f1f;
    border-radius: 999px; padding: 5px 14px 5px 10px;
    font-family: 'Geist Mono', monospace;
    font-size: 0.78rem; color: #4ade80; margin-bottom: 1.8rem;
}
.repo-pill-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #4ade80; box-shadow: 0 0 6px #4ade8088; flex-shrink: 0;
}

.log-wrap {
    background: #0c0c0c; border: 1px solid #1a1a1a;
    border-radius: 8px; padding: 14px 18px; margin: 1rem 0;
}
.log-line {
    font-family: 'Geist Mono', monospace;
    font-size: 0.76rem; color: #3a3a3a;
    line-height: 2; display: flex; align-items: center; gap: 8px;
}
.log-line.active { color: #888; }
.log-line.done   { color: #4ade80; }
.log-prefix { color: #222; }
.log-line.done .log-prefix { color: #1a4a2a; }

.divider { border: none; border-top: 1px solid #141414; margin: 1.6rem 0; }

.msg-row-user  { display: flex; justify-content: flex-end;  margin: 6px 0; }
.msg-row-bot   { display: flex; justify-content: flex-start; margin: 6px 0; }

.bubble-user {
    background: #141414; border: 1px solid #202020;
    border-radius: 14px 14px 3px 14px;
    padding: 10px 16px; max-width: 82%;
    font-family: 'Geist', sans-serif;
    font-size: 0.9rem; color: #d4d4d4; line-height: 1.6;
}
.bubble-bot {
    background: #0d0d0d; border: 1px solid #1a1a1a;
    border-left: 2px solid #4ade80;
    border-radius: 3px 14px 14px 14px;
    padding: 12px 16px; max-width: 90%;
    font-family: 'Geist', sans-serif;
    font-size: 0.9rem; color: #b0b0b0; line-height: 1.75;
}
.bubble-bot code {
    font-family: 'Geist Mono', monospace; font-size: 0.82rem;
    background: #161616; border: 1px solid #222;
    border-radius: 4px; padding: 1px 6px; color: #7dd3fc;
}
.bubble-error {
    background: #1a0a0a; border: 1px solid #3a1010;
    border-left: 2px solid #f87171;
    border-radius: 3px 14px 14px 14px;
    padding: 10px 16px; max-width: 90%;
    font-family: 'Geist Mono', monospace;
    font-size: 0.82rem; color: #f87171; line-height: 1.6;
}

.empty-hint {
    text-align: center; padding: 3rem 0 1rem;
    font-family: 'Geist Mono', monospace;
    font-size: 0.76rem; color: #222; letter-spacing: 0.06em;
}

[data-testid="stTextInput"] input {
    background: #0f0f0f !important; border: 1px solid #222 !important;
    border-radius: 8px !important; color: #e0e0e0 !important;
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.86rem !important; padding: 10px 14px !important;
    transition: border-color 0.15s !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #4ade80 !important;
    box-shadow: 0 0 0 3px #4ade8018 !important;
}
[data-testid="stTextInput"] input::placeholder { color: #2a2a2a !important; }

[data-testid="stChatInput"] textarea {
    background: #0f0f0f !important; border: 1px solid #1e1e1e !important;
    border-radius: 10px !important; color: #e0e0e0 !important;
    font-family: 'Geist', sans-serif !important; font-size: 0.88rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #4ade80 !important;
    box-shadow: 0 0 0 3px #4ade8018 !important;
}
[data-testid="stChatInputSubmitButton"] svg { stroke: #4ade80 !important; }

[data-testid="baseButton-secondary"],
[data-testid="baseButton-primary"] {
    background: #0f0f0f !important; border: 1px solid #1e1e1e !important;
    color: #888 !important; font-family: 'Geist Mono', monospace !important;
    font-size: 0.78rem !important; border-radius: 8px !important;
    transition: all 0.15s !important; letter-spacing: 0.04em;
}
[data-testid="baseButton-secondary"]:hover,
[data-testid="baseButton-primary"]:hover {
    border-color: #4ade80 !important; color: #4ade80 !important;
    background: #0a1a0f !important;
}

[data-testid="stSpinner"] > div { border-top-color: #4ade80 !important; }

div[data-testid="stAlert"] {
    background: #1a0a0a !important; border: 1px solid #3a1010 !important;
    border-radius: 8px !important; color: #f87171 !important;
    font-family: 'Geist Mono', monospace !important; font-size: 0.82rem !important;
}

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── session state ──
for k, v in [("repo_loaded", False), ("repo_url", ""), ("namespace", ""), ("messages", [])]:
    if k not in st.session_state:
        st.session_state[k] = v

def format_response(text: str) -> str:
    text = text.replace("\n", "<br>")
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)   
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)               
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)             
    return text

# ── helpers ──
def log_render(log_box, lines):
    rows = "".join(
        f'<div class="log-line {s}"><span class="log-prefix">{">" if s == "active" else "✓" if s == "done" else " "}</span>{t}</div>'
        for t, s in lines
    )
    log_box.markdown(f'<div class="log-wrap">{rows}</div>', unsafe_allow_html=True)

def api_embed(github_url):
    r = requests.post(f"{API}/rag/embedd", json={"github_url": github_url}, timeout=300)
    r.raise_for_status()
    return r.json()

def api_ask(github_url, question):
    r = requests.post(f"{API}/rag/chat", json={"github_url": github_url, "question": question}, timeout=60)
    r.raise_for_status()
    return r.json()

def api_clear(github_url):
    r = requests.post(f"{API}/rag/clear_namespace", json={"github_url": github_url}, timeout=30)
    r.raise_for_status()
    return r.json()

# ── brand ──
st.markdown("""
<div class="brand"><span class="brand-dot"></span>GitRAG</div>
<div class="brand-sub">chat with any github repository</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
#  NOT LOADED
# ══════════════════════════════════════════
if not st.session_state.repo_loaded:
    url = st.text_input(
        "", placeholder="https://github.com/owner/repo",
        label_visibility="collapsed", key="url_input"
    )
    load_btn = st.button("→  load & embed repository", use_container_width=True)

    if load_btn and url.strip():
        log_box = st.empty()
        try:
            log_render(log_box, [("connecting to api...", "active")])

            with st.spinner(""):
                log_render(log_box, [("cloning & fetching files...", "active")])
                result = api_embed(url.strip())

            files_found   = result.get("files_found", "?")
            chunks_stored = result.get("chunks_stored", "?")

            log_render(log_box, [
                (f"fetched {files_found} files", "done"),
                (f"created & stored {chunks_stored} chunks in pinecone", "done"),
                ("ready — start chatting", "done"),
            ])

            st.session_state.repo_loaded = True
            st.session_state.repo_url    = url.strip()
            st.session_state.namespace   = result.get("github_url", url.strip())
            st.session_state.messages    = []
            st.rerun()

        except requests.exceptions.ConnectionError:
            st.error("cannot reach api — is uvicorn running on http://127.0.0.1:8000?")
        except requests.exceptions.HTTPError as e:
            detail = e.response.json().get("detail", str(e))
            st.error(f"api error: {detail}")
        except Exception as e:
            st.error(f"error: {e}")

# ══════════════════════════════════════════
#  LOADED — chat view
# ══════════════════════════════════════════
else:
    namespace = st.session_state.repo_url.replace("https://github.com/", "").replace(".git", "")

    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(
            f'<div class="repo-pill"><span class="repo-pill-dot"></span>{namespace}</div>',
            unsafe_allow_html=True
        )
    with col2:
        if st.button("✕  clear", use_container_width=True):
            with st.spinner(""):
                try:
                    api_clear(st.session_state.repo_url)
                except Exception:
                    pass
            st.session_state.repo_loaded = False
            st.session_state.repo_url    = ""
            st.session_state.namespace   = ""
            st.session_state.messages    = []
            st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown(
            '<div class="empty-hint">ask anything about this codebase</div>',
            unsafe_allow_html=True
        )

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="msg-row-user"><div class="bubble-user">{msg["content"]}</div></div>',
                unsafe_allow_html=True
            )
        elif msg.get("error"):
            st.markdown(
                f'<div class="msg-row-bot"><div class="bubble-error">{msg["content"]}</div></div>',
                unsafe_allow_html=True
            )
        else:
            raw = msg["content"] or "no response received."
            content = format_response(raw if isinstance(raw, str) else str(raw)).replace("\n", "<br>")
            st.markdown(
                f'<div class="msg-row-bot"><div class="bubble-bot">{content}</div></div>',
                unsafe_allow_html=True
            )

    question = st.chat_input("ask about the codebase...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner(""):
            try:
                result = api_ask(st.session_state.repo_url, question)
                answer = result.get("answer") or "no response received."
                if isinstance(answer, dict):
                    answer = str(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except requests.exceptions.HTTPError as e:
                detail = e.response.json().get("detail", str(e))
                st.session_state.messages.append({"role": "assistant", "content": f"api error: {detail}", "error": True})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"error: {e}", "error": True})
        st.rerun()