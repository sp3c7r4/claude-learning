from dotenv import load_dotenv
from anthropic import AnthropicBedrock, _models, BaseModel
from os import environ


load_dotenv()

client = AnthropicBedrock(
  aws_access_key=environ.get("AWS_ACCESS_KEY_ID"),
  aws_secret_key=environ.get("AWS_SECRET_ACCESS_KEY"),
  aws_region=environ.get("AWS_REGION"),
)

model = "eu.anthropic.claude-sonnet-4-6"
temperature = 0.0
messages = []

def add_user_input(messages, text):
  messages.append({"role": "user", "content": text})

def add_assistant_input(messages, text):
  messages.append({"role": "assistant", "content": text})

def chat():
  params = {
    "model": model,
    "temperature": temperature,
    "messages": messages,
    "max_tokens": 100,
    "stop_sequences": ["```"],
    "system": "You generate cli commands in json. each part should be very short."
  }
  msg = client.messages.create(**params)
  return msg.content[0].text

def main():
  while True:
    try:
      user_input = input("[User]: ").strip()
      if user_input == "exit":
        print("Thanks for using claude ai 😊")
        exit(0)

      add_user_input(messages, user_input)
      add_assistant_input(messages, "```json")  # Prefill for structured output
      response = chat()
      print(f"[Claude]: {response.strip()}")
      add_assistant_input(messages, response)
    except KeyboardInterrupt:
      print("\nThanks for using claude ai 😊")
      exit(0)

if __name__ == "__main__":
  main()
