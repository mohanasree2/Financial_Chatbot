#  FinBot — AI Financial Advisor Chatbot

> A production-ready, multi-turn conversational chatbot powered by **Google Gemini GenAI API**, built with **Streamlit** following real-world AI engineering standards.

---

##  Domain: Personal Finance & Investment Advisory

FinBot provides intelligent, domain-specific guidance on:
-  Budgeting & saving strategies
-  Investment planning (stocks, ETFs, mutual funds, crypto)
-  Retirement planning (401k, IRA, Roth IRA)
-  Tax optimization
-  Debt management
-  Real estate investment basics

---

##  Project Architecture

```
financial_chatbot/
│
├── app.py                  # Streamlit UI layer (pure UI, no business logic)
├── gemini_client.py        # Gemini API integration (modular, separated from UI)
├── prompts.py              # System prompts & configurable prompt templates
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .env                    # Your API key (gitignored)
└── logs/
    └── chatbot.log         # Auto-rotating application logs
```

### Separation of Concerns
| File | Responsibility |
|------|----------------|
| `app.py` | UI rendering, session state, user interaction |
| `gemini_client.py` | API calls, error handling, token tracking, logging |
| `prompts.py` | System prompts, domain constraints, response templates |

---

##  Setup & Installation

### 1. Clone / Download the project
```bash
git clone <repo-url>
cd financial_chatbot
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your Gemini API key
```bash
cp .env.example .env
```
Edit `.env` and add your key:
```
GEMINI_API_KEY=your_gemini_api_key_here
```
Get your free API key at: https://makersuite.google.com/app/apikey

### 5. Run the app
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

##  Technical Requirements Fulfilled

###  4.1 Gemini API Integration
| Requirement | Implementation |
|-------------|---------------|
| Gemini API Integration | `gemini_client.py` → `GeminiChatClient` class |
| Secure API key management | `python-dotenv` → `.env` file, never hardcoded |
| Structured request/response | `ChatResponse` dataclass with typed fields |
| Exception handling & fallback | Try/except with typed error categories + fallback messages |
| API call logging | Loguru → `logs/chatbot.log` with rotation |
| Token usage optimization | Context compression after N turns (`_compress_context()`) |

###  4.2 Advanced Prompt Engineering
| Requirement | Implementation |
|-------------|---------------|
| Structured system prompts | `prompts.py` → `SYSTEM_PROMPT` with sections |
| Role-based instructions | FinBot persona with domain expertise defined |
| Domain-specific constraints | Off-topic redirect rules, disclaimer requirements |
| Configurable & reusable | All prompts in `prompts.py`, easily swappable |

###  4.3 User Interface
| Requirement | Implementation |
|-------------|---------------|
| Chat-style interface | Message bubbles with user/bot differentiation |
| Real-time response rendering | Streaming via Streamlit spinner + `st.rerun()` |
| Conversation history display | Scrollable chat history with full session |
| Loading indicator | `st.spinner("FinBot is analyzing...")` |
| User-friendly layout | Sidebar stats, quick topic buttons, clean dark UI |

---

##  Key Features

### Production-Grade Error Handling
```python
# Error types handled:
- API quota/rate limit exceeded → user-friendly message + retry guidance
- Network errors → connection check prompt
- Safety filter blocks → rephrase guidance
- Missing API key → setup instructions
- General exceptions → graceful fallback
```

### Session Statistics (Live Dashboard)
- Total conversation turns
- Total tokens consumed (input + output)
- Session duration
- Error count

### Token Optimization
- Context compression kicks in every 20 turns
- Old conversation summarized and injected as compact context
- Prevents context window overflow on long sessions

### Quick Topic Starters (Sidebar)
Pre-built prompts for the 6 most common financial questions — one click to start a focused conversation.

---

##  Deployment

### Deploy to Streamlit Cloud (Free)
1. Push code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Add `GEMINI_API_KEY` in **Secrets** (Settings → Secrets)
5. Deploy 

### Deploy to Hugging Face (Free)
#### 1. Create a new Space
- Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **Create new Space**
- Fill in:
  - **Space name:** `finbot` (or any name)
  - **SDK:** `Streamlit`
  - **SDK_Version:** `based on the version using`
  - **Visibility:** Public or Private
- Click **Create Space**

#### 2. Upload your project files
Upload all project files to the Space repository. Your file structure must be:
```
/
├── app.py
├── gemini_client.py
├── prompts.py
└── requirements.txt
```
>  Do **not** upload your `.env` file — API keys go in Secrets (see next step) or simply create a file named `.gitignore` and write '.env' in that and upload that file

You can upload via the HF web UI, or push with Git:
```bash
git clone https://huggingface.co/spaces/<your-username>/<space-name>
# copy your files in, then:
git add .
git commit -m "Initial deploy"
git push
```

#### 3. Add your Gemini API key as a Secret
- In your Space, go to **Settings → Variables and Secrets**
- Click **New Secret**
- Set:
  - **Name:** `GEMINI_API_KEY`
  - **Value:** your key from [aistudio.google.com](https://aistudio.google.com/app/apikey)
- Make sure it is marked as **Secret** (not a public variable)

#### 4. Restart the Space
- Go to **Settings → Factory reboot** (or just push a new commit)
- Wait ~60 seconds for the Space to rebuild and install dependencies

#### 5. Verify it's live
- Click the **App** tab in your Space
- You should see FinBot load with the greeting message
- Send a test message — the response confirms the API key is working

---


### Deploy to Google Cloud Run
```bash
# Build Docker image
docker build -t finbot .

# Deploy
gcloud run deploy finbot --image finbot --platform managed
```

---

##  Logs

Application logs are written to `logs/chatbot.log` with:
- Auto-rotation at 10 MB
- 7-day retention
- Structured format: `TIMESTAMP | LEVEL | MESSAGE`

Sample log:
```
2024-01-15 10:32:11 | INFO    | Gemini client initialized — model: gemini-1.5-flash
2024-01-15 10:32:15 | INFO    | User message (turn 1): How do I start investing with ₹10,000...
2024-01-15 10:32:17 | INFO    | Response received | tokens: 45in/312out | latency: 1842ms
```

---

##  Security Best Practices

-  API key stored in `.env` (never committed to git)
-  `.env` added to `.gitignore`
-  Gemini safety filters enabled (all 4 harm categories)
-  No user PII stored in logs

---

##  Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | ≥1.32 | Web UI framework |
| `google-generativeai` | ≥0.5 | Gemini API SDK |
| `python-dotenv` | ≥1.0 | Secure env var loading |
| `loguru` | ≥0.7 | Structured logging |

---

##  Disclaimer

FinBot provides **general financial education** and is not a substitute for professional financial advice. Always consult a certified financial planner (CFP) for decisions specific to your financial situation.

---

*Built as part of the Innomatics Research Labs AI/ML program.*

* You can also check the app deployment. *
Hugging Face deployment : https://huggingface.co/spaces/Mohanasree-2/Financial_Chatbot 
