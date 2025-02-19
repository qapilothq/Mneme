import requests
import os


def check_for_popup(xml, xml_url, image=None, image_url=None, test_case_description="Close the pop up"):

    payload = {
        "xml_url": xml_url,
        "xml": xml,
        "image_url": image_url,
        "image": image,
        "testcase_dec": test_case_description
    }
    # API request to popup-handler
    api_response = make_api_request(os.getenv("POPUP_HANDLER_URL"), payload)

    if api_response and api_response.get("status", "").lower() == 'success':
        agent_response = api_response.get("agent_response", {})
        popup_detected = agent_response.get("popup_detection")
        if isinstance(popup_detected, bool) and popup_detected:
            print("pop up detected")
            primary_method = agent_response.get("primary_method, {}")
            if primary_method and "element_metadata" in primary_method:
                element_metadata = agent_response.get("element_metadata", {})
                return True, element_metadata
            else:
                return False, {}
        else:
            print("pop up not detected")
            return False, {}
    else:
        print("pop up detection failed")
        return False, {}


def generate_test_data(xml, xml_url, image=None, image_url=None, config_data={}):

    try:
        payload = {
            "xml": xml,
            "xml_url": xml_url,
            "image": image,
            "image_url": image_url,
            "config": config_data
        }
        # API request to popup-handler
        api_response = make_api_request(os.getenv("TEST_DATA_GENERATOR_URL"), payload)

        if api_response and api_response.get("status", "").lower() == 'success':
            agent_response = api_response.get("agent_response", {})
            datagen_required = agent_response.get("data_generation_required")
            if isinstance(datagen_required, bool) and datagen_required:
                print("data generation required")
                fields = agent_response.get("fields", {})
                return True, fields
            else:
                print("data generation not required")
                return False, {}
        else:
            print("data generation failed")
            return False, {}
    except Exception as e:
        print("data generation failed with an exception")
        return False, {}


def make_api_request(request_url, payload):
    try:
        response = requests.post(request_url, json=payload)
        response.raise_for_status()  # Raises an error for bad responses
        return response.json()  # Returns the response as a JSON object
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None