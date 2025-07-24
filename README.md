# Research Collider

An AI-powered research matching tool that helps find professors with research interests matching your query using semantic search and OpenAI embeddings.

## Features

- **Semantic Search**: Uses OpenAI embeddings to find relevant professors based on research interests
- **AI-Generated Summaries**: Provides explanations for why each professor matches your query
- **Vector Database**: ChromaDB for efficient similarity search
- **Web Interface**: Clean Streamlit interface for easy interaction

## Setup Instructions

### Prerequisites
- Python 3.11+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Adamcaon/ReaserchCollider.git
cd ReaserchCollider
```

2. Install dependencies:
```bash
pip install -r requirements_minimal.txt
```

3. Configure OpenAI API key:
   - Create `.streamlit/secrets.toml` file
   - Add your OpenAI API key:
```toml
OPENAI_API_KEY = "your-openai-api-key-here"
```

4. Run the application:
```bash
streamlit run main.py
```

5. Open your browser and go to `http://localhost:8501`

## Usage

1. Enter your research interests in the text area (minimum 20 words)
2. Click "Search" to find matching professors
3. Review the AI-generated summaries explaining why each professor matches your query

## Files Description

- `main.py`: Main Streamlit application
- `web.py`: Web scraper for professor data
- `Data.csv`: Professor metadata
- `combined.json`: CV text data
- `requirements_minimal.txt`: Core dependencies for local setup
- `requirements.txt`: Full dependencies list

## Data

The application searches through professor data from the Association of Chinese Professors at WashU, including:
- Professor names and contact information
- Department and school affiliations
- CV content and research interests

## Technologies Used

- **Streamlit**: Web interface
- **OpenAI**: Embeddings and chat completions
- **LangChain**: Document processing and retrieval
- **ChromaDB**: Vector database
- **BeautifulSoup**: Web scraping
- **Pandas**: Data processing
