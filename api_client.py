import requests
import json


class ApiClient:
    """API Client for communicating with the Flask API"""

    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url

    def _make_request(self, endpoint, method="GET", data=None):
        """Make a request to the API"""
        url = f"{self.base_url}/{endpoint}"
        print(f"Making {method} request to {url}")

        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, data=json.dumps(data), headers=headers)
            elif method == "PUT":
                headers = {'Content-Type': 'application/json'}
                response = requests.put(url, data=json.dumps(data), headers=headers)
            elif method == "DELETE":
                response = requests.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Try to parse JSON response even if there's an HTTP error
            try:
                result = response.json()
            except json.JSONDecodeError:
                # If JSON parsing fails, return error dict
                result = {"success": False, "message": f"HTTP {response.status_code}: {response.text}"}

            # Debug log
            print(f"API Response for {endpoint}: {result}")

            # Check for HTTP errors after parsing JSON
            if response.status_code >= 400:
                # If result doesn't have success field, add it
                if not isinstance(result, dict) or 'success' not in result:
                    result = {"success": False, "message": result if isinstance(result, str) else f"HTTP {response.status_code} error"}
                print(f"API request error for {endpoint}: HTTP {response.status_code}")
                return result

            # Handle success/data structure
            if isinstance(result, dict):
                if 'success' in result:
                    if result['success']:
                        if 'data' in result:
                            print(f"Returning data from {endpoint}")
                            return result['data']
                        elif 'expenses' in result:
                            print(f"Returning expenses from {endpoint}")
                            return result['expenses']
                        elif 'user_id' in result:
                            print(f"Returning user_id from {endpoint}")
                            return result
                        else:
                            print(f"Returning full result from {endpoint}")
                            return result
                    else:
                        error_msg = result.get('message', 'Unknown error')
                        print(f"API request failed: {error_msg}")
                        return result
                print(f"Returning result without success field from {endpoint}")
                return result
            # Liste veya başka bir tip dönebilir (örn: birim_ucretler listesi döndürüyor)
            print(f"Returning list/other type result from {endpoint}")
            return result

        except requests.exceptions.RequestException as e:
            print(f"API request error for {endpoint}: {e}")
            return {"success": False, "message": f"Request failed: {str(e)}"}
        except json.JSONDecodeError as e:
            print(f"JSON decode error for {endpoint}: {e}")
            return {"success": False, "message": f"Invalid JSON response: {str(e)}"}
        except Exception as e:
            print(f"Unexpected error for {endpoint}: {e}")
            return {"success": False, "message": f"Unexpected error: {str(e)}"}

    def login(self, username, password):
        data = {'username': username, 'password': password}
        return self._make_request("login", method="POST", data=data)

    def register(self, username, password):
        data = {'username': username, 'password': password}
        return self._make_request("register", method="POST", data=data)

    def get_all_data(self):
        """Get all data from the API in one request"""
        return self._make_request("all_data")

    def get_bolge_kodlari(self):
        """Get bolge_kodlari from the API"""
        return self._make_request("bolge_kodlari")

    def get_kaynak_tipleri(self):
        """Get kaynak_tipleri from the API"""
        return self._make_request("kaynak_tipleri")

    def get_stages(self):
        """Get stages from the API"""
        return self._make_request("stages")

    def get_operasyonlar(self):
        """Get operasyonlar from the API"""
        return self._make_request("operasyonlar")

    def get_stage_operasyonlar(self):
        """Get stage_operasyonlar from the API"""
        return self._make_request("stage_operasyonlar")

    def get_birim_ucretler(self):
        return self._make_request("birim_ucretler")

    def add_bolge(self, kod, ad):
        """Add a new bolge to the database"""
        data = {"kod": kod, "ad": ad}
        return self._make_request("add_bolge", method="POST", data=data)

    def add_kaynak_tipi(self, kod, ad):
        data = {"kod": kod, "ad": ad}
        return self._make_request("add_kaynak_tipi", method="POST", data=data)

    def add_stage(self, kod, ad):
        data = {"kod": kod, "ad": ad}
        return self._make_request("add_stage", method="POST", data=data)

    def add_operasyon(self, stage_kod, op_kod, op_ad):
        data = {"stage_kod": stage_kod, "operasyon_kod": op_kod, "operasyon_ad": op_ad}
        return self._make_request("add_operasyon", method="POST", data=data)

    def add_stage_operasyon(self, kod, ad):
        data = {"kod": kod, "ad": ad}
        return self._make_request("add_stage_operasyon", method="POST", data=data)

    def add_birim(self, birim, ucret):
        data = {"birim": birim, "ucret": ucret}
        return self._make_request("add_birim", method="POST", data=data)

    def delete_bolge(self, kod):
        return self._make_request(f"delete_bolge/{kod}", method="DELETE")

    def update_bolge(self, eski_kod, yeni_kod, yeni_ad):
        data = {"eski_kod": eski_kod, "yeni_kod": yeni_kod, "ad": yeni_ad}
        return self._make_request("update_bolge", method="PUT", data=data)

    def delete_kaynak_tipi(self, kod):
        return self._make_request(f"delete_kaynak_tipi/{kod}", method="DELETE")

    def update_kaynak_tipi(self, kod, yeni_kod, ad):
        data = {"kod": kod, "yeni_kod": yeni_kod, "ad": ad}
        return self._make_request("update_kaynak_tipi", method="PUT", data=data)

    def delete_stage(self, kod):
        return self._make_request(f"delete_stage/{kod}", method="DELETE")

    def update_stage(self, kod, yeni_kod, ad):
        data = {"kod": kod, "yeni_kod": yeni_kod, "ad": ad}
        return self._make_request("update_stage", method="PUT", data=data)

    def delete_operasyon(self, stage_kod, op_kod):
        return self._make_request(f"delete_operasyon/{stage_kod}/{op_kod}", method="DELETE")

    def update_operasyon(self, stage_kod, op_kod, op_ad):
        data = {"stage_kod": stage_kod, "operasyon_kod": op_kod, "operasyon_ad": op_ad}
        return self._make_request("update_operasyon", method="PUT", data=data)

    def delete_stage_operasyon(self, kod):
        return self._make_request(f"delete_stage_operasyon/{kod}", method="DELETE")

    def update_stage_operasyon(self, kod, ad):
        data = {"kod": kod, "ad": ad}
        return self._make_request("update_stage_operasyon", method="PUT", data=data)

    def delete_birim(self, birim):
        return self._make_request(f"delete_birim/{birim}", method="DELETE")

    def update_birim(self, birim, ucret):
        data = {"birim": birim, "ucret": ucret}
        return self._make_request("update_birim", method="PUT", data=data)

    def save_expense(self, user_id, expense_data):
        """Save a new expense - düzeltilmiş versiyon"""
        # user_id'yi expense_data içine koy
        data = {
            'user_id': user_id,
            **expense_data
        }
        print(f"save_expense çağrıldı - user_id: {user_id}")
        print(f"expense_data: {expense_data}")
        print(f"Gönderilecek data: {data}")

        try:
            response = self._make_request("save_expense", method="POST", data=data)
            print(f"Save expense response: {response}")  # Debug log

            if response and isinstance(response, dict):
                return response
            else:
                print(f"Unexpected response format: {response}")
                return {"success": False, "message": "Beklenmeyen API yanıt formatı"}

        except Exception as e:
            print(f"Error in save_expense: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_expenses(self):
        """Get all expenses for a user"""
        response = self._make_request(f"get_expenses")
        print(f"API Client Response: {response}")  # Debug log
        return response

    def clear_expenses(self, user_id):
        """Clear all expenses for a user"""
        return self._make_request(f"clear_expenses/{user_id}", method="DELETE")

    def delete_expenses(self, expense_id):
        return self._make_request(f"delete_expense/{expense_id}", method="DELETE")

    def get_user_id(self, username):
        """Get user ID by username"""
        data = {'username': username}
        return self._make_request("get_user_id", method="POST", data=data)

    def get_operations_by_stage(self, stage_kod):
        """Get operations for a specific stage code"""
        return self._make_request(f"get_operations_by_stage/{stage_kod}")

    def bulk_add_bolge(self, bolge_listesi):
        """Toplu bölge kodu ekleme"""
        data = {"bolge_listesi": bolge_listesi}
        return self._make_request("bulk_add_bolge", method="POST", data=data)
