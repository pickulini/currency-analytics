import requests
from datetime import datetime, timedelta

class APIClient:
    BASE_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1"

    def __init__(self):
        self.session = requests.Session()
        self._available_currencies = None

    def _get_currencies_list(self):
        """Загружает список всех валют (кэширует)."""
        if self._available_currencies is None:
            try:
                # Ссылка на список валют (без сжатия)
                url = f"{self.BASE_URL}/currencies.min.json"
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                # data: {"usd": "United States Dollar", ...}
                self._available_currencies = sorted([k.upper() for k in data.keys()])
            except Exception as e:
                print(f"Failed to fetch currency list: {e}")
                # Запасной список
                self._available_currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CHF", "CNY", "CAD", "AUD", "NZD", "INR", "BRL", "ZAR"]
        return self._available_currencies

    def fetch_historical_rates(self, start_date, end_date, base_currency="USD", symbols=None):
        """
        Получает курсы для каждой даты в диапазоне [start_date, end_date].
        Возвращает словарь, совместимый с ReportBuilder.
        """
        # Приводим даты к строкам, если пришли объекты datetime
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")

        # Генерируем список дат между start_date и end_date включительно
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        date_list = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end - start).days + 1)]

        rates = {}
        base_lower = base_currency.lower()
        symbols_lower = [s.lower() for s in symbols] if symbols else None

        for date_str in date_list:
            # Формируем URL для конкретной даты
            # Примечание: API не поддерживает параметр date в GET, поэтому мы обращаемся к основному файлу,
            # который всегда содержит курсы на последний день. Но мы можем получить исторические данные,
            # если используем другой эндпоинт: https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/{base}.json
            # Поэтому заменим @latest на конкретную дату.
            # Используем формат: https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/{base}.min.json
            # date в формате ГГГГ-ММ-ДД
            url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date_str}/v1/currencies/{base_lower}.min.json"
            try:
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                # В ответе: { "date": "...", "usd": { "rub": 90.1, ... } }
                if base_lower in data:
                    currency_data = data[base_lower]
                    # Фильтруем только запрошенные валюты, если они есть
                    if symbols_lower:
                        filtered = {s.upper(): currency_data.get(s, None) for s in symbols_lower if s in currency_data}
                    else:
                        filtered = {k.upper(): v for k, v in currency_data.items()}
                    rates[date_str] = filtered
                else:
                    rates[date_str] = {}
            except Exception as e:
                print(f"Failed to fetch {date_str}: {e}")
                rates[date_str] = {}

        return {
            "success": True,
            "base": base_currency,
            "start_date": start_date,
            "end_date": end_date,
            "rates": rates
        }

    def get_available_symbols(self):
        return self._get_currencies_list()