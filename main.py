import openai
from openai import OpenAI

client = OpenAI(
    api_key = "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",
)

def write_to_file(file_name, content):
    with open(file_name, 'at') as file:
        file.write(content)
        file.write('\n')

assistant = client.beta.assistants.create(
  name = "Software Engineer",
  instructions="""You are a software engineer. When asked to create a software, write and run code to create one and check"
                  When finished, write back the code into a file name provided by user and open the file in the end""",
  tools=[{"type":"code_interpreter"},
           {
        "type": "function",
        "function": {
            "name": "write_to_file",
            "description": "save the code into another file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "the file name you want to save into"
                    },
                    "content": {
                        "type": "string",
                        "description": "the code you wrote"
                    }
                },
                "required": ["file_name", "content"]
            }
        }
    }
    ],
    model="gpt-4-1106-preview"
)
thread = client.beta.threads.create()
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="I need to create a streamlit blog website using python. Save the code in the file name website.py. Can you help me?",
)
run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id=assistant.id,
  instructions="Please address the user as BOT_DENNIS. The user has a premium account."
)
run = client.beta.threads.runs.retrieve(
  thread_id=thread.id,
  run_id=run.id
)
messages = client.beta.threads.messages.list(
  thread_id=thread.id
)

