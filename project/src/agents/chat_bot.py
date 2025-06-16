import streamlit as st
import google.generativeai as genai
from rag import rag



# API Key para la API de Google Gemini
GEMINI_API_KEY = "AIzaSyDSWR4UwuJmxjvHrmw8t-V9PzUB5aV3QTU"

chat_utils = rag.ChatUtils()

st.set_page_config(page_title="TuristAI", page_icon="🌴", layout="centered")
st.title("🌴 TuristAI: Tu Asistente Turístico")
st.write("¡Hola! Soy TuristAI, tu asistente turístico. ¿En qué puedo ayudarte hoy?")


# CSS para diferenciar mensajes
st.markdown("""
    <style>
    .user-msg {
        background-color: #DCF8C6;
        color: #222;
        padding: 10px 16px;
        border-radius: 12px;
        margin-bottom: 8px;
        margin-left: 40px;
        max-width: 70%;
        align-self: flex-end;
    }
    .bot-msg {
        background-color: #F1F0F0;
        color: #222;
        padding: 10px 16px;
        border-radius: 12px;
        margin-bottom: 8px;
        margin-right: 40px;
        max-width: 70%;
        align-self: flex-start;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
    }
    </style>
""", unsafe_allow_html=True)


if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg"><b>Tú:</b> {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-msg"><b>TuristAI:</b> {msg["content"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

user_input = st.text_input("Escribe tu mensaje:")
#Utilizar la funcion para mejorar el prompt

def generate(messages):  
    historial = ""
    for m in messages[:-1]:
        if m["role"] == "user":
            historial += f"Usuario: {m['content']}\n"
        else:
            historial += f"Asistente: {m['content']}\n"
    
    user_query = messages[-1]["content"]
    prompt_enriquecido = chat_utils.prompt_gen(user_query, chat_utils.store_vectors, top_k=30)
    
    prompt = historial + "\n" + prompt_enriquecido
  

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
        
    return response.text


if st.button("Enviar") and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    bot_reply = generate(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    st.rerun()