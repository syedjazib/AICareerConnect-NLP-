# NLP AI Career Connect

An AI-powered recruitment and career optimization ecosystem designed to bridge the gap between job seekers and industry demands. Leveraging Natural Language Processing (NLP) and machine learning methodologies, this system intelligently parses resumes, extracts key technical competencies, matches candidates with optimal career pathways, and generates automated insights.

---

## 🚀 Key Features

*   **Intelligent Resume Parsing:** Extracts unstructured text data from resumes and structures it into standardized JSON payloads.
*   **NLP Semantic Matching:** Employs advanced text embedding and semantic similarity algorithms to match applicant profiles with live job descriptions.
*   **Skill Gap Analysis:** Automatically cross-references candidate skill matrices against target job profiles to highlight missing credentials and recommend learning paths.
*   **Automated Interview Insights:** Leverages generative workflows to construct tailored, role-specific interview preparation questions based on candidate experience profiles.

---

## 🛠️ Tech Stack

*   **Core Language:** Python 3.10+
*   **NLP & ML Frameworks:** Scikit-Learn, NLTK, Spacy, Hugging Face Transformers
*   **Data Manipulation & Viz:** Pandas, NumPy, Matplotlib, Seaborn
*   **Development Environment:** Google Colab / Jupyter Notebooks
*   **Version Control:** Git & GitHub

---

## 📂 Project Structure

```text
nlp-ai-career-connect/
│
├── data/                       # Dataset directories
│   ├── raw/                    # Raw sample resumes and job posts
│   └── processed/              # Normalized and tokenized text data
│
├── models/                     # Saved model weights and vectorized vocabularies
│
├── notebooks/                  # Interactive development files
│   └── nlp_career_connect.ipynb # Core Google Colab analytical notebook
│
├── src/                        # Modular source code
│   ├── __init__.py
│   ├── preprocessing.py        # Tokenization, lemmatization, and text cleaning
│   ├── extraction.py           # Named Entity Recognition (NER) for skill harvesting
│   └── matcher.py              # Cosine similarity and ranking algorithms
│
├── .gitignore                  # Tracking exemptions (data, envs, cache)
├── README.md                   # Project documentation
└── requirements.txt            # Operational dependencies


## ⚙️ Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/nlp-ai-career-connect.git
   cd nlp-ai-career-connect

## Establish a Virtual Environment:

```text
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
