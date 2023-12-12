import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from PIL import Image
from db import db
from utils import utils
from generate import generate
from token_status import count

db = db()
utils = utils()
generate = generate()
count = count()

with open('../config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

authenticator.login('Login', 'main')
if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'main', key='unique_key')
    st.write(f'Welcome *{st.session_state["name"]}*')
    st.title('Some content')
elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')

image = Image.open('assets/sap.png')
prompt_tokens = 0
completion_tokens = 0
total_tokens_used = 0
newsletter_prompt_tokens = 0
newsletter_completion_tokens = 0
newsletter_total_tokens_used = 0

def chat_page():
    global prompt_tokens,completion_tokens,total_tokens_used
    st.header("SAP Digital School AI")
    question_input = st.text_area("Enter question", key="question_input")
    submit_button = st.button("Submit", key="submit_button")
    latest_tokens = count.get_latest_token_usage()
    if latest_tokens:
        prompt_tokens, completion_tokens, total_tokens_used = latest_tokens['prompt_tokens'], latest_tokens[
            'completion_tokens'], latest_tokens['total_tokens']
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("Prompt tokens used:", prompt_tokens)
    with col2:
        st.write("Completion tokens used:", completion_tokens)
    with col3:
        st.write("Total tokens used:", total_tokens_used)
    st.markdown("---")
    utils.display_chat_history()
    if submit_button and question_input:
        response = generate.make_request(question_input)
        print(response)
        if response:
            db.add_chat("User", question_input)
            if response.choices[0].message.tool_calls:
                utils.handle_response(response.choices[0].message.tool_calls)
            else:
                chat_content = response.choices[0].message.content
                db.add_chat("SAP Digital School AI", chat_content)

            prompt_tokens = response.usage.prompt_tokens + newsletter_prompt_tokens
            completion_tokens = response.usage.completion_tokens + newsletter_completion_tokens
            total_tokens_used = response.usage.total_tokens + newsletter_total_tokens_used
            count.update_token_usage(prompt_tokens,completion_tokens,total_tokens_used)
            st.experimental_rerun()
        else:
            st.error("No response from the AI. Please try again.")

def prompt_page():
    st.header("Prompt Page")
    latest_prompt = db.get_latest_prompt()
    default_text = latest_prompt if latest_prompt else ''
    question_input = st.text_area("Current Pormpt:", value=latest_prompt if latest_prompt else '', key="question_input", height=600)
    tokens_count = count.count_tokens(question_input)
    st.markdown(f"Approximate Token count: {tokens_count}")
    submit_button = st.button('Edit Prompt', key='prompt_page_submit')
    if submit_button:
        db.save_prompt(question_input)
        st.experimental_rerun()

with st.sidebar:
    st.image(image, use_column_width=True)
    st.header("SAP Digital School AI")
    # Navigation
    st.markdown("---")
    st.subheader("Navigation")
    page = st.radio("Go to", ["Chat", "Prompt"])
    # Button for clearing chat history
    clear_button = st.button('Clear Chat History and token counts', key='clear_history')
    if clear_button:
        db.delete_chat_history()
        count.reset_token_usage()
        st.success('Chat history and token counts cleared!')


if page == "Chat":
    chat_page()
elif page == "Prompt":
    prompt_page()