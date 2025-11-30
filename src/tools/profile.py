import pandas as pd
import json

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
    

if __name__ == '__main__':
    print(data_profiler('data\\BlackFriday_Sales.csv'))