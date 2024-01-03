import streamlit as st
from PIL import Image
from db import db
from utils import utils
from generate import generate
from token_status import count

db = db()
utils = utils()
generate = generate()
count = count()

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
        if response:
            db.add_chat("User", question_input)
            if response.choices[0].message.tool_calls:
                utils.handle_response(response.choices[0].message.tool_calls,question_input)
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
    question_input = st.text_area("Current Pormpt:", value=latest_prompt if latest_prompt else '', key="question_input", height=600)
    tokens_count = count.count_tokens(question_input)
    st.markdown(f"Approximate Token count: {tokens_count}")
    submit_button = st.button('Edit Prompt', key='prompt_page_submit')
    if submit_button:
        db.save_prompt(question_input)
        st.experimental_rerun()
def readme():
    st.subheader("Generate newsletter")
    st.markdown("""
    - Ask AI to write a newsletter in simple words, include as much details as possible.
    
    (example: I need to create a newsletter in English for AIGC bootcamp. The start date is 12/12/2023, and end date is 12/15/2023.
     Can you do it for me?)
    """)

    st.subheader("How to improve the newsletter quality")
    st.markdown("""
    - Aside from more detailed input, you can ask AI to provide you an outline before actually writing the newsletter. And
    modify the outline first, so that you two can have a better understanding of each others' idea.
    
    (example: I need to create a newsletter in English for AIGC bootcamp. The start date is 12/12/2023, and end date is 12/15/2023,
    write me an outline on how you going to draft it.)
    """)

    st.subheader("How to let AI improves/modifies on top of the newsletter it generated")
    st.markdown("""
    - To let AI improves or modifies on the newsletter it generated, just tell it to modifies on the newsletter before.
    
    (examples: I like the previous newsletters you generated, can you modify it and change the start date to 12/13/2023.
    """)

    st.subheader("How to let AI generate pictures for the newsletter")
    st.markdown("""
    - To let AI generate pictures for the newsletter, you simply just ask the AI the number of pictures and the newsletter
    it needs to generate pictures for. And AI will create it for you.

    (examples: I need to create a newsletter in English for AIGC bootcamp. The start date is 12/12/2023, and end date is 12/15/2023.
     Can you create two pictures for me to put in the newsletter?
    """)

    st.subheader("How to change the prompt")
    st.markdown("""
    Inside the "Prompt" Page, there are prompts/command inside which embedded inside the AI prompt system, it sets the tone,
    and special pre-knowledge it needs to know for specific tasks it requires. Inside the "Prompt page", I have stored the previous 
    newsletters for it to study so that it will follow the same format and tone to generate new newsletter. If you like, you can play around
    and store your own prompts to match your specific needs of your own task.
    """)
with st.sidebar:
    st.image(image, use_column_width=True)
    st.header("SAP Digital School AI")
    # Navigation
    st.markdown("---")
    st.subheader("Navigation")
    page = st.radio("Go to", ["Chat", "Prompt","How To Use The Website"])
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
else:
    readme()