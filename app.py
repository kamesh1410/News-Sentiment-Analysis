# app.py (Updated with Error Handling)
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter, defaultdict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from gtts import gTTS
import gradio as gr
import os
import tempfile

# Ensure NLTK data is downloaded
def download_nltk_data():
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('vader_lexicon', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        return True
    except Exception as e:
        print(f"NLTK download failed: {e}")
        return False

download_nltk_data()

# Summarize Text Function
def summarize_text(text, num_sentences=2):
    if not text.strip():
        return "No content to summarize."
    sentences = sent_tokenize(text)
    if len(sentences) <= num_sentences:
        return text.strip()
    stop_words = set(stopwords.words("english"))
    words = [word.lower() for word in word_tokenize(text) if word.isalnum() and word.lower() not in stop_words]
    word_freq = defaultdict(int)
    for word in words:
        word_freq[word] += 1
    sentence_scores = defaultdict(int)
    for sentence in sentences:
        for word, freq in word_freq.items():
            if word in sentence.lower():
                sentence_scores[sentence] += freq
    summary_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
    return " ".join(summary_sentences).strip()

# Fetch News Articles
def fetch_news_articles(company_name):
    search_url = f"https://news.google.com/rss/search?q={company_name}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(search_url, headers=headers, timeout=5)
        if response.status_code != 200:
            return {"error": f"Failed to fetch news (Status: {response.status_code})"}
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")[:10]
        articles = []
        for item in items:
            title = item.title.text.strip()
            link = item.link.text
            pub_date = item.pubDate.text if item.pubDate else "N/A"
            description = item.description.text if item.description else ""
            description = BeautifulSoup(description, "html.parser").get_text().strip()
            if not description or description == title:
                summary = fetch_summary_from_link(link)
            else:
                for separator in [" - ", " | "]:
                    if separator in description:
                        description = description.split(separator, 1)[-1].strip()
                sentences = sent_tokenize(description)
                summary = sentences[0] if sentences else description
            articles.append({
                "title": title,
                "summary": summary,
                "link": link,
                "pub_date": pub_date
            })
        return articles
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}"}

# Fetch Summary from Link
def fetch_summary_from_link(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return "No summary available"
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join(p.text.strip() for p in paragraphs[:3])
        if text:
            sentences = sent_tokenize(text)
            return sentences[0] if sentences else text
    except Exception as e:
        return f"Error fetching summary: {str(e)}"

# Process Articles with Sentiment
def process_articles(articles):
    for article in articles:
        article["sentiment"] = get_sentiment(article["summary"])
    return articles

# Get Sentiment
def get_sentiment(text):
    try:
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(text)
        compound = scores["compound"]
        if compound >= 0.05:
            return "Positive"
        elif compound <= -0.05:
            return "Negative"
        else:
            return "Neutral"
    except Exception as e:
        return f"Sentiment error: {str(e)}"

# Comparative Analysis
def comparative_analysis(articles):
    try:
        sentiments = [article["sentiment"] for article in articles]
        sentiment_dist = Counter(sentiments)
        stop_words = set(stopwords.words("english"))
        all_summaries = " ".join(article["summary"] for article in articles).lower()
        words = [word for word in word_tokenize(all_summaries) if word.isalnum() and word not in stop_words]
        common_topics = Counter(words).most_common(5)
        insights = []
        pos_articles = [a for a in articles if a["sentiment"] == "Positive"]
        neg_articles = [a for a in articles if a["sentiment"] == "Negative"]
        if pos_articles:
            pos_example = pos_articles[0]["title"]
            insights.append(f"Positive coverage (e.g., '{pos_example}') focuses on achievements or growth.")
        if neg_articles:
            neg_example = neg_articles[0]["title"]
            insights.append(f"Negative coverage (e.g., '{neg_example}') highlights challenges or controversies.")
        if sentiment_dist["Neutral"] > 0:
            insights.append(f"Neutral articles ({sentiment_dist['Neutral']}) provide factual updates.")
        report = {
            "Company": articles[0]["title"].split(" - ")[0].split(" ")[0],
            "Sentiment Distribution": dict(sentiment_dist),
            "Common Topics": [word for word, _ in common_topics],
            "Comparative Insights": insights
        }
        return report
    except Exception as e:
        return {"error": f"Comparative analysis error: {str(e)}"}

# Generate Hindi TTS with Temp File
def generate_hindi_tts(report):
    try:
        hindi_template = (
            "कंपनी: {}. "
            "भावना: सकारात्मक {}, नकारात्मक {}, तटस्थ {}. "
            "अंतर्दृष्टि: {}"
        )
        sent_dist = report["Sentiment Distribution"]
        positive = sent_dist.get("Positive", 0)
        negative = sent_dist.get("Negative", 0)
        neutral = sent_dist.get("Neutral", 0)
        insights = " ".join(report["Comparative Insights"])
        hindi_text = hindi_template.format(report["Company"], positive, negative, neutral, insights)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tts = gTTS(text=hindi_text, lang="hi", slow=False)
            tts.save(tmp.name)
            return tmp.name
    except Exception as e:
        return f"TTS error: {str(e)}"

# Process and Analyze with TTS
def process_and_analyze_with_tts(company):
    try:
        articles = fetch_news_articles(company)
        if "error" in articles:
            return articles, None, None
        processed_articles = process_articles(articles)
        report = comparative_analysis(processed_articles)
        if "error" in report:
            return {"error": report["error"]}, None, None
        audio_file = generate_hindi_tts(report)
        if isinstance(audio_file, str) and "error" in audio_file.lower():
            return {"error": audio_file}, None, None
        return processed_articles, report, audio_file
    except Exception as e:
        return {"error": f"Processing error: {str(e)}"}, None, None

# Gradio Process Function
def gradio_process(company, progress=gr.Progress()):
    progress(0, desc="Starting analysis...")
    progress(0.2, desc="Fetching news articles...")
    articles, report, audio_file = process_and_analyze_with_tts(company)
    if "error" in articles:
        progress(1.0, desc="Analysis failed.")
        return articles["error"], None, None
    progress(0.5, desc="Generating report...")
    output_text = f"### Processed {len(articles)} articles for {company}:\n\n"
    for i, article in enumerate(articles, 1):
        output_text += (
            f"**{i}. Title:** {article['title']}\n"
            f"**Summary:** {article['summary']}\n"
            f"**Sentiment:** {article['sentiment']}\n"
            f"**Link:** [{article['link']}]({article['link']})\n\n"
        )
    output_text += "### Comparative Analysis:\n"
    output_text += f"**Company:** {report['Company']}\n"
    output_text += "**Sentiment Distribution:**\n"
    for sent, count in report["Sentiment Distribution"].items():
        output_text += f"  {sent}: {count}\n"
    output_text += f"**Common Topics:** {', '.join(report['Common Topics'])}\n"
    output_text += "**Insights:**\n"
    for insight in report["Comparative Insights"]:
        output_text += f"  - {insight}\n"
    progress(0.8, desc="Generating audio summary...")
    progress(1.0, desc="Analysis complete.")
    return output_text, audio_file, articles

# Custom CSS
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
.gradio-container {
    background: linear-gradient(135deg, #f5f7fa, #c3cfe2);
    font-family: 'Roboto', sans-serif;
    padding: 20px;
    border-radius: 10px;
}
.dark .gradio-container {
    background: linear-gradient(135deg, #2c3e50, #34495e);
    color: #ffffff;
}
h1 {
    color: #4CAF50;
    text-align: center;
    font-weight: 700;
}
.dark h1 {
    color: #4CAF50;
}
.markdown-text {
    background-color: white;
    padding: 15px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    animation: fadeIn 1s ease-in-out;
}
.dark .markdown-text {
    background-color: #2c3e50;
    color: #ffffff;
}
.audio-player {
    margin-top: 20px;
    animation: fadeIn 1s ease-in-out;
}
button {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
button:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
.dark button {
    background-color: #4CAF50;
    color: white;
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
"""

# Gradio Interface
with gr.Blocks(css=custom_css) as demo:
    gr.Markdown("# News Summarization and Sentiment Analysis")
    gr.Markdown("Enter a company name to get a sentiment report and Hindi audio summary.")
    with gr.Row():
        with gr.Column():
            company_input = gr.Textbox(label="Enter Company Name", placeholder="e.g., Tesla", interactive=True)
            submit_button = gr.Button("Analyze", variant="primary")
        with gr.Column():
            pass
    with gr.Row():
        with gr.Column():
            output_markdown = gr.Markdown(label="Sentiment Report", elem_classes=["markdown-text"])
        with gr.Column():
            output_audio = gr.Audio(label="Hindi TTS Output", elem_classes=["audio-player"])
            output_json = gr.JSON(label="Raw Data (for debugging)", visible=False)
    examples = gr.Examples(
        examples=["Tesla", "Microsoft", "Apple"],
        inputs=[company_input],
        outputs=[output_markdown, output_audio, output_json],
        fn=gradio_process,
        cache_examples=True
    )
    submit_button.click(
        gradio_process,
        inputs=[company_input],
        outputs=[output_markdown, output_audio, output_json],
        show_progress=True
    )

if __name__ == "__main__":
    demo.launch()