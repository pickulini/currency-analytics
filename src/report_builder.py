import pandas as pd
import os

class ReportBuilder:
    @staticmethod
    def build_dataframe(api_data):
        if not api_data or "rates" not in api_data:
            return None
        rates = api_data["rates"]
        df = pd.DataFrame.from_dict(rates, orient="index")
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        return df

    @staticmethod
    def save_to_excel(df, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_excel(filepath, sheet_name="Курсы валют")
        return filepath

    @staticmethod
    def save_to_csv(df, filepath):
        df.to_csv(filepath, encoding="utf-8-sig")
        return filepath
