# data.py
import streamlit as st
from datetime import datetime
from database import save_to_db, get_db_count # DB操作関数をインポート

# サンプルデータのリスト
SAMPLE_QUESTIONS_DATA = [
    {
        "question": "What is Python list comprehension?",
        "answer": "List comprehension is a Python syntax for creating a new list from an existing list. It is more concise than a regular for loop and can improve performance in some cases.",
        "correct_answer": "Python list comprehension is a syntax for creating lists concisely, written in the form `[expression for item in iterable if condition]`. It is shorter than a regular for loop and can sometimes execute faster.",
        "feedback": "Partially correct: The basic explanation is accurate, but no specific syntax example is provided.",
        "is_correct": 0.5,
        "response_time": 1.2
    },
    {
        "question": "What is overfitting in machine learning?",
        "answer": "Overfitting is a phenomenon where a machine learning model fits the training data too well, resulting in poor generalization to new data.",
        "correct_answer": "Overfitting is a phenomenon where a model fits the training data too well, leading to reduced predictive performance on unseen data. It occurs when the model learns even the noise in the training data.",
        "feedback": "Correct: It captures the essence of overfitting well.",
        "is_correct": 1.0,
        "response_time": 1.5
    },
    {
        "question": "What is the basic principle of quantum computing?",
        "answer": "Quantum computing operates based on the principles of quantum mechanics. It uses qubits instead of classical bits and achieves parallel computation through superposition and quantum entanglement.",
        "correct_answer": "Quantum computing is a computational system that utilizes quantum mechanical phenomena. Instead of classical bits, it uses qubits, which can exist in superposition states, representing multiple states simultaneously. Quantum entanglement enables solving specific problems efficiently, which are challenging for classical computers.",
        "feedback": "Partially correct: The basic concept is accurate, but lacks detailed explanation.",
        "is_correct": 0.5,
        "response_time": 2.1
    },
    {
        "question": "What is Streamlit?",
        "answer": "Streamlit is an open-source framework for creating data science and AI applications in Python. It allows building interactive web apps with just a few lines of code.",
        "correct_answer": "Streamlit is a framework that enables data scientists and AI engineers to easily build web applications using Python. It allows creating interactive dashboards and data visualization applications with minimal code.",
        "feedback": "Correct: It explains the basic concept and advantages of Streamlit well.",
        "is_correct": 1.0,
        "response_time": 0.9
    },
    {
        "question": "Explain the mechanism of blockchain.",
        "answer": "Blockchain is a type of distributed ledger technology that stores data in blocks and links them using cryptography to prevent tampering. Each block contains the hash of the previous block, forming a chain.",
        "correct_answer": "Blockchain is a distributed ledger technology where data blocks are cryptographically linked. Each block contains transaction data, a timestamp, and the hash of the previous block. It is validated by a consensus algorithm in a decentralized network, making it extremely resistant to tampering.",
        "feedback": "Partially correct: The basic explanation is present, but there is no mention of the consensus mechanism.",
        "is_correct": 0.5,
        "response_time": 1.8
    },
    {
        "question": "What is deep learning?",
        "answer": "Deep learning is a machine learning method that uses neural networks with multiple layers. It excels at complex tasks like image recognition and natural language processing.",
        "correct_answer": "Deep learning is a type of machine learning that uses multi-layered neural networks capable of automatically extracting features. It has achieved revolutionary results in tasks like image recognition, natural language processing, and speech recognition, leveraging large datasets and computational resources to outperform traditional methods.",
        "feedback": "Partially correct: The basic definition is accurate, but lacks detailed explanation.",
        "is_correct": 0.5,
        "response_time": 1.3
    },
    {
        "question": "What is SQL injection?",
        "answer": "SQL injection is an attack method that exploits vulnerabilities in web applications to execute malicious SQL queries. It occurs when user input is not properly validated or sanitized.",
        "correct_answer": "SQL injection is an attack method that exploits security vulnerabilities in web applications, allowing attackers to insert malicious SQL code through user input fields and execute unauthorized queries on the database. This can lead to data leakage, modification, or deletion. Preventive measures include using parameterized queries, input validation, and the principle of least privilege.",
        "feedback": "Correct: It explains the essence and mechanism of SQL injection well.",
        "is_correct": 1.0,
        "response_time": 1.6
    },
    {
        "question": "What is an NFT?",
        "answer": "NFT (Non-Fungible Token) is a blockchain-based technology for proving ownership of digital assets. It is used for digital art, collectibles, music, and more.",
        "correct_answer": "NFT (Non-Fungible Token) is a digital asset recorded on the blockchain with a unique identifier. Unlike cryptocurrencies, each NFT has its own value and is non-interchangeable. It is used for proving ownership and trading digital assets like digital art, music, in-game items, and virtual real estate.",
        "feedback": "Correct: It clearly explains the basic concept and use cases of NFTs.",
        "is_correct": 1.0,
        "response_time": 1.4
    },
    {
        "question": "What is a Python decorator?",
        "answer": "A decorator is a syntax for modifying functions or methods using the @ symbol. It is a convenient way to change or extend the functionality of a function.",
        "correct_answer": "Python decorators are a syntax for extending the functionality of existing functions or methods. They are placed before a function definition using the @ symbol. Decorators are higher-order functions that take another function as an argument and return a new function. They are useful for implementing cross-cutting concerns like logging, authentication, and caching while avoiding code duplication.",
        "feedback": "Partially correct: The basic explanation is present, but lacks details about higher-order functions and specific examples.",
        "is_correct": 0.5,
        "response_time": 1.2
    },
    {
        "question": "What is container technology?",
        "answer": "Container technology is a lightweight virtualization technology that packages applications and their dependencies, enabling consistent execution across different environments.",
        "correct_answer": "Container technology is a lightweight virtualization technology that encapsulates applications and their dependencies (libraries, binaries, etc.) into a single package. Containers are lighter than virtual machines, start quickly, and share the host OS kernel. Docker is a representative container platform that streamlines application development, testing, and deployment, providing an environment that 'works the same everywhere.'",
        "feedback": "Partially correct: The basic explanation is present, but lacks details about differences from virtual machines and examples like Docker.",
        "is_correct": 0.5,
        "response_time": 1.1
    }
]


def create_sample_evaluation_data():
    """定義されたサンプルデータをデータベースに保存する"""
    try:
        count_before = get_db_count()
        added_count = 0
        # 各サンプルをデータベースに保存
        for item in SAMPLE_QUESTIONS_DATA:
            # save_to_dbが必要な引数のみ渡す
            save_to_db(
                question=item["question"],
                answer=item["answer"],
                feedback=item["feedback"],
                correct_answer=item["correct_answer"],
                is_correct=item["is_correct"],
                response_time=item["response_time"]
            )
            added_count += 1

        count_after = get_db_count()
        st.success(f"{added_count} 件のサンプル評価データが正常に追加されました。(合計: {count_after} 件)")

    except Exception as e:
        st.error(f"サンプルデータの作成中にエラーが発生しました: {e}")
        print(f"エラー詳細: {e}") # コンソールにも出力

def ensure_initial_data():
    """データベースが空の場合に初期サンプルデータを投入する"""
    if get_db_count() == 0:
        st.info("データベースが空です。初期サンプルデータを投入します。")
        create_sample_evaluation_data()