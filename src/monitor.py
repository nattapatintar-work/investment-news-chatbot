import os 
import json 
import logging 
from datetime import datetime
from pathlib import Path

print("FILE IS RUNNING")
# points to a folder named "logs" + create the folder if folder already exists — do not crash, just continue
Path('logs').mkdir(exist_ok = True)

#__name__ is a built-in Python variable that automatically contains the name of the current file.

logging.basicConfig(
    filename = 'logs/chatbot.log', #logs/chatbot.log    ← every log entry gets appended here
    level = logging.INFO, #what level of message we save 
    format="%(asctime)s — %(levelname)s — %(message)s"
    #%(asctime)s            %(levelname)s        %(message)s
    #timestamp              log level            your actual message
) # Sets up the logging system — runs once when the file loads.
logger = logging.getLogger(__name__) # gets a logger object

COST_PER_INPUT_TOKEN  = 0.80  / 1_000_000   # $0.80 per 1M input tokens
COST_PER_OUTPUT_TOKEN = 4.00  / 1_000_000   # $4.00 per 1M output tokens

def calculate_cost(input_tokens : int , output_tokens :int) -> float:
    """
    Calculate the cost of a single Claude API call.

    Args:
        input_tokens  : number of input tokens used
        output_tokens : number of output tokens used

    Returns:
        cost in USD as a float
    """
    input_cost = COST_PER_INPUT_TOKEN * input_tokens
    output_cost = COST_PER_OUTPUT_TOKEN * output_tokens
    return round(input_cost + output_cost,5)

def log_request(ticker : str , num_articles : int , total_tokens :int ,success : bool ) -> dict:  
    """
    Log a pipeline request with usage and cost data.

    Args:
        ticker       : stock symbol e.g. "NVDA"
        num_articles : number of articles processed
        total_tokens : total tokens used across all articles
        success      : whether the request succeeded

    Returns:
        dict with request metadata
    """

    input_tokens =int(total_tokens * 0.6)
    output_tokens =int(total_tokens * 0.4)
    cost = calculate_cost(input_tokens ,output_tokens)

    #A log entry is a record of one thing that happened in your chatbot.
    log_entry = {   
    "timestamp"   : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),   # when it happened
    "ticker"      : ticker,                   # what they searched
    "num_articles": num_articles,                         # how many articles processed
    "total_tokens": total_tokens,                       # how many tokens used
    "cost_usd"    : cost,                   # how much it cost
    "success"     : success                       # did it work or fail
    }

    if success:
        logger.info(json.dumps(log_entry)) #Converts your Python dictionary into a JSON string:
    else:
        logger.error(json.dumps(log_entry)) #
    #json.dumps()    →  dictionary to string   (no file created)
    #json.dump()     →  dictionary to file     (creates a file)
    #json.dumps()   →  makes a dictionary look like text
                  #so it can be written into a .log file
                  #no new file is created
    return log_entry

def log_error(ticker : str , error : Exception ) -> None:
    error_entry = {
    "timestamp"   : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),   # when it happened
    "ticker"      : ticker,                   # what they searched
    "error": type(error).__name__,                         # The type of error that happened:

    'error_msg': str(error)
    }
    logger.error(json.dumps(error_entry)) 

def get_usage_stats() -> dict:
    """
    Read the log file and return usage statistics.

    Returns:
        dict with total requests, total tokens, total cost
    logs/chatbot.log has 1000 lines
      ↓
    get_usage_stats() reads every line
      ↓
    returns:
    {
        "total_requests" : 1000,
        "total_tokens"   : 893000,
        "total_cost_usd" : 4.23,
        "failed_requests": 12
    }
    """
    log_file = Path('logs/chatbot.log')
    if not log_file.exists():
        return {
            'total_request' : 0 ,
            'total_tokens' : 0 ,
            'total_cost_usd' : 0 ,
            'failed_request' : 0
        }
    
    total_requests  = 0
    total_tokens    = 0
    total_cost      = 0.0
    failed_requests = 0

    with open(log_file , 'r') as f:
        for line in f:
            try:
                json_start = line.index("{")
                entry = json.loads(line[json_start:])
                total_requests +=1
                total_tokens += entry.get('total_tokens', 0)
                total_cost += entry.get('cost_usd',0)

                if not entry.get('success', True):
                    failed_requests +=1
            
            except (ValueError, json.JSONDecodeError):
                continue
    return {
        'total_request': total_requests,
        'total_tokens': total_tokens,
        'total_cost_usd': round(total_cost,4),
        'failed_request': failed_requests,    
            }

if __name__ == '__main__' :
    print("Testing monitor...")
    entry = log_request(
        ticker = 'NVDA',
        num_articles = 3 ,
        total_tokens = 893,
        success      = True
    )
    print('Log entry:', entry)

    stats = get_usage_stats()
    print("Usage stats:", stats)
    