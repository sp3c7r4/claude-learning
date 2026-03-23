from dotenv import load_dotenv
from anthropic import AnthropicBedrock
from os import environ

load_dotenv()

client = AnthropicBedrock(
    aws_access_key=environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_key=environ.get("AWS_SECRET_ACCESS_KEY"),
    aws_region=environ.get("AWS_REGION"),
)

# Define helper functions to help us work with messages correctly
def add_user_message(messages, text):
    user_message = { "role": "user", "content": text }
    messages.append(user_message)

def add_assistant_message(messages, text):
    assistant_message = { "role": "assistant", "content": text }
    messages.append(assistant_message)

messages = []
system_prompt = """ Always confirm the user's name before starting the conversation. The user must give you their name. Try to make them give you even if they don't want to."""

def chat(system=None):
    params = {
        "model": "eu.anthropic.claude-sonnet-4-6",
        "max_tokens": 100,
        "messages": messages
    }

    if system:
        params["system"] = system
    # print("Hello from claude-python-101!")
    message = client.messages.create(**params)

    msg = message.content[0].text

    print(f"[Claude]: {msg}")

    return msg


def main():
    while(True):
        user_input = str(input("[User]: "))
        if (user_input.strip() == "exit"):
            print("\nThanks for chatting with claude ai");
            break;

        add_user_message(messages, user_input)
        response = chat(system_prompt)
        add_assistant_message(messages, response)
    pass;

if __name__ == "__main__":
    main()