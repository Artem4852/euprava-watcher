import requests
import json
import threading
from bs4 import BeautifulSoup

# https://e-uprava.gov.si/si/javne-evidence/prosti-termini-zemljevid/content/singleton.html?lang=si&type=1&cat=6&izpitniCenter=18&lokacija=-1&offset=0&sentinel_type=ok&sentinel_status=ok&is_ajax=1&complete=false&page=4

def parse_page(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    # Implement parsing logic here
    # For example, extract available slots or relevant information
    available_slots = []
    # Example: Find all elements that contain available slots
    date = None
    for slot in soup.find_all('tr', class_='js_dicDetailsBtnRow'):
        new_date = slot.find('div', class_='sr-only')
        if new_date:
            date = new_date.text.strip()

        time = slot.find('td', attrs={'data-th': 'Ura'}).text.strip()

        place = slot.find('div', class_='dicTitle1').text.strip()
        slot = {
            "date": date,
            "time": time,
            "place": place
        }
        available_slots.append(slot)
    return available_slots

def filter_available(slots, filter_places=["LJUBLJANA", "DOMŽALE"], filter_dates=["10. 2026", "11. 2026"]):
    filtered_slots = [slot for slot in slots if (any(place in slot["place"].upper() for place in filter_places)) and (any(date in slot["date"] for date in filter_dates))]
    return filtered_slots

def fetch_page(page_n):
    r = requests.get(f"https://e-uprava.gov.si/si/javne-evidence/prosti-termini-zemljevid/content/singleton.html?lang=si&type=1&cat=6&izpitniCenter=18&lokacija=-1&offset=0&sentinel_type=ok&sentinel_status=ok&is_ajax=1&complete=false&page={page_n}")

    if r.status_code != 200:
        print(f"Error fetching page {page_n}: {r.status_code}")
        return []

    page_available = parse_page(r.text)
    return page_available

def fetch_available():
    available = []

    threads = []

    for page in range(0, 14):
        thread = threading.Thread(target=lambda p=page: available.extend(fetch_page(p)))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # for page in range(0, 14):
        # r = requests.get(f"https://e-uprava.gov.si/si/javne-evidence/prosti-termini-zemljevid/content/singleton.html?lang=si&type=1&cat=6&izpitniCenter=18&lokacija=-1&offset=0&sentinel_type=ok&sentinel_status=ok&is_ajax=1&complete=false&page={page}")

        # if r.status_code != 200:
        #     print(f"Error fetching page {page}: {r.status_code}")
        #     continue

        # # with open(f"page_{page}.html", "w", encoding="utf-8") as f:
        # #     f.write(r.text)

        # page_available = parse_page(r.text)

        # available.extend()

    return available

if __name__ == "__main__":
    data = fetch_available()
    data = filter_available(data)

    with open("available_slots.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)