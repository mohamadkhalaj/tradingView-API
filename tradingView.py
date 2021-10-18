import json, random, string, re, requests
from websocket import create_connection

tradingViewSocket = 'wss://data.tradingview.com/socket.io/websocket'

def search(query, type):
	# type = 'stock' | 'futures' | 'forex' | 'cfd' | 'crypto' | 'index' | 'economic'
	# query = what you want to search!
	# it returns first matching item
	res = requests.get(f'https://symbol-search.tradingview.com/symbol_search/?text={query}&type={type}')
	if res.status_code == 200:
		res = res.json()
		if len(res) == 0:
			print('Nothing Found!')
			return False	
		else:
			return res[0]
	else:
		print('Network Error!')

def generateSession():
	stringLength = 12
	letters = string.ascii_lowercase
	random_string =  ''.join(random.choice(letters) for i in range(stringLength))
	return "qs_" +random_string

def prependHeader(st):
	return "~m~" + str(len(st)) + "~m~" + st

def constructMessage(func, paramList):
	return json.dumps({
		"m":func,
		"p":paramList
		}, separators=(',', ':'))

def createMessage(func, paramList):
	return prependHeader(constructMessage(func, paramList))

def sendMessage(ws, func, args):
	ws.send(createMessage(func, args))

headers = json.dumps({
	'Origin': 'https://data.tradingview.com'
})

def main():

	# serach btcusdt from crypto category
	data = search('btcusdt', 'crypto')
	if not data:
		exit()
	symbol_name = data['symbol']
	broker = data['exchange']
	symbol_id = f'{broker.upper()}:{symbol_name.upper()}'
		
	print(symbol_id, end='\n\n')
	
	# create tunnel
	ws = create_connection(tradingViewSocket, headers = headers)
	session = generateSession()

	sendMessage(ws, "quote_create_session", [session])
	sendMessage(ws,"quote_set_fields", [session, 'lp'])
	sendMessage(ws, "quote_add_symbols",[session, symbol_id])

	while True:
		try:
			result = ws.recv()
			if 'quote_completed' in result or 'session_id' in result:
				continue
			Res = re.findall("^.*?({.*)$", result)
			if len(Res) != 0:
				jsonRes = json.loads(Res[0])

				if jsonRes['m'] == 'qsd':
					symbol = jsonRes['p'][1]['n']
					price = jsonRes['p'][1]['v']['lp']
					print(f'{symbol} -> {price}')
			else:
				# ping packet
				pingStr = re.findall(".......(.*)", result)
				if len(pingStr) != 0:
					pingStr = pingStr[0]
					ws.send("~m~" + str(len(pingStr)) + "~m~" + pingStr)
		except Exception as e:
			continue

if __name__ == '__main__':
	main()
