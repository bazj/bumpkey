import requests
import hibp_keys
from bs4 import BeautifulSoup


class BumpKeyApp:

    def __init__(self, hibp_api_key=None):
        self.headers = {'content-type': 'application/json', 'api-version': '3',
                        'User-Agent': 'BumpKey script for checking and removing data from searchable databases',
                        'hibp-api-key': hibp_api_key or hibp_keys.hibp_api_key}
        # HIBP API requires a paid for key, read more here:  https://haveibeenpwned.com/API/Key

    def request_pwnage_data_for_email(self, email):
        response = requests.get(
                    f'https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false',
                    headers=self.headers)
        return response

    def process_pwnage_data_for_email(self, response):
        parsed_data = []
        if response.status_code == 200:
            data = response.json()
            for record in data:
                breach_name = record['Name']
                breach_domain = record['Domain']
                breach_date = record['BreachDate']
                logo_path = record['LogoPath']
                print(f'Found breach: {breach_name}\nDomain: {breach_domain}\nDate: {breach_date}\n')
                parsed_data.append([breach_name, breach_domain, breach_date, logo_path])
        elif response.status_code == 401:
            print('The API key  is not authorised to query HIBP API. Please check the provided API Key')
        else:
            data = response.json()
            print(f'Error: {response.status_code}  {data.get("message", "")}')
        return parsed_data

    def query_dehashed_for_email(self, email_address):
        formatted_email_address = email_address.replace('@', '%40')
        response = requests.get(f'https://www.dehashed.com/search?query={formatted_email_address}')
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            removal_data = soup.find_all(class_="request-removal")
            removal_links = [f'https://www.dehashed.com{link.get("href")}' for link in removal_data]
            #This gives us the first page of results only.
            #Further results are available at https://dehashed.com/search?query=basimjafar%40gmail.com&page=2
            #TODO need to figure out how to find the 'end page for an email address set of results.



    def compile_data_for_email(self, email_address):
        #We first use HIBP API as an indicator as to whether or not the email is likely to have been breached
        #HIBP provide a public API for this and I consider them a trustworthy source
        response = self.request_pwnage_data_for_email(email_address)
        processed_data = self.process_pwnage_data_for_email(response)
        if processed_data:
            dehashed_data = self.query_dehashed_for_email_data(email_address)

        return processed_data

if __name__ == '__main__':
    app = BumpKeyApp()
    app.compile_data_for_email('test@example.com')
