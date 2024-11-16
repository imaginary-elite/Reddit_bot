from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from tabulate import tabulate
import os
import praw
import yfinance as yf
import time
import json
import signal
import sys


directory = "trading_bot_data"
if not os.path.exists(directory):
    os.makedirs(directory)
DATA_FILE = os.path.join(directory, "trading_data.json")

def signal_handler(sig, frame):
    print("\nExiting and saving data...")
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
    top_posts3 = subreddit3.new(limit=500)
    return top_posts, top_posts2, top_posts3

def trade(compound_score, positive_score, negative_score):
    global total_balance, profit_loss 
    trade_summary = []

    total_profit = 0
    total_loss = 0

    for key in compound_score:
        if compound_score[key] > 1.5:  # Buy condition (positive sentiment)
            total_balance -= ticker[key] * 2
            total_stocks[key] += 2
            if key not in profit_loss:
                profit_loss[key] = {'purchase_price': ticker[key], 'quantity': 2}  # Record purchase price and quantity
            else:
                profit_loss[key]['quantity'] += 2  # If stock already bought, just increase the quantity
            trade_summary.append(f"Purchased {key}: New balance = ${total_balance:.2f}")
        elif compound_score[key] < 1:  # Sell condition (negative sentiment)
            if total_stocks[key] > 1:
                total_balance += ticker[key] * 2
                total_stocks[key] -= 2

                # Calculate profit/loss based on the sale price and the purchase price
                purchase_price = profit_loss[key]['purchase_price']
                profit_loss_value = (ticker[key] - purchase_price) * 2  # Profit or loss for 2 stocks sold
                profit_loss[key]['quantity'] -= 2  # Update the quantity of remaining stocks
                
                # Update the total profit/loss
                if profit_loss_value > 0:
                    total_profit += profit_loss_value  # Add profit
                else:
                    total_loss += abs(profit_loss_value)  # Add loss

    print("\nTrade Execution Summary")
    for summary in trade_summary:
        if "Purchased" in summary: 
            print(summary)

    holdings_table = []
    total_stock_value = 0 
    for symbol, quantity in total_stocks.items():
        if quantity > 0:
            stock_value = quantity * ticker[symbol]
            individual_profit_loss = profit_loss.get(symbol, {'purchase_price': 0, 'quantity': 0})
            holdings_table.append([symbol, quantity, f"${stock_value:.2f}"])

            total_stock_value += stock_value  

    print("\nCurrent Stock Holdings")
    print(tabulate(holdings_table, headers=["Stock", "Quantity", "Potential Sale Value (USD)"], tablefmt="grid"))

    # Print total value of holdings
    print(f"\nTotal Value of Current Holdings: ${total_stock_value:.2f}")

    # Print profit and loss separately
    print(f"\nProfit: ${total_profit:.2f}")
    print(f"Loss: ${total_loss:.2f}")

    # Now print total profit/loss
    total_profit_loss = total_profit - total_loss
    print(f"\nTotal Profit/Loss (All Stocks): ${total_profit_loss:.2f}")

def SentimentAnalyser(new_posts):
    global compound_score, positive_score, negative_score
    compound_score = {}
    positive_score = {}
    negative_score = {}

    for top in new_posts:
        compound = analyzer.polarity_scores(top.title)
        split = top.title.split()
        for word in split:
            if word.lower() in symbols_dict:
                stock_symbol = symbols_dict[word.lower()]
                if stock_symbol not in compound_score:
                    compound_score[stock_symbol] = 0
                    positive_score[stock_symbol] = 0
                    negative_score[stock_symbol] = 0
                compound_score[stock_symbol] += compound['compound']
                positive_score[stock_symbol] += compound['pos']
                negative_score[stock_symbol] += compound['neg']
                ticker[stock_symbol] = 0

    # Prepare and print sentiment score table
    table_data = [
        [symbol, compound_score[symbol], positive_score[symbol], negative_score[symbol]]
        for symbol in compound_score
    ]
    print("\nSentiment Scores for each Stock:")
    print(tabulate(table_data, headers=["Stock", "Compound Score", "Positive Score", "Negative Score"], tablefmt="grid"))

    return compound_score, positive_score, negative_score

# Get today's stock prices
def getTodayStockPrice():
    stock_price_table = []

    for key in ticker:
        stock = yf.Ticker(key)
        data = stock.history(period="1d")
        
        if not data.empty:
            ticker[key] = float(data['Close'].iloc[-1])
            stock_price_table.append([key, f"${ticker[key]:.2f}"])
        else:
            stock_price_table.append([key, "No data (may be delisted)"])

    # Print stock prices table
    print("\nStock Prices")
    print(tabulate(stock_price_table, headers=["Stock", "Price (USD)"], tablefmt="grid"))

# Save data to a JSON file
def save_data():
    try:
        data = {
            "seen_posts": list(seen_posts),
            "total_stocks": total_stocks,
            "total_balance": total_balance,
            "profit_loss": profit_loss  # Store profit/loss data
        }
        with open(DATA_FILE, 'w') as file:
            json.dump(data, file)
        print("Data saved successfully.")
    except Exception as e:
        print(f"Error saving data: {e}")

# Load data from JSON file
def load_data():
    global seen_posts, total_stocks, total_balance, profit_loss
    try:
        with open(DATA_FILE, 'r') as file:
            data = json.load(file)
            seen_posts = set(data.get("seen_posts", []))
            total_stocks = data.get("total_stocks", total_stocks)
            total_balance = data.get("total_balance", initial_balance)
            profit_loss = data.get("profit_loss", {})  # Load profit/loss data
        print("Data loaded successfully.")
    except FileNotFoundError:
        print("No saved data found, starting fresh.")
    except Exception as e:
        print(f"Error loading data: {e}")
# Run the bot
def runbot():
    global reddit, seen_posts
    reddit = praw.Reddit(
        client_id='GJmAuNIY6YqPB0eZHuZMaQ',
        client_secret='yPvM7U74zTXTMF3f9_8I-4rOSGb_oQ',
        user_agent="posts by elite"
    )
    while True:
        print("\nFetching Posts and Analyzing Sentiment...")
        posts1, posts2, posts3 = getposts()
        new_posts = [post for post in posts1 if post.id not in seen_posts]
        new_posts.extend([post for post in posts2 if post.id not in seen_posts])
        new_posts.extend([post for post in posts3 if post.id not in seen_posts])

        if new_posts:
            print("\nNew Posts Detected - Analyzing Sentiment")
            compound_score, positive_score, negative_score = SentimentAnalyser(new_posts)
            print("\nFetching Today's Stock Prices")
            getTodayStockPrice()
            print("\nExecuting Trades Based on Sentiment")
            trade(compound_score, positive_score, negative_score)
            print("\nSleeping for 60 seconds...")
            seen_posts.update(post.id for post in new_posts)
            time.sleep(60)
            save_data()
        else:
            print("No New Posts Found, Sleeping for 60 seconds...")
            time.sleep(60)

# Stock symbols and other setup variables
symbols_dict = {
    "apple": "AAPL", "microsoft": "MSFT", "alphabet (class a)": "GOOGL", 
    "google": "GOOGL", "alphabet (class c)": "GOOG", "amazon": "AMZN", 
    "nvidia": "NVDA", "berkshire hathaway (class b)": "BRK.B", "meta": "META", 
    "tesla": "TSLA", "unitedhealth group": "UNH", "exxon mobil": "XOM",
    "johnson & johnson": "JNJ", "jpmorgan chase": "JPM", "visa": "V", 
    "procter & gamble": "PG", "eli lilly": "LLY", "mastercard": "MA", 
    "home depot": "HD", "chevron": "CVX", "abbvie": "ABBV", "merck": "MRK",
    "pepsico": "PEP", "coca-cola": "KO", "pfizer": "PFE", "broadcom": "AVGO", 
    "costco": "COST", "mcdonald's": "MCD", "thermo fisher": "TMO", "nike": "NKE",
    "salesforce": "CRM", "oracle": "ORCL", "t-mobile us": "TMUS", "settle": "SPLK", 
    "abbott": "ABT", "wells fargo": "WFC", "goldman sachs": "GS", "service now": "NOW", 
    "target": "TGT", "caterpillar": "CAT", "honeywell": "HON", "ibm": "IBM", 
    "adobe": "ADBE", "qualcomm": "QCOM", "intuit": "INTU", "airbnb": "ABNB", 
    "boston scientific": "BSX", "paypal": "PYPL", "shopify": "SHOP", "dell technologies": "DELL",
    "snowflake": "SNOW", "roku": "ROKU", "snap": "SNAP", "twilio": "TWLO", "zoom": "ZM", 
    "okta": "OKTA", "amd": "AMD", "intel": "INTC", 'lulu': 'LULU', 'pltr': 'PLTR'
}

total_stocks = {symbol: 0 for symbol in symbols_dict.values()}

initial_balance = 10000
profit_loss = {}  

total_balance = initial_balance
analyzer = SentimentIntensityAnalyzer()
ticker = {}
seen_posts = set()

load_data()
runbot()
