from typing import List;
from main import chat, add_user_message
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from jinja2 import Template

""" Define our prompt evaluator """
class PromptEvaluator:

  """constructor function"""
  def __init__(self, max_concurrent_tasks: int = 3):
    self.max_concurrent_tasks = max_concurrent_tasks
    
    pass

  """ Singleton Instane """
  @staticmethod
  def getInstance() -> PromptEvaluator:
    instance: PromptEvaluator = None;
    if( instance == None ): instance = PromptEvaluator()

    return instance;


  def generate_dataset(self, task_description: str, prompt_inputs_spec: dict, num_cases: int , output_file: str = "dataset.json" ):
    unique_ideas = self.generate_unique_ideas(task_description, prompt_inputs_spec, num_cases)

    dataset = []
    completed = 0
    total = len(unique_ideas)
    last_reported_percentage = 0

    with ThreadPoolExecutor(max_workers=4) as t:
      future = {
        t.submit(
          self.generate_test_case,
          task_description,
          prompt_inputs_spec,
          idea
        ): idea for idea in unique_ideas
      }

      for f in as_completed(future):
        result = f.result()
        completed += 1
        dataset.append({future[f]: result})
      
    with open(output_file, "w") as o:
      json.dump(dataset, o, indent=2)
  
  def generate_test_case(self, task_description: str, prompt_inputs_spec: dict, idea: str):
    messages = []
    prompt = """
        Generate a single detailed test case for a prompt evaluation based on:
        
        <task_description>
        {{task_description}}
        </task_description>
        
        <specific_idea>
        {{idea}}
        </specific_idea>
        
        <allowed_input_keys>
        {{allowed_keys}}
        </allowed_input_keys>
        
        Output Format:
        ```json
        {
            "prompt_inputs": {
              {{example_prompt_inputs}}
            },
            "solution_criteria": ["criterion 1", "criterion 2", ...] // Concise list of criteria for evaluating the solution, 1 to 4 items
        }
        ```
        
        IMPORTANT REQUIREMENTS:
        - You MUST ONLY use these exact input keys in your prompt_inputs: {allowed_keys}        
        - Do NOT add any additional keys to prompt_inputs
        - All keys listed in allowed_input_keys must be included in your response
        - Make the test case realistic and practically useful
        - Include measurable, concise solution criteria
        - The solution criteria should ONLY address the direct requirements of the task description and the generated prompt_inputs
        - Avoid over-specifying criteria with requirements that go beyond the core task
        - Keep solution criteria simple, focused, and directly tied to the fundamental task
        - The test case should be tailored to the specific idea provided
        - Quick to solve without requiring extensive computation or multi-step processing
        - Solvable with no more than 400 tokens of output
        - DO NOT include any fields beyond those specified in the output format

        Here's an example of a sample input with an ideal output:
        <sample_input>
        <sample_task_description>
        Extract topics out of a passage of text
        </sample_task_description>
        <sample_specific_idea>
        Testing with a text that contains multiple nested topics and subtopics (e.g., a passage about renewable energy that covers solar power economics, wind turbine technology, and policy implications simultaneously)
        </sample_specific_idea>

        <sample_allowed_input_keys>
        "content"
        </sample_allowed_input_keys>
        </sample_input>
        <ideal_output>
        ```json
        {
            "prompt_inputs": {
                "content": "The transition to renewable energy encompasses numerous interdependent dimensions. Solar photovoltaic technology has seen dramatic cost reductions, with panel efficiency improving 24% since 2010 while manufacturing costs declined by 89%, making it economically competitive with fossil fuels in many markets. Concurrently, wind energy has evolved through innovative turbine designs featuring carbon-fiber composite blades and advanced control systems that increase energy capture by 35% in low-wind conditions."
            },
            "solution_criteria": [
                "Includes all topics mentioned"   
            ]
        }
        ```
        </ideal_output>
        This is ideal output because the solution criteria is concise and doesn't ask for anything outside of the scope of the task description.
        """
    
    output_schema = {
       "format": {
          "type": "json_schema",
          "schema": {
             "type": "object",
             "properties": {
                "prompt_inputs": { 
                  "type": "object",
                  "properties": { key: { "type": "string", "description": value } for key, value in prompt_inputs_spec.items() },
                  "required": [ key for key in prompt_inputs_spec ],
                  "additionalProperties": False
                },
                "solution_criteria": {
                  "type": "array",
                  "items": { "type": "string" }
                }
             },
             "required": ["solution_criteria", "prompt_inputs"],
             "additionalProperties": False
          }
       }
    }

    allowed_keys = ", ".join([f"{key}" for key in prompt_inputs_spec.keys()])
    example_prompt_inputs = ''
    for key, value in prompt_inputs_spec.items():
      example_prompt_inputs += f"key: {key}, EXAMPLE VALUE // {value} \n, "

    example_prompt_inputs.replace('\n', '\\n')

    keywords = {
      "allowed_keys": allowed_keys,
      "example_prompt_inputs": example_prompt_inputs,
      "task_description": task_description,
      "idea": idea
    }

    add_user_message(messages, self.render(prompt, keywords))
    response = chat(messages, output_schema)
    return json.loads(response)
     
  def generate_unique_ideas(self, task_description: str, prompt_inputs_spec: dict, num_cases: int ) -> List[str]:
    messages = []

    prompt = """
      Generate {{num_cases}} unique, diverse ideas for testing a prompt that accomplishes this task:
      
      <task_description>
      {{task_description}}
      </task_description>

      The prompt will receive the following inputs
      <prompt_inputs>
      {{prompt_inputs_spec}}
      </prompt_inputs>
      
      Each idea should represent a distinct scenario or example that tests different aspects of the task.
      
      Output Format:
      Provide your response as a structured JSON array where each item is a brief description of the idea.
      
      Example:
      ```json
      { 
        "unique_ideas": 
            [
                "Testing with technical computer science terminology",
                "Testing with medical research findings",
                "Testing with complex mathematical concepts",
                ...
            ]
      }
      ```
      
      Ensure each idea is:
      - Clearly distinct from the others
      - Relevant to the task description
      - Specific enough to guide generation of a full test case
      - Quick to solve without requiring extensive computation or multi-step processing
      - Solvable with no more than 400 tokens of output

      Remember, only generate {{num_cases}} unique ideas
      """
    
    # Step3 - Eliminate the curly brackets
    mutated_input_spec = ''
    for key, value in prompt_inputs_spec.items():
      msg = f"{key}: {value}, "
      mutated_input_spec += msg
    
    template = self.render(prompt, {
       "num_cases": num_cases,
       "task_description": task_description,
       "prompt_inputs_spec": mutated_input_spec
    })
    

    # step 4: Get an output config
    output_config = {
      "format": {
        "type": "json_schema",
        "schema": {
          "type": "object",
          "properties": {
            "unique_ideas": { "type": "array", "items": { "type": "string" } }
          },
          "required": ["unique_ideas"],
          "additionalProperties": False
        }
      }
    }

    add_user_message(messages, template)
    response = chat(messages, output_config, temperature=0.8)

    output = json.loads(response)
    return output["unique_ideas"]

  def run_evaluation(self):
    pass;

  def render(self, template_string, variables):
      # placeholders = findall(r"{([^{}]+)}", template_string)

      # result = template_string
      # for placeholder in placeholders:
      #     if placeholder in variables:
      #         result = result.replace(
      #             "{" + placeholder + "}", str(variables[placeholder])
      #         )

      # return result.replace("{{", "{").replace("}}", "}")
      template: Template = Template(template_string)
      return template.render(variables)
  
evaluator = PromptEvaluator.getInstance()
params = [
      "Write a compact, concise 1 day meal plan for a single athlete", 

      {
          "height": "Athlete's height in cm",
          "weight": "Athlete's weight in kg",
          "goal": "Goal of the athlete",
          "restrictions": "Dietary restrictions of the athlete",
      },

      3
      # "Testing with a tall, heavyweight strength athlete (190cm, 95kg) with a muscle-building goal and no dietary restrictions to verify adequate protein distribution across 3 meals"
    ]

print(evaluator.generate_dataset(*params))