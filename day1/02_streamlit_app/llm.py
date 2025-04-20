# llm.py
import os
import torch
from transformers import pipeline
import streamlit as st
import time
from config import MODEL_NAME
from huggingface_hub import login


# モデルをキャッシュして再利用
@st.cache_resource
def load_model():
    """Load the LLM model"""
    try:
        # Save access token
        hf_token = st.secrets["huggingface"]["token"]
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        st.info(f"Using device: {device}")  # Display the device being used
        pipe = pipeline(
            "text-generation",
            model=MODEL_NAME,
            model_kwargs={"torch_dtype": torch.bfloat16},
            device=device
        )
        st.success(f"Successfully loaded model '{MODEL_NAME}'.")
        return pipe
    except Exception as e:
        st.error(f"Failed to load model '{MODEL_NAME}': {e}")
        st.error("There might be insufficient GPU memory. Consider terminating unnecessary processes or using a smaller model.")
        return None

def generate_response(pipe, user_question):
    """Generate a response to the user's question using the LLM"""
    if pipe is None:
        return "Cannot generate a response because the model is not loaded.", 0

    try:
        start_time = time.time()
        messages = [
            {"role": "user", "content": user_question},
        ]
        # Allow adjustment of max_new_tokens (example)
        outputs = pipe(messages, max_new_tokens=512, do_sample=True, temperature=0.7, top_p=0.9)

        # Adjustments may be needed to match Gemma's output format
        # Retrieve the last assistant message
        assistant_response = ""
        if outputs and isinstance(outputs, list) and outputs[0].get("generated_text"):
           if isinstance(outputs[0]["generated_text"], list) and len(outputs[0]["generated_text"]) > 0:
               # For messages format
               last_message = outputs[0]["generated_text"][-1]
               if last_message.get("role") == "assistant":
                   assistant_response = last_message.get("content", "").strip()
           elif isinstance(outputs[0]["generated_text"], str):
               # For simple string format (older transformers?) - may need to exclude the prompt part
               # This part may need adjustments depending on the model or transformers version
               full_text = outputs[0]["generated_text"]
               # Simple method: Get the part after the user's question
               prompt_end = user_question
               response_start_index = full_text.find(prompt_end) + len(prompt_end)
               # Extract only the response part (more robust methods may be needed)
               possible_response = full_text[response_start_index:].strip()
               # Adjustments specific to the model, such as searching for a specific start token
               if "<start_of_turn>model" in possible_response:
                    assistant_response = possible_response.split("<start_of_turn>model\n")[-1].strip()
               else:
                    assistant_response = possible_response  # Fallback

        if not assistant_response:
             # Fallback or debugging if the response is not found above
             print("Warning: Could not extract assistant response. Full output:", outputs)
             assistant_response = "Failed to extract the response."

        end_time = time.time()
        response_time = end_time - start_time
        print(f"Generated response in {response_time:.2f}s")  # For debugging
        return assistant_response, response_time

    except Exception as e:
        st.error(f"An error occurred while generating the response: {e}")
        # Output error details to the log
        import traceback
        traceback.print_exc()
        return f"An error occurred: {str(e)}", 0
