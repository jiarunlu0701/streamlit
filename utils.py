import json
from generate import generate
import streamlit as st
from db import db
db = db()
class utils:
    def markdown_copyable_text(self, role, message, max_line_length=80):
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

    def handle_response(self, tool_calls):
        global newsletter_prompt_tokens, newsletter_completion_tokens, newsletter_total_tokens_used
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments_dict = json.loads(tool_call.function.arguments)
            print(arguments_dict)
            if function_name == 'make_image':
                question_input, num = arguments_dict.get('question_input'), arguments_dict.get('num')
                response_img = generate.make_image(question_input, num)
                if response_img:
                    generate.display_images(response_img)
            elif function_name == 'generate_newsletter':
                question_input, Switch = arguments_dict.get('question_input'), arguments_dict.get('Switch')
                print(question_input,Switch)
                newsletter_response = generate.generate_newsletter(Switch, question_input)
                if newsletter_response:
                    newsletter_content = newsletter_response.choices[0].message.content
                    newsletter_prompt_tokens = newsletter_response.usage.prompt_tokens
                    newsletter_completion_tokens = newsletter_response.usage.completion_tokens
                    newsletter_total_tokens_used = newsletter_response.usage.total_tokens
                    db.add_chat("SAP Digital School AI", newsletter_content)

    def display_images(self, response_img):
        st.write("I have generated the images you required")
        image_urls = [image_data.url for image_data in response_img.data]
        db.add_chat("SAP Digital School AI", "[images]", image_urls)

    def display_chat_history(self):
        chats = db.get_chat_history_descending()
        for chat in chats:
            role, message = chat['ROLE'], chat['MESSAGE']
            image_urls_str = chat['IMAGE_URL'] if 'IMAGE_URL' in chat.keys() else None

            if message and message != '[images]':
                self.markdown_copyable_text(role, message)
            elif image_urls_str:
                image_urls = image_urls_str.split(',')  # Splitting the URLs back into a list
                cols = st.columns(len(image_urls))
                for col, image_url in zip(cols, image_urls):
                    with col:
                        st.image(image_url, use_column_width=True)
                        st.caption("Generated Image")
