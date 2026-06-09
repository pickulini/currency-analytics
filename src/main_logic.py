import os
from datetime import datetime, timedelta
from .auth import AuthManager
from .api_client import APIClient
from .report_builder import ReportBuilder

class AppController:
    def __init__(self):
        self.auth = AuthManager()
        self.api = APIClient()
        self.report_builder = ReportBuilder()
        self.current_user = None

    def login(self, username, password):
        success, role = self.auth.authenticate(username, password)
        if success:
            self.current_user = self.auth.get_current_user()
        return success, role

    def logout(self):
        self.auth.logout()
        self.current_user = None

    def get_current_user_info(self):
        return self.current_user

    def register(self, username, password):
        return self.auth.register(username, password)

    def fetch_currency_data(self, period_days, base_currency="USD", symbols=None):
        if not self.current_user:
            return None
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        data = self.api.fetch_historical_rates(start_date, end_date, base_currency, symbols)
        if data:
            df = self.report_builder.build_dataframe(data)
            return df
        return None

    def save_report(self, df, file_format="excel", filename=None):
        if not self.current_user or df is None:
            return None
        folder = self.current_user["reports_folder"]
        os.makedirs(folder, exist_ok=True)
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}"
        if file_format == "excel":
            full_path = os.path.join(folder, f"{filename}.xlsx")
            self.report_builder.save_to_excel(df, full_path)
        else:
            full_path = os.path.join(folder, f"{filename}.csv")
            self.report_builder.save_to_csv(df, full_path)
        return full_path

    def list_user_reports(self):
        if not self.current_user:
            return []
        folder = self.current_user["reports_folder"]
        if not os.path.exists(folder):
            return []
        files = [f for f in os.listdir(folder) if f.endswith(('.xlsx', '.csv'))]
        return files

    def delete_report(self, username, filename):
        if not self.current_user:
            return False, "Не авторизован"
        if username == self.current_user['username'] or self.current_user['role'] == 'admin':
            folder = f"data/reports/{username}"
            full_path = os.path.join(folder, filename)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True, "Удалено"
            else:
                return False, "Файл не найден"
        else:
            return False, "Нет прав"

    def get_reports_for_user(self, username):
        if self.current_user is None or self.current_user['role'] != 'admin':
            return []
        folder = f"data/reports/{username}"
        if not os.path.exists(folder):
            return []
        return [f for f in os.listdir(folder) if f.endswith(('.xlsx', '.csv'))]

    def get_all_users(self):
        if self.current_user is None or self.current_user['role'] != 'admin':
            return []
        users = self.auth.list_users()
        return [u['username'] for u in users]
