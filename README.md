# News Summarization and Sentiment Analysis

## Description
This project fetches news articles from Google News RSS feeds, summarizes them, performs sentiment analysis, and generates an audio summary in Hindi. It uses a Gradio interface to provide an interactive experience for analyzing news about a specified company, offering insights into sentiment distribution, common topics, and comparative analysis. The app is deployed on Hugging Face Spaces for public access.

## Live Demo
Try the app on Hugging Face Spaces:  
[https://huggingface.co/spaces/Kamesh14/News-Sentiment-Analysis](https://huggingface.co/spaces/Kamesh14/News-Sentiment-Analysis)

## Installation
To run this project locally, follow these steps:

1. **Clone the Repository:**
2. **Install Dependencies:**
Ensure you have Python 3.9+ installed. Then, install the required libraries:
3. **Run the Application:**The Gradio interface will launch at `http://127.0.0.1:7860`.

## Usage
1. Open the app in a web browser (local URL or deployed Space).
2. Enter a company name (e.g., "Tesla") in the textbox.
3. Click "Analyze" to process the request.
4. View the results:
   - **Sentiment Report:** Article titles, summaries, sentiments, and links.
   - **Hindi TTS Output:** An audio summary in Hindi.
   - **Raw Data:** JSON output for debugging (hidden by default).

## Files
- `app.py`: Main application script with Gradio interface and logic.
- `requirements.txt`: List of Python dependencies.
- `README.md`: Project documentation.
- `LICENSE`: MIT License file.
- `thumbnail.png`: Thumbnail image for the project.

## Limitations
- Summaries rely on Google News RSS descriptions, which may be limited. Fallback scraping (basic HTML parsing) is used when needed.
- Hindi audio includes English insights due to time constraints on translation.
- Processes only the top 10 articles per request for performance.

## License
This project is licensed under the MIT License.
