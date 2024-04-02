import requests


class Goons:

    def find_goons():
        try:
            response = requests.get(
                "https://docs.google.com/spreadsheets/u/0/d/e/2PACX-1vR-wIQI351UH85ILq5KiCLMMrl0uHRmjDinBCt6nXGg5exeuCxQUf8DTLJkwn7Ckr8-HmLyEIoapBE5/pubhtml/sheet?headers=false&gid=1420050773"
            )

            if response.status_code == 200:
                data = response.json()

                if len(data) > 1:
                    second_row = data[1]
                    timestamp_value = second_row[1]
                    map_value = second_row[2]

                    formatted_data = {"map": map_value, "timestamp": timestamp_value}

                    return formatted_data
                else:
                    return "Data not found"
            else:
                return "Error fetching data"
        except requests.exceptions.RequestException as e:
            return "Error fetching data"

    formatted_data = find_goons()
