import streamlit as st
from chatbot import GraphRAGExcelChatbot

# Initialize chatbot
chatbot = GraphRAGExcelChatbot()

st.set_page_config(page_title="Graph RAG Chatbot", layout="centered")

st.title("🤖 RAG Chatbot with Knowledge Graph")
st.write("Upload an Excel file and ask questions!")

# File Upload
file = st.file_uploader("Upload Excel File", type=["xlsx"])
if file:
    chatbot.upload_and_process(file)
    st.success("✅ File uploaded and processed!")

    # Show Graph
    if st.button("Visualize Graph"):
        chatbot.visualize_graph()
        st.image("graph.png")

# Chat Input
user_input = st.text_input("Ask a Question:")
if st.button("Submit"):
    if user_input:
        response, context = chatbot.ask_question(user_input)
        st.write("**Answer:**", response)
        st.write("**Context Used:**", context)
    else:
        st.warning("Please enter a question.")
