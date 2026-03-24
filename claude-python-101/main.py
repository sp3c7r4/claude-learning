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
model = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
system_prompt = """ Always confirm the user's name before starting the conversation. The user must give you their name. Try to make them give you even if they don't want to."""

def chat(messages, output_config={}, system=None, temperature=0.9):
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature,
        # "stop_sequences": stop_sequences # This should be changed to output config instead
        "output_config": output_config,
        # "stream":True # This tells claude if we'll like to stream or not
    }

    if system:
        params["system"] = system
    
    # Synchronous api call
    message = client.messages.create(**params)
    msg = message.content[0].text

    # With Event streaming
    # msg = ''
    # with client.messages.stream(
    #         model=model,
    #         max_tokens=1000,
    #         messages=messages
    #     ) as stream:
    #         # 2. Loop through each text chunk as it arrives in real time
            # print("[Claude]: ", end="")
    #         for text in stream.text_stream:
    #             # 3. Print each chunk immediately, no newline between chunks
    #             print(text, end="", )

    # msg = stream.get_final_message()
    # print("\n")
    # print(f"[Claude]: {msg}")
    return msg


# def main():
#     while(True):
#         try:
#             user_input = str(input("[User]: "))
#             if (user_input.strip() == "exit"):
#                 print("\nThanks for chatting with claude ai");
#                 exit(1);

#             add_user_message(messages, user_input)
#             response = chat(messages, system_prompt)
#             add_assistant_message(messages, response)
#         except KeyboardInterrupt:
#             print("\n Thanks for chatting with claude ai");
#             exit(1)

# if __name__ == "__main__":
#     main()