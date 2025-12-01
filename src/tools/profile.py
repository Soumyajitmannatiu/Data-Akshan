import pandas as pd
import json
from src.utils.AgentConfig import APP_NAME,USER_ID,SESSION_ID
from google.adk.sessions.base_session_service import BaseSessionService
def data_profiler(input_file:str)->dict:
    """
    Profiles data present in a csv file. Gives context around data given using pandas based operations like df.describe,df.columns and etc.
    Args:
        input_file: Directory of the input csv file.
    Returns:
        Dictionary with status and profile for the data.
        Success: {"status":"success", "profile":A json string that holds the profiled data}
        Error: {"status": "error","message": "File not found" }
    """
    try:
        df= pd.read_csv(input_file)
        #Profiling operations
        profile = {
            "columns": [{column:str(df[column].dtypes)} for column in df.columns],
            "index": str(df.index),
            "description": df.describe().to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "head": df.head(2).to_dict()
        }
        return {"status":"success","profile":json.dumps(profile)}
    except Exception as e:
        return {"status": "error","message": e}
    
async def get_profile(session_service:BaseSessionService,app_name:str=APP_NAME,user_id:str=USER_ID,session_id:str=SESSION_ID):   
    """
    Tool return the data
    """
    session= await session_service.get_session(app_name=app_name,session_id=session_id,user_id=user_id)
    if session:
        current_profile= session.state.get('data_profile','No Profile created yet.')
    return current_profile

if __name__ == '__main__':
    print(data_profiler('data\\BlackFriday_Sales.csv'))