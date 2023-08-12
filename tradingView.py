import json
import random
import re
import string

import requests
from websocket import create_connection


# Search for a symbol based on query and category
def search(query, category):
    url = f"https://symbol-search.tradingview.com/symbol_search/?text={query}&type={category}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        assert len(data) != 0, "Nothing Found."
        return data[0]
    else:
        print("Network Error!")
        exit(1)


# Generate a random session ID
def generate_session():
    string_length = 12
    letters = string.ascii_lowercase
    random_string = "".join(random.choice(letters) for _ in range(string_length))
    return "qs_" + random_string


# Prepend header to content
def prepend_header(content):
    return f"~m~{len(content)}~m~{content}"


# Construct a JSON message
def construct_message(func, param_list):
    return json.dumps({"m": func, "p": param_list}, separators=(",", ":"))


# Create a full message with header
def create_message(func, param_list):
    return prepend_header(construct_message(func, param_list))


# Send a message over the WebSocket connection
def send_message(ws, func, args):
    ws.send(create_message(func, args))


# Send a ping packet
def send_ping_packet(ws, result):
    ping_str = re.findall(".......(.*)", result)
    if ping_str:
        ping_str = ping_str[0]
        ws.send(f"~m~{len(ping_str)}~m~{ping_str}")


# Handle WebSocket messages
def socket_job(ws):
    while True:
        try:
            result = ws.recv()
            if "quote_completed" in result or "session_id" in result:
                continue
            res = re.findall("^.*?({.*)$", result)
            if res:
                json_res = json.loads(res[0])
                if json_res["m"] == "qsd":
                    prefix = json_res["p"][1]
                    symbol = prefix["n"]
                    price = prefix["v"].get("lp", None)
                    volume = prefix["v"].get("volume", None)
                    change = prefix["v"].get("ch", None)
                    change_percentage = prefix["v"].get("chp", None)
                    print(f"{symbol} -> {price=}, {change=}, {change_percentage=}, {volume=}")
            else:
                send_ping_packet(ws, result)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            exit(0)
        except Exception as e:
            print(f"ERROR: {e}\nTradingView message: {result}")
            continue


# Get symbol ID based on pair and market
def get_symbol_id(pair, market):
    data = search(pair, market)
    symbol_name = data["symbol"]
    broker = data.get("prefix", data["exchange"])
    symbol_id = f"{broker.upper()}:{symbol_name.upper()}"
    print(symbol_id, end="\n\n")
    return symbol_id


# Main function to establish WebSocket connection and start job
def main(pair, market):
    symbol_id = get_symbol_id(pair, market)

    trading_view_socket = "wss://data.tradingview.com/socket.io/websocket"
    headers = json.dumps({"Origin": "https://data.tradingview.com"})
    ws = create_connection(trading_view_socket, headers=headers)
    session = generate_session()

    send_message(ws, "quote_create_session", [session])
    send_message(
        ws,
        "quote_set_fields",
        [
            session,
            "lp",
            "low_price",
            "volume",
            "ch",
            "chp",
        ],
    )
    send_message(ws, "quote_add_symbols", [session, symbol_id])

    socket_job(ws)


if __name__ == "__main__":
    pair = "btcusdt"
    market = "crypto"
    main(pair, market)
