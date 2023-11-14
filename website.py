import streamlit as st
import json
from openai import OpenAI
import sqlite3
from PIL import Image
import os

image = Image.open('sap.png')
prompt_tokens = 0
completion_tokens = 0
total_tokens_used = 0
newsletter_prompt_tokens = 0
newsletter_completion_tokens = 0
newsletter_total_tokens_used = 0

client = OpenAI(
    api_key=st.secrets["openai_api_key"],
)
def get_db_connection():
    conn = sqlite3.connect('chat_history.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_chat_history_descending():
    conn = get_db_connection()
    # Fetch entries in descending order so the newest are first
    chats = conn.execute("SELECT * FROM CHAT WHERE ROLE IN ('User', 'SAP Digital School AI') ORDER BY ID DESC").fetchall()
    conn.close()
    return chats

def get_last_two_chats():
    conn = get_db_connection()
    # Fetch the last two entries
    last_two_chats = conn.execute("SELECT * FROM CHAT WHERE ROLE IN ('User', 'SAP Digital School AI') ORDER BY ID DESC LIMIT 2").fetchall()
    conn.close()
    return last_two_chats

def update_token_usage(prompt_tokens, completion_tokens, total_tokens):
    conn = get_db_connection()
    conn.execute('INSERT INTO TOKEN_USAGE (prompt_tokens, completion_tokens, total_tokens) VALUES (?, ?, ?)',
                 (prompt_tokens, completion_tokens, total_tokens))
    conn.commit()
    conn.close()

def reset_token_usage():
    conn = get_db_connection()
    conn.execute('DELETE FROM TOKEN_USAGE')  # Assuming TOKEN_USAGE is your table name
    conn.commit()
    conn.close()

def get_latest_token_usage():
    conn = get_db_connection()
    token_usage = conn.execute('SELECT * FROM TOKEN_USAGE ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    return token_usage if token_usage else None

def add_chat(role, message, image_urls=None):
    conn = get_db_connection()
    if image_urls:
        image_urls_str = ','.join(image_urls)  # Joining the URLs into a single string
        conn.execute('INSERT INTO CHAT (ROLE, MESSAGE, IMAGE_URL) VALUES (?, ?, ?)', (role, message, image_urls_str))
    else:
        conn.execute('INSERT INTO CHAT (ROLE, MESSAGE) VALUES (?, ?)', (role, message))
    conn.commit()
    conn.close()

def delete_chat_history():
    conn = get_db_connection()
    conn.execute('DELETE FROM CHAT')
    conn.commit()
    conn.close()

def save_prompt(prompt_text):
    conn = get_db_connection()
    conn.execute('INSERT INTO PROMPTS (prompt) VALUES (?)', (prompt_text,))
    conn.commit()
    conn.close()

def get_latest_prompt():
    conn = get_db_connection()
    prompt = conn.execute('SELECT prompt FROM PROMPTS ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    return prompt['prompt'] if prompt else None

def count_tokens(text):
    # Simple approximation: count the spaces and add one
    # This is a crude approximation, actual tokenization is more complex
    return len(text.split())

def markdown_copyable_text(role, message, max_line_length=80):
    # Function to add line breaks at a specified length
    def add_line_breaks(text, length):
        lines = []
        for paragraph in text.split('\n'):
            while len(paragraph) > length:
                # Find the nearest space before the max line length
                break_point = paragraph.rfind(' ', 0, length)
                if break_point == -1:  # No space found, force break
                    break_point = length
                lines.append(paragraph[:break_point])
                paragraph = paragraph[break_point:].lstrip()
            lines.append(paragraph)
        return '\n'.join(lines)

    # Pre-format the message
    formatted_message = add_line_breaks(message, max_line_length)

    # Include the role above the code box for clarity
    st.markdown(f"**{role}:**")
    # Use triple backticks to format the message as code within the markdown
    markdown_text = f"```\n{formatted_message}\n```"
    st.markdown(markdown_text)

def make_image(question_input,num):
    try:
        response = client.images.generate(
            model="dall-e-2",
            prompt=f"{question_input}",
            size="1024x1024",
            quality="standard",
            n=int(num),
        )
        return response
    except Exception as e:
        st.error(f"An error occurred while generating images: {e}")
        return None

def generate_newsletter(Switch,question_input):
    if Switch=='True':
        latest_prompt = get_latest_prompt()
        if latest_prompt:
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                temperature=0.5,
                messages=[
                    {"role": "system", "content": f"{latest_prompt}"},
                    {"role": "user", "content": question_input},
                ],
            )
        return response

def make_request(question_input):
    # Fetch recent chat history
    chat_history = get_last_two_chats()  # or use a different method to fetch more/less history

    # Format the chat history for the GPT model
    formatted_history = []
    for chat in chat_history:
        role = 'user' if chat['ROLE'] == 'User' else 'assistant'
        message = chat['MESSAGE']
        formatted_history.append({"role": role, "content": message})

    # Add the current user message to the history
    formatted_history.append({"role": "user", "content": question_input})

    # Create the completion request with the formatted chat history
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=0.5,
        messages=formatted_history,
        tools=tools
    )
    return response

def handle_response(tool_calls):
    global newsletter_prompt_tokens, newsletter_completion_tokens, newsletter_total_tokens_used
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        arguments_dict = json.loads(tool_call.function.arguments)
        if function_name == 'make_image':
            question_input, num = arguments_dict.get('question_input'), arguments_dict.get('num')
            response_img = make_image(question_input, num)
            if response_img:
                display_images(response_img)
        elif function_name == 'generate_newsletter':
            question_input, switch = arguments_dict.get('question_input'), arguments_dict.get('Switch')
            newsletter_response = generate_newsletter(switch,question_input)
            if newsletter_response:
                newsletter_content = newsletter_response.choices[0].message.content
                newsletter_prompt_tokens = newsletter_response.usage.prompt_tokens
                newsletter_completion_tokens = newsletter_response.usage.completion_tokens
                newsletter_total_tokens_used = newsletter_response.usage.total_tokens
                add_chat("SAP Digital School AI", newsletter_content)

def display_images(response_img):
    st.write("I have generated the images you required")
    image_urls = [image_data.url for image_data in response_img.data]
    add_chat("SAP Digital School AI", "[images]", image_urls)

def display_chat_history():
    chats = get_chat_history_descending()
    for chat in chats:
        role, message = chat['ROLE'], chat['MESSAGE']
        image_urls_str = chat['IMAGE_URL'] if 'IMAGE_URL' in chat.keys() else None

        if message and message != '[images]':
            markdown_copyable_text(role, message)
        elif image_urls_str:
            image_urls = image_urls_str.split(',')  # Splitting the URLs back into a list
            cols = st.columns(len(image_urls))
            for col, image_url in zip(cols, image_urls):
                with col:
                    st.image(image_url, use_column_width=True)
                    st.caption("Generated Image")

tools = [
    {
        "type": "function",
        "function": {
            "name": "make_image",
            "description": "Generate numbers of pictures to meet the demand of the topic of the question_input area",
            "parameters": {
                "type": "object",
                "properties": {
                    "question_input": {
                        "type": "string",
                        "description": "A summary on the topic for the generated images",
                    },
                    "num": {
                        "type": "string",
                        "description": "Number of images user asked to generate",
                    },
                },
                "required": ["question_input", "num"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_newsletter",
            "description": "If Switch == True, then generate newsletter",
            "parameters": {
                "type": "object",
                "properties": {
                    "Switch": {
                        "type": "string",
                        "description": "If Switch == 'True', then generate newsletter",
                    },
                    "question_input": {
                        "type": "string",
                        "description": "preserve the entire user's question_input",
                    },
                },
                "required": ["Switch", "question_input"],
            },
        }
    }
]

def chat_page():
    global prompt_tokens,completion_tokens,total_tokens_used
    st.header("SAP Digital School AI")
    question_input = st.text_area("Enter question", key="question_input")
    submit_button = st.button("Submit", key="submit_button")
    latest_tokens = get_latest_token_usage()
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
    display_chat_history()
    if submit_button and question_input:
        response = make_request(question_input)
        print(response)
        if response:
            add_chat("User", question_input)
            if response.choices[0].message.tool_calls:
                handle_response(response.choices[0].message.tool_calls)
            else:
                chat_content = response.choices[0].message.content
                add_chat("SAP Digital School AI", chat_content)

            prompt_tokens = response.usage.prompt_tokens + newsletter_prompt_tokens
            completion_tokens = response.usage.completion_tokens + newsletter_completion_tokens
            total_tokens_used = response.usage.total_tokens + newsletter_total_tokens_used
            update_token_usage(prompt_tokens,completion_tokens,total_tokens_used)
            st.experimental_rerun()
        else:
            st.error("No response from the AI. Please try again.")

def prompt_page():
    st.header("Prompt Page")
    latest_prompt = get_latest_prompt()
    default_text = latest_prompt if latest_prompt else ''
    question_input = st.text_area("Current Pormpt:", value=latest_prompt if latest_prompt else '', key="question_input", height=600)
    tokens_count = count_tokens(question_input)
    st.markdown(f"Approximate Token count: {tokens_count}")
    submit_button = st.button('Edit Prompt', key='prompt_page_submit')
    if submit_button:
        save_prompt(question_input)
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
        delete_chat_history()
        reset_token_usage()
        st.success('Chat history and token counts cleared!')

if page == "Chat":
    chat_page()
elif page == "Prompt":
    prompt_page()