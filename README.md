# LLM-powered-chatbot-for-Indian-Government-Schemes

A **Large Language Model (LLM) powered chatbot** designed to provide information on **Government Schemes** with a focus on accessibility, transparency, and user-friendliness.  
This project integrates **Retrieval-Augmented Generation (RAG)** with **Pinecone** and **Django** to allow users to query about schemes and receive context-aware, accurate responses.

---

## 🚀 Features

- **Conversational Chatbot Interface** – Ask natural language questions about government schemes.  
- **RAG Pipeline** – Uses embeddings + Pinecone vector database for context retrieval.  
- **LLM Integration** – Generates responses based on retrieved scheme data.  
- **User-Friendly Web UI** – Built with Django + HTML/CSS for interaction.  
- **Extensible** – Easily connect to APIs.  
- **Scalable Backend** – Ready for deployment on cloud platforms .  

---

## 🏗️ Project Structure

```
gov_scheme_project/
│
├── manage.py
├── db.sqlite3
├── rag.py
├── initialize.py
├── schemeData.json
├── rag.jsonl
│
├── govSchemeProj/                # Main project settings folder
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│
├── chat/                         # App for chat functionality
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   │   └── __init__.py
│   └── templates/
│       └── chat/
│           ├── home.html
│           └── chatStart.html
│
├── requirements.txt        
├── .gitignore
└── README.md
```

---

## ⚙️ Tech Stack

- **Backend & Frontend**: Django (Python, Django Templates with HTML/CSS/JS) 
- **LLM Integration**: HuggingFace / OpenAI API / Ollama
- **RAG Storage**: Pinecone (Vector DB)  

---

## 📦 Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/yourusername/govscheme-llm-chatbot.git
cd govscheme-llm-chatbot
```

### 2️⃣ Setup Python environment
```bash
python3 -m venv venv
source venv/bin/activate   # On Mac/Linux
venv\Scripts\activate      # On Windows
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Setup Django
```bash
python manage.py migrate
python manage.py runserver
```

---

## 🧑‍💻 Usage

### 1. Run **initialize.py** to fetch all government scheme data
```bash
python initialize.py
```
This will create/update `schemeData.json` with the latest schemes.

---

### 2. Run **rag.py** to preprocess, chunk, and upsert data into Pinecone
```bash
python rag.py
```
This will generate `rag.jsonl` and insert scheme chunks into the Pinecone vector database.

---

### 3. Start the Django chatbot server
```bash
python manage.py runserver
```
<<<<<<< Updated upstream
Then open your browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/) 🎉
=======
Then open your browser at http://127.0.0.1:8000/
>>>>>>> Stashed changes

---

## 📊 Example Queries

- *“What financial assistance schemes are available for women entrepreneurs?”*  
- *“List pension schemes for senior citizens in India.”*  
- *“Eligibility for scholarships for differently abled students in Puducherry.”*  

---

## 📌 Roadmap

- Improve scheme dataset coverage (all states + central schemes).  
- Add multilingual support (Hindi, Marathi, Tamil, etc.).  
- Deploy chatbot on cloud with Docker & CI/CD.  
- Add voice-based query input.  

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📜 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.
