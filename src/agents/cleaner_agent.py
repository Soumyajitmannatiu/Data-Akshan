from tools.sandbox import execute_sandboxed_code
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
    description='Agent that cleans given data (in .csv format) using a fucntion tool',
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are an expert Data cleaner. You're job is to clean data by writing a custom python program using:
1. A data profile that gives the idea of the structure of the data.
2. The execute_sandboxed_code tool to execute the code gsenerated.
""",
tools=[execute_sandboxed_code]
)