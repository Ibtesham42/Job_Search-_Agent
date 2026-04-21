# 🧠 Job Search Agent (AI-Powered Job Extraction System)

An end-to-end **AI-powered job extraction system** that collects job listings from websites and PDFs, processes them using LLMs, and displays structured results via a web UI.

---

## 🚀 Features

* 🔍 Extract jobs from **web pages & PDFs**
* 🤖 AI-powered job parsing using LLM
* 🧹 Deduplication of job listings
* 💾 Store results in CSV
* 🌐 FastAPI backend
* 🖥️ Streamlit frontend UI
* 🔗 Input custom URLs directly from UI
* ⚡ Modular pipeline (Search → Crawl → Parse → Extract → Store → Display)

---

## 🏗️ Project Structure

```
job-agent/
│
├── backend/
│   ├── main.py          # FastAPI app
│   ├── pipeline.py      # Orchestrates flow
│   ├── extractor.py     # LLM extraction logic
│   ├── parser.py        # HTML/PDF parsing
│   ├── models.py        # Pydantic schema
│   └── storage.py       # Save results
│
├── frontend/
│   └── app.py           # Streamlit UI
│
├── data/
│   └── jobs.csv         # Output storage
│
├── .env.example         # Environment template
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/job-agent.git
cd job-agent
```

---

### 2️⃣ Create Virtual Environment (Python 3.10+)

```bash
python -m venv venv
```

#### Activate:

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

---

### 3️⃣ Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4️⃣ Setup Environment Variables

Create `.env` file:

```bash
cp .env.example .env
```

Then edit `.env`:

```
GROQ_API_KEY=your_groq_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

---

## 🔐 API Keys Required

* Groq → https://console.groq.com/keys
* Serper → https://serper.dev

---

## ▶️ Running the Application

### 🧠 Start Backend (FastAPI)

```bash
cd backend
uvicorn main:app --reload
```

Backend runs at:

```
http://127.0.0.1:8000
```

---

### 🖥️ Start Frontend (Streamlit)

Open new terminal:

```bash
cd frontend
streamlit run app.py
```

---

## 🧪 Usage

1. Open Streamlit UI
2. Paste URLs (one per line), for example:

```
https://amazon.jobs
https://careers.google.com
```

3. Click **Extract Jobs**

---

## 📊 Output Format

| Company | Job Title | Description | Location | Posted Date | Apply By | Apply Link | Source |
| ------- | --------- | ----------- | -------- | ----------- | -------- | ---------- | ------ |

---

## 🔁 Pipeline Flow

```
Input URLs
   ↓
Crawl (Fetch HTML/PDF)
   ↓
Parse Content
   ↓
Extract Jobs (LLM)
   ↓
Deduplicate
   ↓
Store (CSV)
   ↓
Display (UI)
```

---

## ⚠️ Notes

* Only extracts **real job data**
* Missing fields → `NULL`
* Avoids duplicates
* Works best with:

  * Career pages
  * Govt job PDFs
  * Job listing sites

---

## 🧩 Future Improvements

* 🗄️ PostgreSQL integration
* 🔐 User authentication
* 🤖 Job recommendation engine
* 📊 Resume-job matching
* ☁️ Deployment (AWS / Render)

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first.

---

## 📄 License

MIT License

---

## 👨‍💻 Author

Ibteshm Akhtar
