# tradingView-API
tradingview real time socket api get prices from tradingview.

## How to run

```
git clone https://github.com/mohamadkhalaj/tradingView-API.git
cd tradingView-API
pip3 install -r requirements.txt
python3 tradingView.py
```

# How to use

First you should select category type and searching text (by search() function in the code):
```
category list: 'stock' | 'futures' | 'forex' | 'cfd' | 'crypto' | 'index' | 'economic'
```
# Example
```python
data = search('btcusdt', 'crypto')
```

if any results found it will be shown.


