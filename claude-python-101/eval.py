import json
from main import chat, add_user_message, add_assistant_message
from dotenv import load_dotenv
from statistics import mean


load_dotenv()
# Code evaluators
import re, ast, json

def validate_python(text):
   try:
      ast.parse(text);
      return 10
   except SyntaxError:
      return 0

def validate_json(text):
   try:
      json.loads(text.strip());
      return 10
   except json.JSONDecodeError:
      return 0
   
def validate_regex(text):
   try:
      re.compile(text.strip());
      return 10
   except re.error:
      return 0

def syntax_grade(response, test_case):
   format = test_case["format"]
   if format == "json":
      return validate_json(response)
   elif format == "python":
      return validate_python(response)
   else:
      return validate_regex(response)

   
# Helper functions to help run evals
def run_prompt(test_case):
  prompt = f"""
  Please solve the following task:

  {test_case["task"]}

  * Respond only with Python, JSON or a Plain Regex
  * Do not add any comments
  """
  messages = []
  add_user_message(messages, prompt)
  output = chat(messages)
  return output;

# Function to grade a test case + output using a model
def grade_by_model(test_case, output):
    eval_prompt = f"""
      You are an expert AWS code reviewer. Your task is to evaluate the following AI-generated solution.

      Original Task:
      <task>
      {test_case["task"]}
      </task>

      Solution to Evaluate:
      <solution>
      {output}
      </solution>

      <solution_criteria>
      {test_case["solution_criteria"]}
      </solution_criteria>

      Output Format
      Provide your evaluation as a structured JSON object with the following fields, in this specific order:
      - "strengths": An array of 1-3 key strengths
      - "weaknesses": An array of 1-3 key areas for improvement
      - "reasoning": A concise explanation of your overall assessment
      - "score": A number between 1-10

      Respond with JSON. Keep your response concise and direct.
      Example response shape:
      {{
          "strengths": string[],
          "weaknesses": string[],
          "reasoning": string,
          "score": number
      }}
    """

    messages = []
    add_user_message(messages, eval_prompt)

    output_config = {
       "format": {
          "type": "json_schema",
          "schema": {
             "type": "object",
             "properties": {
                "strengths": { "type": "array", "items": { "type": "string" } },
                "weaknesses": { "type": "array", "items": { "type": "string" } },
                "reasoning": { "type": "array", "items": { "type": "string" } },
                "score": { "type": "number"}
             },
             "required": ["strengths", "weakness", "reasoning", "score"],
             "additionalProperties": False
          }
       }
    }

    eval_text = chat(messages, output_config)
    return json.loads(eval_text)

def run_test_case(test_case):
  """Calls run_prompt, then grades the result"""
  
  output = run_prompt(test_case)

  syntax_score = syntax_grade(output, test_case)
  model_grade = grade_by_model(test_case, output)

  model_score = model_grade["score"]
  reasoning = model_grade["reasoning"]
  
  score = (model_score+syntax_score)
  # weaknesses = grade["weaknesses"]
  # strengths = grade["strengths"]
  # reasoning = grade["reasoning"]

  return {
    "output": output,
    "test_case": test_case,
    "reasoning": reasoning,
    "score": score
  }

def run_eval(dataset):
    """Loads the dataset and calls run_test_case with each case"""
    results = []

    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)

    average_score = mean([result["score"] for result in results])
    print(f"Average score: {average_score}\n")

    return results

with open("cases.json", "r") as dataset:
  data = json.load(dataset);

results = run_eval(data)
print(results)
