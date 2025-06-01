# Fake News Detection System

## Description
This is a Streamlit web application that analyzes the trustworthiness of news articles using graph-based insights. It evaluates news content by examining:
- The credibility of the source website
- External citations and references
- Content similarity with other sources
- Network relationships between referenced sites

## Key Features
- Web scraping of news articles and their citations
- NLP processing to extract and compare keywords
- Graph algorithms to analyze site relationships
- Interactive visualization of trust networks
- Final trust score calculation
- Top referenced sites analysis

## How It Works
1. Input a news article URL
2. The system scrapes the article content and external citations
3. Processes the text to extract key terms and concepts
4. Builds a graph of referenced sites and their relationships
5. Calculates trust scores based on:
   - Source credibility (from data.csv)
   - Citation quality
   - Content similarity
6. Visualizes the network and provides a final trust score

## Installation
1. Clone this repository
2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   streamlit run main.py
   ```

## Dependencies
- Python 3.x
- Streamlit
- BeautifulSoup
- NLTK
- Requests
- Pandas
- Network visualization libraries

## File Structure
```
- main.py: Main application logic and Streamlit interface
- web_scrapper.py: Web scraping functionality
- Tokenizer_Trie.py: NLP processing and text analysis
- data.csv: Trust scores for known news sources
- cpp/: C++ implementation components
- lib/: JavaScript visualization libraries
```

## Usage
1. Run the application:
   ```bash
   streamlit run main.py
   ```
2. Enter a news article URL in the input field
3. View the interactive visualization of referenced sites
4. See the calculated trust score and top referenced sites
5. Click "Analyze another URL" to evaluate a different article

## Notes
- The system works best with English-language news articles
- Some news sites may block automated scraping
- Results should be considered as supplementary information, not absolute truth
