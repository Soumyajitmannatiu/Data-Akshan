from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from google.adk.sessions.database_session_service import DatabaseSessionService
from google.genai import types
from src.agents import code_writer,planner,profiler
from src.tools.state import add_context_variable,add_user_intent
from src.utils.AgentConfig import APP_NAME,retry_config
import os,asyncio,dotenv

dotenv.load_dotenv()

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

db_url = "sqlite+aiosqlite:///my_agent_data.db"  # Local SQLite file
session_service = DatabaseSessionService(db_url=db_url)

orchestrator_agent=Agent(name='Orchestrator_Agent',
                         model=Gemini(model='gemini-2.0-flash',retry_options=retry_config),
                         instruction=""" You are an Orchestrator agent. You're an expert data analyzer and planner.
                         ***IMPORTANT INSTRUCTIONS***
                         1. The file given by the user would be present inside the .\\data\\ directory.
                         2. You're work is divided into the following steps:
                         - Start by saving the user's intention for analysis by calling the `add_user_intent` tool.
                         - Then, call the `profiler` to create a profile of the data.
                         - After successfully receiving the `data_profile` there are 3 types of taks you have to perform, ['Clean','Analyze','Visualize']. Follow this order of tasks.
                         - To execute each of these steps follow the following sub-steps
                            a. Create a context variable for the "task" that is to done next by calling the `add_context_variable` tool.
                            b. Call the `planner` to get a clear plan of what to do in this step.
                            c. Once the plan is received, call `code_writer` to execute the plan.
                            d. Repeat the above sub-steps for each step.
                         - Finally return a complete report of the analysis along with the path of files saved.
                        """,
                        tools=[AgentTool(agent=code_writer),AgentTool(agent=profiler),AgentTool(agent=planner),FunctionTool(func=add_context_variable),FunctionTool(func=add_user_intent)]
                         )

async def main():
    runner= Runner(app_name=APP_NAME,session_service=session_service,agent=orchestrator_agent)
    response= await runner.run_debug('Find the patterns in salary with age and degree in "salary_table.csv"')
    print(response)

if __name__=="__main__":
    try:
        gemini_api_key=os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise KeyError("Check API key")
        os.environ['GEMINI_API_KEY']=gemini_api_key
        print("Gemini Configured")
    except Exception as e:
        print("Error",e)
    asyncio.run(main())