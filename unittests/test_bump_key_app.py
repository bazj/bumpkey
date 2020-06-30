from unittest import TestCase
from unittest.mock import patch, Mock, MagicMock, PropertyMock
import bump_key_app
import requests


class TestBumpKeyApp(TestCase):

    def mocked_request(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

        if args[0] == 'https://haveibeenpwned.com/api/v3/breachedaccount/imaginary@email.co?truncateResponse=false':
            return MockResponse({"some": "data"}, 200)
        elif args[0] == 'https://haveibeenpwned.com/api/v3/breachedaccount/some@email.co?truncateResponse=false':
            raise requests.Timeout('Test error')
        return MockResponse(None, 404)

    @patch('requests.get', side_effect=mocked_request)
    def test_request_pwnage_data_for_email(self, mocked_request):
        """
        Verify that when a simulated call is made to the HIBP API, the expected data is returned.
        """
        dummy_email = "imaginary@email.co"
        test_target = bump_key_app.BumpKeyApp()
        test_result = test_target.request_pwnage_data_for_email(dummy_email)
        self.assertEqual(test_result.status_code, 200)
        self.assertEqual(test_result.json_data, {"some": "data"})

    @patch('requests.get', side_effect=mocked_request)
    def test_request_pwnage_data_for_email_with_exception(self, mocked_request):
        """
        Verify that when a simulated exception is thrown in this method it is raised upwards.
        """
        dummy_email = "some@email.co"
        test_target = bump_key_app.BumpKeyApp()
        with self.assertRaises(requests.Timeout):
            test_target.request_pwnage_data_for_email(dummy_email)


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

    def test_process_pwnage_data_for_email(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = [{'Name': 'Breach1', 'Domain': 'D1', 'BreachDate': '1', 'LogoPath': '/x/y/z',
                                       'Other': '1'},
                                      {'Name': 'Breach2', 'Domain': 'D2', 'BreachDate': '2', 'LogoPath': '/x/y/x',
                                       'Other': '2'},
                                      {'Name': 'Breach3', 'Domain': 'D3', 'BreachDate': '3', 'LogoPath': '/x/y/y',
                                       'Other': '3'}
                                      ]
        test_target = test_target = bump_key_app.BumpKeyApp()
        test_result = test_target.process_pwnage_data_for_email(response)
        self.assertTrue(type(test_result) == list)
        self.assertTrue(len(test_result) == 3)
        self.assertEqual(test_result, [['Breach1', 'D1', '1', '/x/y/z'],
                                        ['Breach2', 'D2', '2', '/x/y/x'],
                                        ['Breach3', 'D3', '3', '/x/y/y']])

    def test_query_dehashed_for_email(self):
        self.fail('Not implemented')

    def test_compile_data_for_email(self):
        self.fail('Not implemented')