# database.py
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st
from config import DB_FILE
from metrics import calculate_metrics  # Required for calculating metrics

# --- Schema Definition ---
TABLE_NAME = "chat_history"
SCHEMA = f'''
CREATE TABLE IF NOT EXISTS {TABLE_NAME}
(id INTEGER PRIMARY KEY AUTOINCREMENT,
 timestamp TEXT,
 question TEXT,
 answer TEXT,
 feedback TEXT,
 correct_answer TEXT,
 is_correct REAL,      -- Changed from INTEGER to REAL (to allow 0.5)
 response_time REAL,
 bleu_score REAL,
 similarity_score REAL,
 word_count INTEGER,
 relevance_score REAL)
'''

# --- Database Initialization ---
def init_db():
    """Initialize the database and table"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(SCHEMA)
        conn.commit()
        conn.close()
        print(f"Database '{DB_FILE}' initialized successfully.")
    except Exception as e:
        st.error(f"Failed to initialize the database: {e}")
        raise e  # Re-raise the error to stop the app or handle it appropriately

# --- Data Manipulation Functions ---
def save_to_db(question, answer, feedback, correct_answer, is_correct, response_time):
    """Save chat history and evaluation metrics to the database"""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate additional evaluation metrics
        bleu_score, similarity_score, word_count, relevance_score = calculate_metrics(
            answer, correct_answer
        )

        c.execute(f'''
        INSERT INTO {TABLE_NAME} (timestamp, question, answer, feedback, correct_answer, is_correct,
                                 response_time, bleu_score, similarity_score, word_count, relevance_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, question, answer, feedback, correct_answer, is_correct,
             response_time, bleu_score, similarity_score, word_count, relevance_score))
        conn.commit()
        print("Data saved to DB successfully.")  # For debugging
    except sqlite3.Error as e:
        st.error(f"An error occurred while saving to the database: {e}")
    finally:
        if conn:
            conn.close()

def get_chat_history():
    """Retrieve all chat history from the database"""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        # Since is_correct is of type REAL, read it accordingly
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME} ORDER BY timestamp DESC", conn)
        # Check the data type of the is_correct column and convert if necessary
        if 'is_correct' in df.columns:
             df['is_correct'] = pd.to_numeric(df['is_correct'], errors='coerce')  # Convert to numeric, set NaN on failure
        return df
    except sqlite3.Error as e:
        st.error(f"An error occurred while retrieving history: {e}")
        return pd.DataFrame()  # Return an empty DataFrame
    finally:
        if conn:
            conn.close()

def get_db_count():
    """Get the number of records in the database"""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        count = c.fetchone()[0]
        return count
    except sqlite3.Error as e:
        st.error(f"An error occurred while retrieving the record count: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def clear_db():
    """Delete all records from the database"""
    conn = None
    confirmed = st.session_state.get("confirm_clear", False)

    if not confirmed:
        st.warning("Are you sure you want to delete all data? Press the 'Clear Database' button again to confirm.")
        st.session_state.confirm_clear = True
        return False  # Deletion was not executed

    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(f"DELETE FROM {TABLE_NAME}")
        conn.commit()
        st.success("The database has been successfully cleared.")
        st.session_state.confirm_clear = False  # Reset confirmation state
        return True  # Deletion successful
    except sqlite3.Error as e:
        st.error(f"An error occurred while clearing the database: {e}")
        st.session_state.confirm_clear = False  # Reset on error as well
        return False  # Deletion failed
    finally:
        if conn:
            conn.close()