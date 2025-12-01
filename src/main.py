from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from google.adk.sessions.database_session_service import DatabaseSessionService
from google.genai import types
from src.agents import cleaner_agent,profiler_agent
from src.tools.profile import get_profile
from src.utils.AgentConfig import APP_NAME,USER_ID,SESSION_ID
import os,asyncio

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

db_url = "sqlite+aiosqlite:///my_agent_data.db"  # Local SQLite file
session_service = DatabaseSessionService(db_url=db_url)

orchestrator_agent=Agent(name='Orchestrator_Agent',
                         model=Gemini(retry_options=retry_config),
                         instruction=""" You are an Orchestrator agent. Yoe're an expert data analyzer and planner.
                         ***IMPORTANT INSTRUCTIONS***
                         1. The file given by the user would be present inside the data directory.
                         2. You're work is divided into 5 steps:
                            - First, you MUST profile data by calling `Profiler_Agent` tool.
                            - After receiving the data profile, call the `Cleaner_Agent` tool to clean the data based on the data profile.
                            - Next, call the `Analyzer_Agent` tool to do an analysis on the cleaned data based on the user's request.
                            - After
                        """,
                        tools=[AgentTool(agent=cleaner_agent),AgentTool(agent=profiler_agent)]
                         )

async def main():
    runner= Runner(app_name=APP_NAME,session_service=session_service,agent=orchestrator_agent)
    response= await runner.run_debug('I want to understand the structure of the data in the file-"BlackFriday_Sales.csv" inside the data directory.')
    print(response)

if __name__=="__main__":
    # if sys.platform == 'win32':
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        gemini_api_key=os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise ValueError("Check API key")
        os.environ['GEMINI_API_KEY']=gemini_api_key
        print("Gemini Configured")
    except Exception as e:
        print("Error",e)
    asyncio.run(main())