import requests
from datetime import datetime, timedelta

class APIClient:
    def __init__(self):
        self.session = requests.Session()

    def fetch_historical_rates(self, start_date, end_date, base_currency="USD", symbols=None):
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")
        
        # Преобразуем даты в список
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        date_list = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end - start).days + 1)]
        
        rates_by_date = {}
        for date_str in date_list:
            # API: https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@2026-06-09/v1/currencies/usd.json
            url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date_str}/v1/currencies/{base_currency.lower()}.json"
            try:
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    currency_data = data.get(base_currency.lower(), {})
                    # Выбираем только нужные валюты
                    if symbols:
                        filtered = {sym.lower(): currency_data.get(sym.lower()) for sym in symbols}
                    else:
                        filtered = currency_data
                    rates_by_date[date_str] = {k.upper(): v for k, v in filtered.items() if v is not None}
                else:
                    print(f"No data for {date_str}")
            except Exception as e:
                print(f"Error fetching {date_str}: {e}")
        
        if rates_by_date:
            return {"rates": rates_by_date, "base": base_currency}
        return None
