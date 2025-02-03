import requests
import os



def check_for_popup(xml_url, image_url=None, test_case_description=""):

    payload = {
        "xml": xml_url,
        "image": image_url,
        "testcase_dec": test_case_description
    }
    # API request to popup-handler
    api_response = make_api_request(os.getenv("POPUP_HANDLER_URL"), payload)

    if api_response and api_response.get("status", "").lower() == 'success':
        agent_response = api_response.get("agent_response", {})
        if agent_response.get("popup_detection", "").lower() == "yes":
            print("pop up detected")
            element_metadata = agent_response.get("element_metadata", {})
            return True, element_metadata
        else:
            print("pop up not detected")
            return False, {}
    else:
        print("pop up detection failed")
        return False, {}


def generate_test_data(xml_url, image_url=None, config_data={}):

    payload = {
        "xml": xml_url,
        "image": image_url,
        "config": config_data
    }
    # API request to popup-handler
    api_response = make_api_request(os.getenv("TEST_DATA_GENERATOR_URL"), payload)

    if api_response and api_response.get("status", "").lower() == 'success':
        agent_response = api_response.get("agent_response", {})
        if agent_response.get("data_generation_required", "").lower() == "yes":
            print("data generation required")
            fields = agent_response.get("fields", {})
            return True, fields
        else:
            print("data generation not required")
            return False, {}
    else:
        print("data generation failed")
        return False, {}


def make_api_request(request_url, payload):
    try:
        response = requests.post(request_url, json=payload)
        response.raise_for_status()  # Raises an error for bad responses
        return response.json()  # Returns the response as a JSON object
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None