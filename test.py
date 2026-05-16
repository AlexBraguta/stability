from binance.um_futures import UMFutures
import config


client = UMFutures(config.API_KEY, config.API_SECRET)

info = client.exchange_info()

# print(info['symbols'])

t_list = {item['symbol'] for item in info['symbols'] }

print(t_list)