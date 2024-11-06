from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
import praw
import yfinance as yf
import time
import json
import signal
import sys


directory = "trading_bot_data"

# Create the directory if it doesn't exist
if not os.path.exists(directory):
    os.makedirs(directory)
    DATA_FILE = os.path.join(directory, "trading_data.json")


# File path to save and load data
DATA_FILE = os.path.join(directory, "trading_data.json")


def signal_handler(sig, frame):
    print("Exiting and saving data...")
    save_data()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
def getposts():
    global reddit
    subreddit = reddit.subreddit("wallstreetbets")
    subreddit2 = reddit.subreddit("stocks")
    subreddit3 = reddit.subreddit("stockmarket")
    top_posts = subreddit.new(limit=500)
    top_posts2 = subreddit2.new(limit=500)
    top_posts3 = subreddit3.new(limit = 500)
    return top_posts,top_posts2,top_posts3


def trade(compound_score,positive_score,negative_score):
   
    global total_balance
    for key in compound_score:
        if compound_score[key] > 1.5:
            total_balance = total_balance - ticker[key]*2
            total_stocks[key] = total_stocks[key] + 2
            print("Current balance after Purchasing",key,total_balance,"$")
        elif compound_score[key] < 1:
            if total_stocks[key]>1:
                total_balance = total_balance + ticker[key]*2
                total_stocks[key] = total_stocks[key] + -2
                
                print("Balance after selling:",key,total_balance,"$")
            else:
                print(f"{key}: is currently zero")
                print("Current Balance",total_balance,"$")



def SentimentAnalyser(new_posts):
    global compound_score,positive_score,negative_score
    compound_score = {}
    positive_score = {}
    negative_score = {}
    print("Compound Score of each Stocks!")
    for top in new_posts:
        c = 0
        compound = analyzer.polarity_scores(top.title)
        split = top.title.split()
        

        for i in split:
            if i.lower() in symbols_dict:
                c=1
            if c==1:
               
                test = symbols_dict[i.lower()]
                if test not in compound_score:
                    compound_score[test] = 0
                    positive_score[test] = 0
                    negative_score[test] = 0
                compound_score[test] += compound['compound']
                positive_score[test] += compound['pos']
                negative_score[test] += compound['neg']
                ticker[test]=0
                print(symbols_dict[i.lower()],compound_score[test]," ")
            c=0
    return compound_score,positive_score,negative_score

def getTodayStockPrice():
    for key in ticker:
        stock = yf.Ticker(key)
        data = stock.history(period="1d")
        ticker[key] = float(data['Close'].iloc[-1])

    print("Today's Stock Prices:")
    for price in ticker:
        print(f"{price}: {ticker[price]}")

def save_data():
    try:
        data = {
            "seen_posts": list(seen_posts),
            "total_stocks": total_stocks,
            "total_balance": total_balance,
        }
        with open(DATA_FILE, 'w') as file:
            json.dump(data, file)
        print("Data saved successfully.")
    except Exception as e:
        print(f"Error saving data: {e}")


def load_data():
    global seen_posts, total_stocks, total_balance
    try:
        with open(DATA_FILE, 'r') as file:
            data = json.load(file)
            seen_posts = set(data.get("seen_posts", []))
            total_stocks = data.get("total_stocks", total_stocks)
            total_balance = data.get("total_balance", initial_balance)
        print("Data loaded successfully.")
    except FileNotFoundError:
        print("No saved data found, starting fresh.")
    except Exception as e:
        print(f"Error loading data: {e}")



def runbot():
    global reddit,seen_posts
    reddit = praw.Reddit(
        client_id = 'GJmAuNIY6YqPB0eZHuZMaQ',
        client_secret = 'yPvM7U74zTXTMF3f9_8I-4rOSGb_oQ',
        user_agent="posts by elite"
    )
    while True:
        print("Fetching Posts and analyzing Sentiment")
        posts1,posts2,posts3 = getposts()
        new_posts = [post for post in posts1 if post.id not in seen_posts]
        temp1=[post for post in posts2 if post.id not in seen_posts]
        temp2 = [post for post in posts3 if post.id not in seen_posts]
        new_posts.extend(temp1)
        new_posts.extend(temp2)
      
        if new_posts:
            print("New Posts detected")
            compound_score,positive_score,negative_score = SentimentAnalyser(new_posts)
            print("Fetching Today's Stock prices")
            getTodayStockPrice()
            print("Executing Trade")
            trade(compound_score,positive_score,negative_score)
            print("Sleeping for 60 seconds")
            seen_posts.update(post.id for post in new_posts)
            time.sleep(60)
            save_data()
        else:
            print("No new Posts")
            time.sleep(60)


symbols_dict = {
    "apple": "AAPL", "microsoft": "MSFT", "alphabet (class a)": "GOOGL", "google":"GOOGL",
    "alphabet (class c)": "GOOG", "amazon": "AMZN", "nvidia": "NVDA",
    "berkshire hathaway (class b)": "BRK.B", "meta": "META", "tesla": "TSLA",
    "unitedhealth group": "UNH", "exxon mobil": "XOM", "johnson & johnson": "JNJ",
    "jpmorgan chase": "JPM", "visa": "V", "procter & gamble": "PG",
    "eli lilly": "LLY", "mastercard": "MA", "home depot": "HD",
    "chevron": "CVX", "abbvie": "ABBV", "merck": "MRK",
    "pepsico": "PEP", "coca-cola": "KO", "pfizer": "PFE",
    "broadcom": "AVGO", "costco": "COST", "mcdonald's": "MCD",
    "nvda": "NVDA", "thermo fisher": "TMO", "nike": "NKE",
    "salesforce": "CRM", "oracle": "ORCL", "t-mobile us": "TMUS",
    "settle": "SPLK", "abbott": "ABT", "wells fargo": "WFC",
    "goldman sachs": "GS", "service now": "NOW", "target": "TGT",
    "caterpillar": "CAT", "honeywell": "HON", "ibm": "IBM",
    "adobe": "ADBE", "qualcomm": "QCOM", "intuit": "INTU",
    "airbnb": "ABNB", "boston scientific": "BSX", "paypal": "PYPL",
    "shopify": "SHOP", "dell technologies": "DELL", "snowflake": "SNOW",
    "roku": "ROKU", "snap": "SNAP", "twilio": "TWLO",
    "zoom": "ZM", "okta": "OKTA", "amd": "AMD", "intel": "INTC",'lulu':'LULU','pltr':'PLTR',
    "aapl": "AAPL",
    "msft": "MSFT",
    "googl": "GOOGL",
    "goog": "GOOG",
    "amzn": "AMZN",
    "nvda": "NVDA",
    "brk.b": "BRK.B",
    "meta": "META",
    "tsla": "TSLA",
    "unh": "UNH",
    "xom": "XOM",
    "jnj": "JNJ",
    "jpm": "JPM",
    "v": "V",
    "pg": "PG",
    "lly": "LLY",
    "ma": "MA",
    "hd": "HD",
    "cvx": "CVX",
    "abbv": "ABBV",
    "mrk": "MRK",
    "pep": "PEP",
    "ko": "KO",
    "pfe": "PFE",
    "avgo": "AVGO",
    "cost": "COST",
    "mcd": "MCD",
    "tmo": "TMO",
    "nke": "NKE",
    "crm": "CRM",
    "orcl": "ORCL",
    "tmus": "TMUS",
    "splk": "SPLK",
    "abt": "ABT",
    "wfc": "WFC",
    "gs": "GS",
    "now": "NOW",
    "tgt": "TGT",
    "cat": "CAT",
    "hon": "HON",
    "ibm": "IBM",
    "adbe": "ADBE",
    "qcom": "QCOM",
    "intu": "INTU",
    "abnb": "ABNB",
    "bsx": "BSX",
    "pypl": "PYPL",
    "shop": "SHOP",
    "dell": "DELL",
    "snow": "SNOW",
    "roku": "ROKU",
    "snap": "SNAP",
    "twlo": "TWLO",
    "zm": "ZM",
    "okta": "OKTA",
    "amd": "AMD",
    "intc": "INTC",
    "lulu": "LULU",
    "pltr": "PLTR"
}




total_stocks = {


    'AAPL': 0, 'MSFT': 0, 'GOOGL': 0, 'GOOG': 0, 'AMZN': 0, 'NVDA': 0, 'BRK.B': 0,
    'META': 0, 'TSLA': 0, 'UNH': 0, 'XOM': 0, 'JNJ': 0, 'JPM': 0, 'V': 0, 'PG': 0,
    'LLY': 0, 'MA': 0, 'HD': 0, 'CVX': 0, 'ABBV': 0, 'MRK': 0, 'PEP': 0, 'KO': 0,
    'PFE': 0, 'AVGO': 0, 'COST': 0, 'MCD': 0, 'TMO': 0, 'NKE': 0, 'CRM': 0,
    'ORCL': 0, 'TMUS': 0, 'SPLK': 0, 'ABT': 0, 'WFC': 0, 'GS': 0, 'NOW': 0, 'TGT': 0,
    'CAT': 0, 'HON': 0, 'IBM': 0, 'ADBE': 0, 'QCOM': 0, 'INTU': 0, 'ABNB': 0, 'BSX': 0,
    'PYPL': 0, 'SHOP': 0, 'DELL': 0, 'SNOW': 0, 'ROKU': 0, 'SNAP': 0, 'TWLO': 0, 'ZM': 0,
    'OKTA': 0, 'AMD': 0, 'INTC': 0, 'LULU': 0, 'PLTR': 0



}



initial_balance = 10000
netprofit = 0
dailyprofit = 0
total_balance = initial_balance
analyzer = SentimentIntensityAnalyzer()
ticker={}
seen_posts = set()
signal.signal(signal.SIGINT, signal_handler)
load_data()
runbot()