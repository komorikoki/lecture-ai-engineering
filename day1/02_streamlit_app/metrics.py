# metrics.py
import streamlit as st
import nltk
from janome.tokenizer import Tokenizer
import re
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# NLTK helper functions (with fallback on error)
try:
    nltk.download('punkt', quiet=True)
    from nltk.translate.bleu_score import sentence_bleu as nltk_sentence_bleu
    from nltk.tokenize import word_tokenize as nltk_word_tokenize
    print("NLTK loaded successfully.")  # For debugging
except Exception as e:
    st.warning(f"An error occurred during NLTK initialization: {e}\nUsing simplified fallback functions.")
    def nltk_word_tokenize(text):
        return text.split()
    def nltk_sentence_bleu(references, candidate):
        # Simplified BLEU score (exact/partial match)
        ref_words = set(references[0])
        cand_words = set(candidate)
        common_words = ref_words.intersection(cand_words)
        precision = len(common_words) / len(cand_words) if cand_words else 0
        recall = len(common_words) / len(ref_words) if ref_words else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        return f1  # Return F1 score as a simplified alternative

def initialize_nltk():
    """Function to attempt downloading NLTK data"""
    try:
        nltk.download('punkt', quiet=True)
        print("NLTK Punkt data checked/downloaded.")  # For debugging
    except Exception as e:
        st.error(f"Failed to download NLTK data: {e}")

def calculate_metrics(answer, correct_answer):
    """Calculate evaluation metrics from the answer and correct answer"""
    word_count = 0
    bleu_score = 0.0
    similarity_score = 0.0
    relevance_score = 0.0

    if not answer:  # Do not calculate if there is no answer
        return bleu_score, similarity_score, word_count, relevance_score

    # Count the number of words
    tokenizer = Tokenizer()
    tokens = list(tokenizer.tokenize(answer))  # Convert iterator to list
    word_count = len(tokens)

    # Calculate BLEU and similarity only if there is a correct answer
    if correct_answer:
        answer_lower = answer.lower()
        correct_answer_lower = correct_answer.lower()

        # Calculate BLEU score
        try:
            reference = [nltk_word_tokenize(correct_answer_lower)]
            candidate = nltk_word_tokenize(answer_lower)
            # Prevent division by zero
            if candidate:
                bleu_score = nltk_sentence_bleu(reference, candidate, weights=(0.25, 0.25, 0.25, 0.25))  # 4-gram BLEU
            else:
                bleu_score = 0.0
        except Exception as e:
            # st.warning(f"BLEU score calculation error: {e}")
            bleu_score = 0.0  # Default to 0 on error

        # Calculate cosine similarity
        try:
            vectorizer = TfidfVectorizer()
            # fit_transform expects a list, so pass as a list
            if answer_lower.strip() and correct_answer_lower.strip():  # Ensure non-empty strings
                tfidf_matrix = vectorizer.fit_transform([answer_lower, correct_answer_lower])
                similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            else:
                similarity_score = 0.0
        except Exception as e:
            # st.warning(f"Similarity score calculation error: {e}")
            similarity_score = 0.0  # Default to 0 on error

        # Calculate relevance score (based on keyword match rate)
        try:
            answer_words = set(re.findall(r'\w+', answer_lower))
            correct_words = set(re.findall(r'\w+', correct_answer_lower))
            if len(correct_words) > 0:
                common_words = answer_words.intersection(correct_words)
                relevance_score = len(common_words) / len(correct_words)
            else:
                relevance_score = 0.0
        except Exception as e:
            # st.warning(f"Relevance score calculation error: {e}")
            relevance_score = 0.0  # Default to 0 on error

    return bleu_score, similarity_score, word_count, relevance_score

def get_metrics_descriptions():
    """Return descriptions of evaluation metrics"""
    return {
        "Accuracy Score (is_correct)": "Evaluate the accuracy of the answer on a 3-point scale: 1.0 (accurate), 0.5 (partially accurate), 0.0 (inaccurate)",
        "Response Time (response_time)": "Time taken to get an answer after asking a question (in seconds). Represents model efficiency.",
        "BLEU Score (bleu_score)": "A machine translation evaluation metric that measures n-gram overlap between the correct answer and the response (value between 0 and 1, higher is better).",
        "Similarity Score (similarity_score)": "Semantic similarity between the correct answer and the response, calculated using cosine similarity of TF-IDF vectors (value between 0 and 1).",
        "Word Count (word_count)": "The number of words in the response. Indicates the amount of information or detail.",
        "Relevance Score (relevance_score)": "Proportion of common words between the correct answer and the response. Represents topic relevance (value between 0 and 1).",
        "Efficiency Score (efficiency_score)": "Accuracy divided by response time. Higher scores indicate faster and more accurate responses."
    }