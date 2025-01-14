import yfinance as yf
import pandas as pd
import datetime
import numpy as np
import requests
import json

def fetch_candlestick_data(tickers, start_date=None, end_date=None):
    """Fetch candlestick (OHLCV) data for a single ticker or list of tickers from yfinance.

    Args:
        tickers (str or list of str): Ticker symbols (e.g., 'AAPL' or ['AAPL', 'MSFT']).
        start_date (str, optional): Start date in 'YYYY-MM-DD' format. Defaults to two years ago.
        end_date (str, optional): End date in 'YYYY-MM-DD' format. Defaults to today.

    Returns:
        pd.DataFrame or dict: DataFrame or a dictionary of DataFrames for multiple tickers.
    """
    if start_date is None or end_date is None:
        end_date_dt = datetime.datetime.today()
        start_date_dt = end_date_dt - datetime.timedelta(days=365 * 2)

        start_date = start_date_dt.strftime('%Y-%m-%d')
        end_date = end_date_dt.strftime('%Y-%m-%d')

    return yf.download(tickers=tickers, start=start_date, end=end_date, progress=False)

def compute_daily_returns(close_series):
    """Compute daily percentage returns for a given close price series.

    Args:
        close_series (pd.Series): Series of close prices.

    Returns:
        pd.Series: Series of daily returns.
    """
    return close_series.pct_change().dropna()

def compute_volatility(daily_returns):
    """Compute the annualized volatility from daily returns.

    Args:
        daily_returns (pd.Series): Series of daily returns.

    Returns:
        float: Annualized volatility.
    """
    return daily_returns.std() * np.sqrt(252)

def compute_annualized_return(daily_returns):
    """Compute the annualized average return from daily returns.

    Args:
        daily_returns (pd.Series): Series of daily returns.

    Returns:
        float: Annualized average return.
    """
    return daily_returns.mean() * 252

def compute_risk(volatility_value):
    """Compute risk metric, often associated with volatility.

    Args:
        volatility_value (float): Volatility value.

    Returns:
        float: Risk metric.
    """
    return volatility_value

def get_risk_volatility_return(close_series):
    """Compute risk, volatility, and return for a given close price series.

    Args:
        close_series (pd.Series): Series of close prices.

    Returns:
        dict: Dictionary with keys ['risk', 'volatility', 'annualized_return'].
    """
    daily_returns = compute_daily_returns(close_series)
    vol = compute_volatility(daily_returns)
    ann_return = compute_annualized_return(daily_returns)
    risk = compute_risk(vol)

    return {
        'risk': risk,
        'volatility': vol,
        'annualized_return': ann_return
    }

def perform_calculations_for_tickers(tickers, start_date=None, end_date=None):
    """Perform calculations for tickers, including fetching data and computing metrics.

    Args:
        tickers (str or list of str): Ticker symbols.
        start_date (str, optional): Start date in 'YYYY-MM-DD' format. Defaults to two years ago.
        end_date (str, optional): End date in 'YYYY-MM-DD' format. Defaults to today.

    Returns:
        dict: Dictionary of results, keyed by ticker.
    """
    df = fetch_candlestick_data(tickers, start_date, end_date)

    results = {}

    if isinstance(tickers, str):
        close_series = df['Close'].dropna()
        calc = get_risk_volatility_return(close_series)
        results[tickers] = calc
    else:
        for ticker in tickers:
            close_series = df['Close', ticker].dropna()
            calc = get_risk_volatility_return(close_series)
            results[ticker] = calc

    return results

def send_raw_data_to_api(url, raw_data):
    """Send raw data (e.g., candlestick data) to another URL as JSON to an API.

    Args:
        url (str): API endpoint.
        raw_data (dict): JSON-serializable object containing raw data.

    Returns:
        requests.Response: Response object from the API call.
    """
    payload = json.dumps(raw_data, default=str)
    return perform_api_call(url=url, method="POST", data=payload)

def perform_api_call(url, method="GET", data=None, headers=None):
    """Perform a generic API call using the requests library.

    Args:
        url (str): API endpoint.
        method (str): HTTP method (GET, POST, PUT, DELETE, etc.). Defaults to 'GET'.
        data (str or dict, optional): Request body, JSON string, or dictionary. Defaults to None.
        headers (dict, optional): Additional headers for the request. Defaults to {'Content-Type': 'application/json'}.

    Returns:
        requests.Response: Response object from the API call.
    """
    if headers is None:
        headers = {"Content-Type": "application/json"}

    if method.upper() == "GET":
        response = requests.get(url, headers=headers, params=data)
    elif method.upper() == "POST":
        response = requests.post(url, headers=headers, data=data)
    elif method.upper() == "PUT":
        response = requests.put(url, headers=headers, data=data)
    elif method.upper() == "DELETE":
        response = requests.delete(url, headers=headers, data=data)
    else:
        raise ValueError(f"Unsupported method {method}")

    return response

def send_features_to_api(url, features_dict):
    """Send calculated features (risk, volatility, return, etc.) to another URL as JSON.

    Args:
        url (str): API endpoint.
        features_dict (dict): Dictionary containing the calculated features.

    Returns:
        requests.Response: Response object from the API call.
    """
    payload = json.dumps(features_dict)
    return perform_api_call(url=url, method="POST", data=payload)