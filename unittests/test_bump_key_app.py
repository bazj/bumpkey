from unittest import TestCase
from unittest.mock import patch, Mock, call

import requests

import bump_key_app


class TestBumpKeyApp(TestCase):

    def setUp(self):
        self.mocked_return_data = [{'Name': 'Breach1', 'Domain': 'D1', 'BreachDate': '1', 'LogoPath': '/x/y/z',
                                    'Other': '1'},
                                   {'Name': 'Breach2', 'Domain': 'D2', 'BreachDate': '2', 'LogoPath': '/x/y/x',
                                    'Other': '2'},
                                   {'Name': 'Breach3', 'Domain': 'D3', 'BreachDate': '3', 'LogoPath': '/x/y/y',
                                    'Other': '3'}
                                   ]

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

    def test_process_pwnage_data_for_email_positive_case(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = self.mocked_return_data
        test_target = bump_key_app.BumpKeyApp()
        test_result = test_target.process_pwnage_data_for_email(response)
        self.assertTrue(type(test_result) == list)
        self.assertTrue(len(test_result) == 3)
        self.assertEqual(test_result, [['Breach1', 'D1', '1', '/x/y/z'],
                                       ['Breach2', 'D2', '2', '/x/y/x'],
                                       ['Breach3', 'D3', '3', '/x/y/y']])

    def test_process_pwnage_data_for_email_negative_case_auth(self):
        response = Mock()
        response.status_code = 401
        response.json.return_value = self.mocked_return_data
        test_target = bump_key_app.BumpKeyApp()
        with self.assertRaises(PermissionError):
            test_target.process_pwnage_data_for_email(response)

    def test_process_pwnage_data_for_email_negative_case_other(self):
        response = Mock()
        response.status_code = 666
        response.json.return_value = 'ERROR'
        test_target = bump_key_app.BumpKeyApp()
        with self.assertRaises(Exception):
            test_target.process_pwnage_data_for_email(response)

    def test_query_dehashed_for_email(self):

        def patch_request_page_and_filter(query):
            if query != 'search?query=test%40domain.random':
                raise Exception(f'patch_request_page_and_filter called with unexpected value {query}')

        test_email_address = "test@domain.random"
        test_target = bump_key_app.BumpKeyApp()
        test_target.removal_links = ['SomePreExistingValue']  # Set variable to some value to verify it is reset on test
        test_target.request_page_and_filter = patch_request_page_and_filter
        self.assertTrue(test_target.removal_links)
        test_target.query_dehashed_for_email(test_email_address)
        self.assertFalse(test_target.removal_links)

    def test_compile_data_for_email(self):

        def patch_request_pwnage_data_for_email(email_add):
            if email_add == 'test@random.domain':
                return Mock()
            else:
                raise Exception(f'Unexpected email address passed {email_add}')

        def patch_process_pwnage_data_for_email(resp):
            resp.passed()

        test_target = bump_key_app.BumpKeyApp()
        test_target.request_pwnage_data_for_email = patch_request_pwnage_data_for_email
        test_target.process_pwnage_data_for_email = patch_process_pwnage_data_for_email
        test_email_address = "test@random.domain"
        test_target.compile_data_for_email(test_email_address)

    def request_page_and_filter(self):
        self.fail('Not implemented')

    def test_request_removal_of_details(self):
        mocked_scraper = Mock()
        test_removal_links = ['test1', 'test2', 'test3']
        test_target = bump_key_app.BumpKeyApp()
        test_target.scraper = mocked_scraper
        test_target.request_removal_of_details(test_removal_links)
        expected_call_list = [call.get(x) for x in test_removal_links]
        mocked_scraper.assert_has_calls(expected_call_list, any_order=True)
        self.assertEqual(mocked_scraper.get.call_count, len(test_removal_links))
