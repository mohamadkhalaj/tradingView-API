import json
import random
import re
import string

import requests
from websocket import create_connection


def search(query, category):
    # category = 'stock' | 'futures' | 'forex' | 'cfd' | 'crypto' | 'index' | 'economic'
    # query = what you want to search!
    # it returns first matching item
    res = requests.get(
        f"https://symbol-search.tradingview.com/symbol_search/?text={query}&type={category}"
    )
    if res.status_code == 200:
        res = res.json()
        assert len(res) != 0, "Nothing Found."
        return res[0]
    else:
        print("Network Error!")
        exit(1)


def generate_session():
    string_length = 12
    letters = string.ascii_lowercase
    random_string = "".join(random.choice(letters) for _ in range(string_length))
    return "qs_" + random_string


def prepend_header(content):
    return f"~m~{len(content)}~m~{content}"


def construct_message(func, param_list):
    return json.dumps({"m": func, "p": param_list}, separators=(",", ":"))


def create_message(func, param_list):
    return prepend_header(construct_message(func, param_list))


def send_message(ws, func, args):
    ws.send(create_message(func, args))


def send_ping_packet(ws, result):
    ping_str = re.findall(".......(.*)", result)
    if ping_str:
        ping_str = ping_str[0]
        ws.send(f"~m~{len(ping_str)}~m~{ping_str}")


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
                    print(
                        f"{symbol} -> {price=}, {change=}, {change_percentage=}, {volume=}"
                    )
            else:
                # ping packet
                send_ping_packet(ws, result)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            exit(0)
        except Exception as e:
            print(f"ERROR: {e}\nTradingView message: {result}")
            continue


def get_symbol_id(pair, market):
    data = search(pair, market)
    symbol_name = data["symbol"]
    broker = data.get("prefix", data["exchange"])
    symbol_id = f"{broker.upper()}:{symbol_name.upper()}"
    print(symbol_id, end="\n\n")
    return symbol_id


def main(pair, market):
    # search btcusdt from crypto category
    symbol_id = get_symbol_id(pair, market)

    # create tunnel
    trading_view_socket = "wss://data.tradingview.com/socket.io/websocket"
    headers = json.dumps({"Origin": "https://data.tradingview.com"})
    ws = create_connection(trading_view_socket, headers=headers)
    session = generate_session()

    # Send messages
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
    # Start job
    socket_job(ws)


if __name__ == "__main__":
    pair = "btcusdt"
    market = "crypto"
    main(pair, market)
