from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools.function_tool import FunctionTool
from google.genai import types
from src.tools.profile import data_profiler
import asyncio

import sys
import os
import dotenv

dotenv.load_dotenv()

try:
    gemini_api_key=os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        raise ValueError("Check API key")
    os.environ['GEMINI_API_KEY']=gemini_api_key
    print("Gemini Configured")
except Exception as e:
    print("Error",e)

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

profiler_agent=Agent(
    name='Profiler_Agent',
    description='Agent that proflies given data (in .csv format) using a fucntion tool',
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are an expert data profiler.Don't analyze the data yourself instead use the data_profiler tool and interpretthe output to create a profile. It should contain the following pionts,
    1. Column names and their inferred types (group the columns of same type).  
    2. Percentage of missing values for each column.
    3. Cardinality (number of unique values) for categorical columns.
    3. A summary of potential issues (e.g., "Column 'Sale_Amount' is an 'object' type but looks numeric. Column 'Order_Date' is an 'object' but looks like a date.").
""",
tools=[FunctionTool(func=data_profiler)],
output_key='data_profile'
)

async def main():
    runner= InMemoryRunner(agent=profiler_agent)
    response= await runner.run_debug('I want to understand the structure of the data in the file-"BlackFriday_Sales.csv" inside the data directory.')
    print(response)
if __name__=="__main__":
    # if sys.platform == 'win32':
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())