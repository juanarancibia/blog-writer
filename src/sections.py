import os

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

from lib.streamlit_callback import get_streamlit_cb
from workflows.sections_outliner.graph import invoke_graph

load_dotenv()

st.title("Sections Outliner")
st.markdown("#### Te voy a dar secciones")

# st write magic
"""

Tira un tema yo voy por las secciones

--- 
"""

# Check if the API key is available as an environment variable
if not os.getenv("AKASH_API_KEY"):
    # If not, display a sidebar input for the user to provide the API key
    st.sidebar.header("Akash Api Key Setup")
    api_key = st.sidebar.text_input(
        label="API Key", type="password", label_visibility="collapsed"
    )
    os.environ["AKASH_API_KEY"] = api_key
    # If no key is provided, show an info message and stop further execution
    # and wait till key is entered
    if not api_key:
        st.info("Please enter your AKASH_API_KEY in the sidebar.")
        st.stop()

if "messages" not in st.session_state:
    # default initial message to render in message state
    st.session_state["messages"] = [
        AIMessage(content="Sobre que tema queres investigar?")
    ]

# Loop through all messages in the session state and render them as a chat
# on every st.refresh mech
for msg in st.session_state.messages:
    # https://docs.streamlit.io/develop/api-reference/chat/st.chat_message
    # we store them as AIMessage and HumanMessage as its easier to send to LangGraph
    if type(msg) is AIMessage:
        st.chat_message("assistant").write(msg.content)
    if type(msg) is HumanMessage:
        st.chat_message("user").write(msg.content)

# takes new input in chat box from user and invokes the graph
if prompt := st.chat_input():
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.chat_message("user").write(prompt)

    # Process the AI's response and handles graph events using the callback mechanism
    with st.chat_message("assistant"):
        # create a new container for streaming messages only, and give it context
        st_callback = get_streamlit_cb(st.container())
        response = invoke_graph(st.session_state.messages[-1].content, [st_callback])
        # Add that last message to the st_message_state
        # Streamlit's refresh the message will automatically be visually rendered bc
        # of the msg render for loop above
        st.session_state.messages.append(
            AIMessage(content=str(response["markdown_sections"]))
        )

        st.rerun()
