from langsmith import traceable
import requests
import os
import traceback
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@traceable
def check_for_popup(request_id, xml, xml_url, image=None, image_url=None, test_case_description="Close the pop up"):

    try:
        logging.info(f"requestid :: {request_id} :: Checking for Pop Up")
        payload = {
            "xml_url": xml_url,
            "xml": xml,
            "image_url": image_url,
            "image": image,
            "testcase_dec": test_case_description
        }
        # API request to popup-handler
        logging.info(f"requestid :: {request_id} :: Calling for Pop Up Handler Agent - {os.getenv('POPUP_HANDLER_URL')}")
        api_response = make_api_request(request_id=request_id, request_url=os.getenv("POPUP_HANDLER_URL"), payload=payload)

        if api_response and api_response.get("status", "").lower() == 'success':
            agent_response = api_response.get("agent_response", {})
            popup_detected = agent_response.get("popup_detection")
            if isinstance(popup_detected, bool) and popup_detected:
                logging.info(f"requestid :: {request_id} :: Pop Up detected - {api_response}")
                primary_method = agent_response.get("primary_method, {}")
                if primary_method and "element_metadata" in primary_method:
                    element_metadata = agent_response.get("element_metadata", {})
                    logging.info(f"requestid :: {request_id} :: Pop Up primary method found - {element_metadata}")
                    return True, element_metadata
                else:
                    logging.info(f"requestid :: {request_id} :: Pop Up primary method/element metadata not found; returning false")
                    return False, {}
            else:
                logging.info(f"requestid :: {request_id} :: Pop Up not detected - {api_response}")
                return False, {}
        else:
            logging.info(f"requestid :: {request_id} :: Pop Up Detection failed; API response - {str(api_response)}")
            return False, {}
    except Exception as e:
        logging.error(f"requestid :: {request_id} :: Pop Up detection failed with an exception - {str(e)} -- {traceback.format_exc()}")
        return False, {}

@traceable
async def generate_test_data(request_id, xml, xml_url, image=None, image_url=None, config_data={}):

    try:
        logging.info(f"requestid :: {request_id} :: Generating test data")
        payload = {
            "xml": xml,
            "xml_url": xml_url,
            "image": image,
            "image_url": image_url,
            "config": config_data
        }
        # API request to datagenerator
        logging.info(f"requestid :: {request_id} :: Calling for Test Data Generator Agent - {os.getenv('TEST_DATA_GENERATOR_URL')}")
        api_response = make_api_request(request_id=request_id, request_url=os.getenv("TEST_DATA_GENERATOR_URL"), payload=payload)

        if api_response and api_response.get("status", "").lower() == 'success':
            agent_response = api_response.get("agent_response", {})
            datagen_required = agent_response.get("data_generation_required")
            logging.info(f"requestid :: {request_id} :: Test Data generation response received; API response - {api_response}")
            if isinstance(datagen_required, bool) and agent_response.get("data_generation_required"):
                fields = agent_response.get("fields", {})
                return True, fields
            else:
                return False, []
        else:
            logging.info(f"requestid :: {request_id} :: Test Data generation failed; API response - {str(api_response)}")
            return False, []
    except Exception as e:
        logging.error(f"requestid :: {request_id} :: Test Data generation failed with an exception - {str(e)} -- {traceback.format_exc()}")
        return False, []

@traceable
def make_api_request(request_id, request_url, payload):
    try:
        response = requests.post(request_url, json=payload)
        response.raise_for_status()  # Raises an error for bad responses
        return response.json()  # Returns the response as a JSON object
    except requests.exceptions.RequestException as e:
        logging.error(f"requestid :: {request_id} :: Exception while making API request to - {request_url} -- Stacktrace - {traceback.format_exc()}")
        return None