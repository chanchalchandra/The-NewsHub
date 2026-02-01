from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from newspaper import Article
import nltk
from nltk import sent_tokenize, word_tokenize, pos_tag, ne_chunk
from nltk.chunk import tree2conlltags
import random
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Download required NLTK data
try:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')
    logger.info("NLTK data downloaded successfully")
except Exception as e:
    logger.error(f"Error downloading NLTK data: {str(e)}")

def extract_key_info(text):
    try:
        # Tokenize and tag the text
        sentences = sent_tokenize(text)
        entities = []
        
        for sentence in sentences:
            # Get named entities
            tokens = word_tokenize(sentence)
            tagged = pos_tag(tokens)
            chunks = ne_chunk(tagged)
            entities.extend([(chunk.leaves()[0][0], chunk.label()) for chunk in chunks if isinstance(chunk, nltk.Tree)])
        
        return {
            'sentences': sentences,
            'entities': entities
        }
    except Exception as e:
        logger.error(f"Error in extract_key_info: {str(e)}")
        raise

def generate_question_from_sentence(sentence, entities, all_sentences):
    try:
        # Templates for questions
        templates = [
            "What is mentioned in the article about {}?",
            "According to the article, what happened regarding {}?",
            "The article discusses {} in relation to what?",
            "Which of the following is true about {}?",
            "What does the article state about {}?"
        ]
        
        # Generate wrong options
        def generate_wrong_options(correct_answer, all_sentences):
            wrong_options = []
            other_sentences = [s for s in all_sentences if s != sentence]
            
            # Take parts of other sentences or modify the correct answer slightly
            if other_sentences:
                wrong_options.extend(random.sample(other_sentences, min(2, len(other_sentences))))
            
            # Add some generic wrong answers if we need more
            generic_wrong = [
                "This was not mentioned in the article",
                "The article states the opposite",
                "None of the above",
                "This is incorrect according to the article"
            ]
            
            while len(wrong_options) < 3:
                wrong_options.append(random.choice(generic_wrong))
            
            return wrong_options[:3]

        # Try to generate a question using named entities
        for entity, entity_type in entities:
            if entity.lower() in sentence.lower():
                question = random.choice(templates).format(entity)
                wrong_options = generate_wrong_options(sentence, all_sentences)
                
                return {
                    "question": question,
                    "options": [sentence] + wrong_options,
                    "correct_answer": sentence,
                    "explanation": f"This is directly stated in the article regarding {entity}."
                }
        
        # Fallback: Use the first noun or important word
        words = word_tokenize(sentence)
        tagged = pos_tag(words)
        for word, tag in tagged:
            if tag.startswith('NN'):  # If it's a noun
                question = random.choice(templates).format(word)
                wrong_options = generate_wrong_options(sentence, all_sentences)
                
                return {
                    "question": question,
                    "options": [sentence] + wrong_options,
                    "correct_answer": sentence,
                    "explanation": f"This information about {word} is directly stated in the article."
                }
        
        # Final fallback
        question = "Which of the following statements is true according to the article?"
        wrong_options = generate_wrong_options(sentence, all_sentences)
        
        return {
            "question": question,
            "options": [sentence] + wrong_options,
            "correct_answer": sentence,
            "explanation": "This statement is directly quoted from the article."
        }
    except Exception as e:
        logger.error(f"Error in generate_question_from_sentence: {str(e)}")
        raise

@app.route('/')
def index():
    try:
        return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'summarizer.html')
    except Exception as e:
        logger.error(f"Error serving index: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/<path:filename>')
def serve_file(filename):
    try:
        return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename)
    except Exception as e:
        logger.error(f"Error serving file {filename}: {str(e)}")
        return jsonify({'error': str(e)}), 404

@app.route('/summarize', methods=['POST'])
def summarize_article():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({'error': 'No JSON data received'}), 400
            
        url = data.get('url')
        if not url:
            logger.error("URL is required")
            return jsonify({'error': 'URL is required'}), 400

        logger.info(f"Attempting to summarize: {url}")
        
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()
        
        summary = article.summary
        if not summary:
            logger.error("Could not generate summary")
            return jsonify({'error': 'Could not generate summary'}), 500
            
        result = {
            'title': article.title,
            'summary': summary,
            'authors': article.authors,
            'publish_date': str(article.publish_date) if article.publish_date else None
        }
        
        logger.info(f"Successfully summarized article: {article.title}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in summarize_article: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({'error': 'No JSON data received'}), 400
            
        summary = data.get('summary')
        if not summary:
            logger.error("Summary is required")
            return jsonify({'error': 'Summary is required'}), 400

        logger.info("Received quiz generation request")
        
        # Extract key information from the summary
        info = extract_key_info(summary)
        logger.info(f"Extracted {len(info['sentences'])} sentences and {len(info['entities'])} entities")
        
        if not info or not info['sentences']:
            logger.error("Could not extract sentences from summary")
            return jsonify({'error': 'Could not extract sentences from summary'}), 400
            
        sentences = info['sentences']
        entities = info['entities']
        
        # Generate 5 questions
        questions = []
        used_sentences = set()
        
        # Try to generate questions from sentences with named entities first
        for sentence in sentences:
            if len(questions) >= 5:
                break
                
            if sentence not in used_sentences:
                question = generate_question_from_sentence(sentence, entities, sentences)
                if question:
                    questions.append(question)
                    used_sentences.add(sentence)
        
        # If we need more questions, use remaining sentences
        remaining_sentences = [s for s in sentences if s not in used_sentences]
        while len(questions) < 5 and remaining_sentences:
            sentence = random.choice(remaining_sentences)
            remaining_sentences.remove(sentence)
            question = generate_question_from_sentence(sentence, entities, sentences)
            if question:
                questions.append(question)
        
        logger.info(f"Generated {len(questions)} questions")
        
        # Ensure we have at least one question
        if not questions:
            logger.warning("No questions generated, using fallback question")
            first_sentence = sentences[0] if sentences else summary
            questions.append({
                "question": "Which of the following statements is true according to the article?",
                "options": [first_sentence, "This was not mentioned in the article", "The article states something different", "None of the above"],
                "correct_answer": first_sentence,
                "explanation": "This statement is directly quoted from the article."
            })
            
        return jsonify({
            'questions': questions
        })
            
    except Exception as e:
        logger.error(f"Error in generate_quiz: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 