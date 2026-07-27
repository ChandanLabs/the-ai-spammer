# 🤖 Placement Compliance & Nudge Bot

> An automated platform that uploads student CSVs, links Telegram accounts, and sends AI-generated escalating reminders until every student registers — or the deadline passes.

---

## ✨ Features

- **CSV Upload** — Drag-and-drop student lists (name, roll_no, email, branch, year, phone)
- **Hiring Drives** — Create drives with company name, registration link, and deadline
- **Telegram Bot** — Deep-link (`/start ROLL_NO`) or manual roll-number entry to link students
- **3-Level AI Nudging** — APScheduler runs every 30 min and escalates messages:
  - 🟢 **Level 1** (count 0–1): Polite friendly reminder
  - 🟡 **Level 2** (count 2–4): Urgent, deadline-focused message
  - 🔴 **Level 3** (count 5+): FOMO — "your peers are already registered!"
- **Admin Dashboard** — Real-time stats, registration progress, manual trigger button
- **Nudge Logs** — Full message history with level badge and expandable text

---

## 🗂️ Project Structure

```
the-ai-spammer/
├── backend/
│   ├── main.py                   # FastAPI entrypoint (runs on :8000)
│   ├── config.py                 # Settings from .env
│   ├── models/
│   │   ├── database.py           # SQLAlchemy + SQLite setup
│   │   ├── schemas.py            # ORM models: HiringDrive, Student, NudgeLog
│   │   └── __init__.py
│   ├── routers/
│   │   ├── admin.py              # All admin API endpoints
│   │   └── bot_webhook.py        # Telegram bot logic
│   ├── services/
│   │   ├── nudge_engine.py       # Gemini/OpenAI message generation
│   │   ├── scheduler.py          # APScheduler nudge loop
│   │   └── csv_parser.py         # Pandas CSV cleaner
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx            # Root layout with sidebar
│   │   ├── dashboard/page.tsx    # KPI cards + quick upload
│   │   ├── students/page.tsx     # Student table with filters
│   │   ├── drives/page.tsx       # Hiring drives CRUD
│   │   └── logs/page.tsx         # Nudge log viewer
│   ├── components/
│   │   ├── Sidebar.tsx
│   │   └── UploadZone.tsx        # Drag-and-drop CSV component
│   ├── lib/api.ts                # Typed API client
│   └── package.json
│
├── sample_students.csv           # Test data — 10 sample students
└── README.md
```

---

## 🗄️ Database Schema

### `hiring_drives`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `company_name` | String | e.g. "Google" |
| `registration_link` | String | Optional URL |
| `deadline` | DateTime | When nudging stops |
| `is_active` | Boolean | Default: True |

### `students`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `drive_id` | FK → HiringDrive | Optional |
| `name` | String | |
| `roll_number` | String | Unique, indexed |
| `email / branch / year / phone` | String | Optional |
| `telegram_chat_id` | BigInt | Filled when student starts bot |
| `status` | Enum | `PENDING` · `REGISTERED` · `BLOCKED` |
| `nudge_count` | Integer | Increments each successful nudge |
| `last_nudge_sent_at` | DateTime | |

### `nudge_logs`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `student_id / drive_id` | FK | |
| `message_sent` | Text | Full AI-generated message |
| `nudge_level` | Integer | 1=Polite, 2=Urgent, 3=FOMO |
| `sent_at` | DateTime | |
| `status` | String | `sent` or `failed` |

---

## 🚀 Quick Start

### Step 1 — Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env — add your TELEGRAM_BOT_TOKEN and GEMINI_API_KEY

# Start FastAPI server
python -m uvicorn backend.main:app --reload --port 8000
```

FastAPI Swagger docs → http://localhost:8000/docs

### Step 2 — Telegram Bot (separate terminal)

```bash
cd backend
venv\Scripts\activate
python -m backend.routers.bot_webhook
```

### Step 3 — Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Dashboard → http://localhost:3000

---

## 🔧 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | From [@BotFather](https://t.me/BotFather) |
| `GEMINI_API_KEY` | ✅ | From [Google AI Studio](https://aistudio.google.com) |
| `AI_PROVIDER` | | `gemini` (default) or `openai` |
| `OPENAI_API_KEY` | | If using OpenAI |
| `NUDGE_INTERVAL_MINUTES` | | Default: 30 |
| `DATABASE_URL` | | Default: `sqlite:///./placement.db` |

---

## 🤖 Telegram Bot Commands

| Command | Description |
|---|---|
| `/start` | Link your roll number (also supports deep link: `t.me/YourBot?start=ROLL_NO`) |
| `/status` | Check registration status, drive info, nudge count |
| `/help` | Show available commands |

### Deep Link Flow
1. Admin generates link: `https://t.me/YourBot?start=CS2021001`
2. Student clicks → bot extracts roll number → matches DB → marks REGISTERED
3. Student never needs to type anything

---

## 📡 API Reference

All endpoints are prefixed with `/api/admin`:

| Method | Path | Description |
|---|---|---|
| `GET` | `/stats` | Dashboard KPIs |
| `GET/POST` | `/drives` | List / create hiring drives |
| `PATCH/DELETE` | `/drives/{id}` | Update / delete a drive |
| `GET` | `/students` | List students (filterable) |
| `PATCH` | `/students/{id}` | Update student status |
| `POST` | `/upload-csv` | Upload CSV (with optional drive_id) |
| `GET` | `/logs` | List nudge logs |
| `POST` | `/nudge/trigger` | Manually trigger nudge job |

---

## 🧪 Testing the Full Flow

1. Start backend + bot + frontend
2. Go to **Drives** → Create a drive with a deadline 24h from now
3. Go to **Dashboard** → Upload `sample_students.csv` → assign to the drive
4. Open Telegram → start your bot → enter a roll number from the CSV
5. Check **Students** page → student status should be `REGISTERED`
6. Click **Trigger Nudge Now** on dashboard
7. Check **Nudge Logs** → see the AI message that was generated

---

## 📦 CSV Format

Minimum required columns:
```csv
name,roll_no,email,branch,year,phone
Aarav Sharma,CS2021001,aarav@college.edu,CSE,3rd,9876543210
```

Aliases supported: `roll_no` = `roll_number`, `mobile` = `phone`, `department` = `branch`
