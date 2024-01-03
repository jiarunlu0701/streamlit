from openai import OpenAI
import streamlit as st
from db import db
db = db()

client = OpenAI(
    api_key=st.secrets["openai_api_key"],
)

class generate:

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

    def make_image(question_input, num):
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

    def generate_newsletter(Switch, question_input):
        if Switch == 'True':
            latest_prompt = db.get_latest_prompt()
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

    def make_request(self, question_input):
        # Fetch recent chat history
        chat_history = db.get_last_two_chats()  # or use a different method to fetch more/less history

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
            tools=self.tools
        )
        return response

