import requests
from bs4 import BeautifulSoup

class Goons:

    def __init__(self):
        pass

    def find_goons(self):
        url = "https://docs.google.com/spreadsheets/u/0/d/e/2PACX-1vR-wIQI351UH85ILq5KiCLMMrl0uHRmjDinBCt6nXGg5exeuCxQUf8DTLJkwn7Ckr8-HmLyEIoapBE5/pubhtml/sheet?headers=false&gid=1420050773"
        session = requests.Session()
        response = session.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Assuming the data is in a table, find the second row
            table = soup.find('table')
            rows = table.find_all('tr')
            print(rows)
            if len(rows) > 1:
                second_row = rows[2]
                cells = second_row.find_all('td')
                timestamp_value = cells[0].text
                map_value = cells[1].text
                formatted_data = {"map": map_value, "timestamp": timestamp_value}
                return formatted_data
            else:
                return "Data not found"
        else:
            return "Error fetching data"
        
goons = Goons()
print(goons.find_goons())