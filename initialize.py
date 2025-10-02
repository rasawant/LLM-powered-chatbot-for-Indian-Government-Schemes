import requests
import json
import os  

SLUG_URL="https://api.myscheme.gov.in/search/v5/schemes?lang=en&q=%5B%22education%22%5D&keyword=&sort=&from=0&size=100"
def getSlug():
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate,",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Origin": "https://www.myscheme.gov.in",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-CH-UA": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        "Sec-CH-UA-Mobile": "?1",
        "Sec-CH-UA-Platform": '"Android"',
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        "x-api-key": "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
    }

    response = requests.get(SLUG_URL, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            slug=[]
            for item in data['data']['hits']['items']:
                slug.append(item['fields']['slug'])
            
        except requests.exceptions.JSONDecodeError as e:
            print("JSON decode error:", e)
            print("Raw response:", response.text[:500])
    else:
        print(f"Error: {response.status_code} – {response.reason}")
        print("Raw response:", response.text[:500])
    return slug

def getSchemeDetails(slugs):
    # Creating the newdata.json and Writing the entire data to Newdata.json after fetching it from API with the help of slug
    with open("schemeData.json", "w", encoding="utf-8") as f:
        f.write('[')
    for s in slugs:
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "origin": "https://www.myscheme.gov.in",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
            "x-api-key": "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
        }

        response = requests.get("https://api.myscheme.gov.in/schemes/v5/public/schemes?slug="+s+"&lang=en",headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
                with open("schemeData.json", "a", encoding="utf-8") as f:
                    json.dump(data['data']['en'], f, ensure_ascii=False, indent=4)
                    f.write(',')
                
                print("✅ JSON data saved to 'schemeData.json'")
            except requests.exceptions.JSONDecodeError as e:
                print("JSON decode error:", e)
                print("Raw response:", response.text[:500])
        else:
            print(f"Error: {response.status_code} – {response.reason}")
            print("Raw response:", response.text[:500])
    with open("schemeData.json", "r+b") as f:
        f.seek(-1, os.SEEK_END)
        f.truncate()
    with open("schemeData.json", "a", encoding="utf-8") as f:
        f.write(']')



if __name__ == "__main__":
    slugs = getSlug()
    # print(slugs)
    getSchemeDetails(slugs)