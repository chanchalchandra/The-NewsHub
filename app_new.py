from flask import Flask, request, jsonify
from flask_cors import CORS
from newspaper import Article
import nltk

app = Flask(__name__)
CORS(app)

# Download required NLTK data
nltk.download('punkt')

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/summarize', methods=['POST'])
def summarize_article():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Create an Article object
        article = Article(url)
        
        # Download and parse the article
        article.download()
        article.parse()
        
        # Perform natural language processing
        article.nlp()
        
        # Get the summary
        summary = article.summary
        
        return jsonify({
            'title': article.title,
            'summary': summary,
            'authors': article.authors,
            'publish_date': str(article.publish_date) if article.publish_date else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 