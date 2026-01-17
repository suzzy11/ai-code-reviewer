# AI Code Reviewer

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![AI/NLP](https://img.shields.io/badge/AI--NLP-enabled-brightgreen) ![LLM](https://img.shields.io/badge/LLM-GPT%2C%20Configurable-yellow) ![Status](https://img.shields.io/badge/Status-Active-blueviolet) ![License](https://img.shields.io/badge/License-MIT-green)

## Project Description

**AI Code Reviewer** is a Python-based, Streamlit-powered application designed to automatically analyze Python source files, detect missing docstrings, generate baseline documentation, and report code coverage. It leverages advanced Natural Language Processing (NLP) and configurable Large Language Models (LLMs) to assist developers in improving code quality and documentation practices locally and in workflows. ([GitHub][1])

This tool can be used as a local desktop application, integrated into development environments, and is suitable for demonstrating AI and coding skills for **Infosys certification** or similar professional evaluations.

---

## Features

* Parse Python files and extract structural components. ([GitHub][1])
* Detect missing docstrings in functions, classes, and modules. ([GitHub][1])
* Generate baseline documentation using AI-powered text generation. ([GitHub][1])
* Analyze code coverage and compile coverage reports. ([GitHub][1])
* Interactive UI through **Streamlit** for easy use. ([GitHub][1])

---

## Techniques Used

### Natural Language Processing (NLP)

* Utilizes NLP to interpret code context and generate meaningful descriptions.
* Helps bridge code semantics with human-readable documentation.

### Prompt Engineering

* Custom prompts are designed to structure AI requests for concise code summaries and docstring suggestions.
* Prompts are adaptable based on project needs.

### LLM-based Text Generation

* Integrates configurable transformer-based LLMs for generating insights, comments, and documentation.
* You can switch or configure models such as OpenAI GPT variants or other compatible LLMs.

---

## Tech Stack

### Programming Language

* Python

### Libraries / Frameworks

* Streamlit (for UI)
* Coverage / parsing libraries (as defined in `requirements.txt`) ([GitHub][1])

### AI / ML Technologies

* Natural Language Processing (NLP)
* Transformer-based LLMs (e.g., GPT-family)

### LLM Details

* **Transformer-based LLMs** are used for text and documentation generation.
* **Configurable LLM model support** lets you choose the model and parameters best suited to your environment and performance goals.

---

## Project Structure

```
ai-code-reviewer/
├── .devcontainer
├── cli
├── core
├── examples
├── src
├── storage
├── temp_uploads
├── tests
├── .gitignore
├── requirements.txt
└── README.md
```

*(Output structure inferred from repository contents.)* ([GitHub][1])

---

## Installation Steps

1. **Clone the repository**

   ```
   git clone https://github.com/suzzy11/ai-code-reviewer.git
   cd ai-code-reviewer
   ```
2. **Create and activate a virtual environment**

   ```
   python3 -m venv venv
   source venv/bin/activate      # macOS/Linux
   venv\Scripts\activate         # Windows
   ```
3. **Install dependencies**

   ```
   pip install -r requirements.txt
   ```

---

## How to Run the Project Locally

1. Activate the virtual environment (if not already active).
2. Run the Streamlit app:

   ```
   streamlit run src/app.py
   ```
3. Open your browser and navigate to `http://localhost:8501`.
4. Upload Python files to analyze, and view generated documentation and coverage reports.

---

## Certification Use Case

This project is ideal for demonstrating skills in Python programming, AI/ML, NLP, and LLM integration for code analysis and documentation — useful for portfolio reviews or **Infosys certification submissions**. It showcases the ability to combine AI technologies with software development practices to deliver a practical engineering solution.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](https://github.com/suzzy11/ai-code-reviewer/blob/main/LICENSE) file for details. ([GitHub][1])

[1]: https://github.com/suzzy11/ai-code-reviewer "GitHub - suzzy11/ai-code-reviewer: A Streamlit-based AI Code Reviewer that parses Python files, detects missing docstrings, generates baseline documentation, and reports code coverage."
