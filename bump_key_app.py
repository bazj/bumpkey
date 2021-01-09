import time

import cloudscraper
import requests
from bs4 import BeautifulSoup

import hibp_keys


class BumpKeyApp:

    def __init__(self, hibp_api_key=None, scraper=None):
        self.headers = {'content-type': 'application/json', 'api-version': '3',
                        'User-Agent': 'BumpKey script for checking and removing data from searchable databases',
                        'hibp-api-key': hibp_api_key or hibp_keys.hibp_api_key}
        # HIBP API requires a paid for key, read more here:  https://haveibeenpwned.com/API/Key
        self.scraper = scraper or cloudscraper.create_scraper()
        self.removal_links = []

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
            raise PermissionError('The API key is not authorised to query HIBP API. Please check the provided API Key')
        else:
            data = response.json()
            raise Exception(f'Error: {response.status_code}  {data.get("message", "")}')
        return parsed_data

    def request_page_and_filter(self, sub_page):
        # Dehashed uses Cloudflare anti bot protection which can prevent results being scraped
        # In order to access results we will use a third party API instead of requests that solves the cloudflare
        # Javascript challenge https://github.com/Anorov/cloudflare-scrape
        print(f'Querying : {sub_page}')
        # response = requests.get(f'https://www.dehashed.com/{sub_page}')
        response = self.scraper.get(f'https://www.dehashed.com/{sub_page}')
        print(f'Response code:{response.status_code}')
        print(f'Response text:{response.text}')
        if response.status_code == 200:
            print(f'Loading soup')
            soup = BeautifulSoup(response.text, 'html.parser')
            removal_data = soup.find_all(class_="request-removal")
            removal_links = [f'https://www.dehashed.com{link.get("href")}' for link in removal_data]
            if removal_links:
                print(f'Found links: {removal_links}')
            # This gives us the first page of results only.
            # Check for further pages.
            page_selector = soup.find(class_="next pull-right")
            if page_selector:
                # If further pages exist this will give us the link so we can scrape it.
                next_set_of_results = page_selector.find("a").get('href', None)
                print(f'Found additional page of results: {next_set_of_results}')
                print(f'Sleep before requesting to avoid triggering ddos protection: {next_set_of_results}')
                time.sleep(5)
                self.request_page_and_filter(next_set_of_results)

    def query_dehashed_for_email(self, email_address):
        formatted_email_address = email_address.replace('@', '%40')
        self.removal_links = []  # reset the class variable in case of a previous run
        self.request_page_and_filter(f'search?query={formatted_email_address}')

    def compile_data_for_email(self, email_address):
        # We first use HIBP API as an indicator as to whether or not the email is likely to have been breached
        # HIBP provide a public API for this and I consider them a trustworthy source
        response = self.request_pwnage_data_for_email(email_address)
        processed_data = self.process_pwnage_data_for_email(response)
        if processed_data:
            self.query_dehashed_for_email_data(email_address)

    def request_removal_of_details(self, removal_links):
        # Once we have the removal URLs, query each one to trigger dehashed.com to send the user a removal confirmation
        if removal_links:
            for found_url in removal_links:
                self.scraper.get(found_url)
                time.sleep(5)  # Sleep to avoid triggering ddos protection


if __name__ == '__main__':
    app = BumpKeyApp()
    app.compile_data_for_email('test@example.com')
    app.request_removal_of_details(app.removal_links)
