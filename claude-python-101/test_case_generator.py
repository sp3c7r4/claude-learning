from main import add_user_message, chat
import json

def test_case_generator(prompt):
    output_schema = {
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "test_cases": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "task": {
                                    "type": "string"
                                },
                                "format": {
                                    "type": "string",
                                    "enum": ["python", "json", "regex"]
                                },
                                "solution_criteria": {
                                    "type": "string"
                                }
                            },
                            "required": ["task", "format", "solution_criteria"],
                            "additionalProperties": False
                        },
                    },


                },
                "required": ["test_cases"],
                "additionalProperties": False
            }
        }
    }
  
    messages = []
    add_user_message(messages, prompt)
    response = chat(messages, output_schema)
    return json.loads(response)["test_cases"]

cases = test_case_generator("""
Generate a evaluation dataset for a prompt evaluation. The dataset will be used to evaluate prompts
that generate Python, JSON, or Regex specifically for AWS-related tasks. Generate an array of JSON objects,
each representing task that requires Python, JSON, or a Regex to complete. Indicate in the task what they're meant to use

Example output:
```json
{ "test_cases": 
  [
      {
          "task": "Description of task",
          "format": "json" or "python" or "regex",
          "solution_criteria": "What a good solution would be or look like. what it must include"
      },
    ...additional
  ]
}
```

* Focus on tasks that can be solved by writing a single Python function, a single JSON object, or a regular expression.
* Focus on tasks that do not require writing much code
* Respond only with Python, JSON, or a plain Regex
* Do not add any comments or commentary or explanation
Please generate 5 objects.
""");

with open("cases.json", "w") as f:
    json.dump(cases, f, indent=2)