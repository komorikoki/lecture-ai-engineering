# ui.py
import streamlit as st
import pandas as pd
import time
from database import save_to_db, get_chat_history, get_db_count, clear_db
from llm import generate_response
from data import create_sample_evaluation_data
from metrics import get_metrics_descriptions

# --- チャットページのUI ---
def display_chat_page(pipe):

    # --- Footer and others (optional) ---
    st.markdown(
    """
    <style>
        [data-testid="stApp"] {
            background-color: black;
            color: white;
        }
        [data-testid="stSidebar"] {
            background-color: gray;
            color: black;
        }
    </style>
    """,
    unsafe_allow_html=True
    )
    st.subheader("please input your question")
    user_question = st.text_area("question", key="question_input", height=100, value=st.session_state.get("current_question", ""))
    submit_button = st.button("submit")

    # セッション状態の初期化（安全のため）
    if "current_question" not in st.session_state:
        st.session_state.current_question = ""
    if "current_answer" not in st.session_state:
        st.session_state.current_answer = ""
    if "response_time" not in st.session_state:
        st.session_state.response_time = 0.0
    if "feedback_given" not in st.session_state:
        st.session_state.feedback_given = False

    # 質問が送信された場合
    if submit_button and user_question:
        st.session_state.current_question = user_question
        st.session_state.current_answer = "" # 回答をリセット
        st.session_state.feedback_given = False # フィードバック状態もリセット

        with st.spinner("Generating response from the model..."):
            answer, response_time = generate_response(pipe, user_question)
            st.session_state.current_answer = answer
            st.session_state.response_time = response_time
            # ここでrerunすると回答とフィードバックが一度に表示される
            st.rerun()

    # 回答が表示されるべきか判断 (質問があり、回答が生成済みで、まだフィードバックされていない)
    if st.session_state.current_question and st.session_state.current_answer:
        st.subheader("Response:")
        st.markdown(st.session_state.current_answer) # Markdownで表示
        st.info(f"Response time: {st.session_state.response_time:.2f} seconds")

        # フィードバックフォームを表示 (まだフィードバックされていない場合)
        if not st.session_state.feedback_given:
            display_feedback_form()
        else:
             # フィードバック送信済みの場合、次の質問を促すか、リセットする
             if st.button("Next question"):
                  # 状態をリセット
                  st.session_state.current_question = ""
                  st.session_state.current_answer = ""
                  st.session_state.response_time = 0.0
                  st.session_state.feedback_given = False
                  st.rerun() # 画面をクリア


def display_feedback_form():
    """フィードバック入力フォームを表示する"""
    with st.form("feedback_form"):
        st.subheader("feedback")
        feedback_options = ["correct", "partial correct", "incorrect"]
        # label_visibility='collapsed' でラベルを隠す
        feedback = st.radio("回答の評価", feedback_options, key="feedback_radio", label_visibility='collapsed', horizontal=True)
        correct_answer = st.text_area("More accurate answer (optional)", key="correct_answer_input", height=100)
        feedback_comment = st.text_area("Comment (optional)", key="feedback_comment_input", height=100)
        submitted = st.form_submit_button("Submit feedback")
        if submitted:
            # フィードバックをデータベースに保存
            is_correct = 1.0 if feedback == "correct" else (0.5 if feedback == "partial correct" else 0.0)
            # コメントがない場合でも '正確' などの評価はfeedbackに含まれるようにする
            combined_feedback = f"{feedback}"
            if feedback_comment:
                combined_feedback += f": {feedback_comment}"

            save_to_db(
                st.session_state.current_question,
                st.session_state.current_answer,
                combined_feedback,
                correct_answer,
                is_correct,
                st.session_state.response_time
            )
            st.session_state.feedback_given = True
            st.success("Feedback has been saved!")
            # フォーム送信後に状態をリセットしない方が、ユーザーは結果を確認しやすいかも
            # 必要ならここでリセットして st.rerun()
            st.rerun() # フィードバックフォームを消すために再実行

# --- 履歴閲覧ページのUI ---
def display_history_page():
    """履歴閲覧ページのUIを表示する"""
    # --- Footer and others (optional) ---
    st.markdown(
    """
    <style>
        [data-testid="stApp"] {
            background-color: black;
            color: white;
        }
    </style>
    """,
    unsafe_allow_html=True
    )
    st.subheader("Chat History and Metrics")
    history_df = get_chat_history()

    if history_df.empty:
        st.info("There are no chat history yet.")
        return

    # タブでセクションを分ける
    tab1, tab2 = st.tabs(["History", "Metrics Analysis"])

    with tab1:
        display_history_list(history_df)

    with tab2:
        display_metrics_analysis(history_df)

def display_history_list(history_df):
    """履歴リストを表示する"""
    st.write("#### History List")
    # 表示オプション
    filter_options = {
        "all": None,
        "correct only": 1.0,
        "partially correct only": 0.5,
        "incorrect only": 0.0
    }
    display_option = st.radio(
        "Display Filter",
        options=filter_options.keys(),
        horizontal=True,
        label_visibility="collapsed" # ラベル非表示
    )

    filter_value = filter_options[display_option]
    if filter_value is not None:
        # is_correctがNaNの場合を考慮
        filtered_df = history_df[history_df["is_correct"].notna() & (history_df["is_correct"] == filter_value)]
    else:
        filtered_df = history_df

    if filtered_df.empty:
        st.info("No history matches the selected criteria.")
        return

    # ページネーション
    items_per_page = 5
    total_items = len(filtered_df)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    current_page = st.number_input('Page', min_value=1, max_value=total_pages, value=1, step=1)

    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_df = filtered_df.iloc[start_idx:end_idx]


    for i, row in paginated_df.iterrows():
        with st.expander(f"{row['timestamp']} - Q: {row['question'][:50] if row['question'] else 'N/A'}..."):
            st.markdown(f"**Q:** {row['question']}")
            st.markdown(f"**A:** {row['answer']}")
            st.markdown(f"**Feedback:** {row['feedback']}")
            if row['correct_answer']:
                st.markdown(f"**Correct A:** {row['correct_answer']}")

            # 評価指標の表示
            st.markdown("---")
            cols = st.columns(3)
            cols[0].metric("Accuracy Score", f"{row['is_correct']:.1f}")
            cols[1].metric("Response Time (seconds)", f"{row['response_time']:.2f}")
            cols[2].metric("Word Count", f"{row['word_count']}")

            cols = st.columns(3)
            # NaNの場合はハイフン表示
            cols[0].metric("BLEU", f"{row['bleu_score']:.4f}" if pd.notna(row['bleu_score']) else "-")
            cols[1].metric("Similarity", f"{row['similarity_score']:.4f}" if pd.notna(row['similarity_score']) else "-")
            cols[2].metric("Relevance", f"{row['relevance_score']:.4f}" if pd.notna(row['relevance_score']) else "-")
    #英吾に変更
    st.caption(f" {start_idx+1} - {min(end_idx, total_items)} / {total_items}")


def display_metrics_analysis(history_df):
    """評価指標の分析結果を表示する"""
    # --- Footer and others (optional) ---
    st.markdown(
    """
    <style>
        [data-testid="stApp"] {
            background-color: black;
            color: white;
        }
    </style>
    """,
    unsafe_allow_html=True
    )
    st.write("#### analysis of evaluation metrics")

    # is_correct が NaN のレコードを除外して分析
    analysis_df = history_df.dropna(subset=['is_correct'])
    if analysis_df.empty:
        st.warning("No evaluable data available.")
        return

    accuracy_labels = {1.0: 'accurate', 0.5: 'partially accurate', 0.0: 'inaccurate'}
    analysis_df['accuracy'] = analysis_df['is_correct'].map(accuracy_labels)

    # Accuracy distribution
    st.write("##### Accuracy Distribution")
    accuracy_counts = analysis_df['accuracy'].value_counts()
    if not accuracy_counts.empty:
        st.bar_chart(accuracy_counts)
    else:
        st.info("No accuracy data available.")

    # Response time and other metrics relationship
    st.write("##### Response Time and Other Metrics Relationship")
    metric_options = ["bleu_score", "similarity_score", "relevance_score", "word_count"]
    # Include only available metrics in the options
    valid_metric_options = [m for m in metric_options if m in analysis_df.columns and analysis_df[m].notna().any()]

    if valid_metric_options:
        metric_option = st.selectbox(
            "Select the metric to compare",
            valid_metric_options,
            key="metric_select"
        )

        chart_data = analysis_df[['response_time', metric_option, 'accuracy']].dropna() # NaNを除外
        if not chart_data.empty:
             st.scatter_chart(
                chart_data,
                x='response_time',
                y=metric_option,
                color='accuracy',
            )
        else:
            st.info(f"There are no valid data for the selected metric ({metric_option}) and response time.")

    else:
        st.info("There are no metric data available to compare with response time.")


    # 全体の評価指標の統計
    st.write("##### Evaluation Metrics Statistics")
    stats_cols = ['response_time', 'bleu_score', 'similarity_score', 'word_count', 'relevance_score']
    valid_stats_cols = [c for c in stats_cols if c in analysis_df.columns and analysis_df[c].notna().any()]
    if valid_stats_cols:
        metrics_stats = analysis_df[valid_stats_cols].describe()
        st.dataframe(metrics_stats)
    else:
        st.info("There is no metric data available to calculate statistics.")

    # Accuracy level average scores
    st.write("##### Average Scores by Accuracy Level")
    if valid_stats_cols and 'accuracy' in analysis_df.columns:
        try:
            accuracy_groups = analysis_df.groupby('accuracy')[valid_stats_cols].mean()
            st.dataframe(accuracy_groups)
        except Exception as e:
            st.warning(f"An error occurred while aggregating scores by accuracy: {e}")
    else:
         st.info("There is no data available to calculate average scores by accuracy level.")


    # カスタム評価指標：効率性スコア
    st.write("##### efficiency (accuracy) / (response time + 0.1)")  # Fixed typo in "response"
    if 'response_time' in analysis_df.columns and analysis_df['response_time'].notna().any():
        # ゼロ除算を避けるために0.1を追加
        analysis_df['efficiency_score'] = analysis_df['is_correct'] / (analysis_df['response_time'].fillna(0) + 0.1)
        # IDカラムが存在するか確認
        if 'id' in analysis_df.columns:
            # 上位10件を表示
            top_efficiency = analysis_df.sort_values('efficiency_score', ascending=False).head(10)
            # id をインデックスにする前に存在確認
            if not top_efficiency.empty:
                st.bar_chart(top_efficiency.set_index('id')['efficiency_score'])
            else:
                st.info("There are no efficiency score data available.")
        else:
            # IDがない場合は単純にスコアを表示
             st.bar_chart(analysis_df.sort_values('efficiency_score', ascending=False).head(10)['efficiency_score'])

    else:
        st.info("There is no data available to calculate efficiency scores.")


# --- サンプルデータ管理ページのUI ---
def display_data_page():
    # --- Footer and others (optional) ---
    st.markdown(
    """
    <style>
        [data-testid="stApp"] {
            background-color: black;
            color: white;
        }
    </style>
    """,
    unsafe_allow_html=True
    )
    """Display the UI for managing sample evaluation data"""
    st.subheader("Sample Evaluation Data Management")
    count = get_db_count()
    st.write(f"Currently, there are {count} records in the database.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Sample Data", key="create_samples"):
            create_sample_evaluation_data()
            st.rerun() # 件数表示を更新

    with col2:
        # 確認ステップ付きのクリアボタン
        if st.button("clear database", key="clear_db_button"):
            if clear_db(): # clear_db内で確認と実行を行う
                st.rerun() # クリア後に件数表示を更新

    # 評価指標に関する解説
    st.subheader("Evaluation Metrics Explanation")
    metrics_info = get_metrics_descriptions()
    for metric, description in metrics_info.items():
        with st.expander(f"{metric}"):
            st.write(description)