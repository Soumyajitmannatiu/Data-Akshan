from src.tools.sandbox import execute_sandboxed_code
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools.function_tool import FunctionTool
from google.genai import types

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

cleaner_agent=Agent(
    name='Cleaner_Agent',
    description='Agent that cleans a given file using a function tool based on the data profile provided',
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction= """***MISSION***
You are an expert Data Cleaner Agent. Your goal is to take the raw dataset file and create a clean version.
***EXECUTION STEPS***
1.  **Plan:** Based *only* on the Data Profile {data_profile}, list the specific cleaning steps you will take (e.g., "Convert column 'A' to numeric," "Impute missing values in 'B' with the median").
2.  **Code:** Generate Python pandas code.
    * Load raw data file into a DataFrame.
    * Perform the planned cleaning steps.
    * Save the final DataFrame to cleaned_<raw_filename> using `index=False`.(eg: input file-'sales.csv' output file:'cleaned_sales.csv')
3.  **Execute:** Call the `execute_sandboxed_code` tool to run the generated code.
4.  **Verify & Retry:** If the tool returns `status_code: 1` (error), analyze the `stderr`, fix your Python code, and call the tool again.
5.  **Final Report:** Once `status_code: 0`, respond *only* with the final cleaned filename: cleaned_<raw_filename>.
""",
tools=[FunctionTool(func=execute_sandboxed_code)],
output_key='cleaned_data_paths'
)