import copy
import traceback
import json
import os
import requests
import base64
from datetime import datetime
import uuid
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from fastapi import HTTPException
from langsmith import traceable
from llm_utils import llm_prioritize_actions
from xml_utils import parse_bounds

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@traceable
# Prioritize actions with LangChain LLM
async def prioritize_actions(request_id, uitree, screen_context, image, actions, history, user_prompt, phase, llm):
    """
    Prioritize actions using both heuristic and LLM reasoning.
    Args:
    - screen_context: Textual representation of the current screen.
    - actions: List of available actions (each is a dictionary with metadata).
    - history: Log of previous actions.
    - llm: LangChain LLM object.

    Returns:
    - Ranked list of actions with scores and explanations.
    """
    # Heuristic scoring
    # for action in actions:
    #     action['heuristic_score'] = heuristic_score(action['description'], action['attributes'])
    
    logging.info(f"requestid :: {request_id} :: Calling LLM to prioritize UI elments")
    # LLM reasoning
    elements_to_prioritize = filter_elements(request_id=request_id, uitree=uitree, ui_elements=actions)
    logging.info(f"requestid :: {request_id} :: Number of clickable elements to prioritize - {len(elements_to_prioritize)}")
    if image:
        logging.info(f"requestid :: {request_id} :: Marking UI elments on the image")
        annotated_image = annotate_image(image, elements_to_prioritize)
    else:
        annotated_image = None
    prioritization_start_time = datetime.now()
    llm_response = llm_prioritize_actions(
        request_id=request_id,
        screen_context=screen_context,
        base64_image=annotated_image,
        actions=trim_element_jsons(request_id=request_id, elements_to_trim=elements_to_prioritize),
        history=history,
        user_prompt=user_prompt,
        phase=phase,
        llm=llm
    )
    logging.info(f"requestid :: {request_id} :: Time taken by LLM to prioritize elements :: {(datetime.now() - prioritization_start_time).total_seconds() * 1000} milliseconds")
    
    if llm_response:
        # print(f"LLM response: {llm_response}")
        content = llm_response.content.replace('```json\n', '').replace('\n```', '').replace('\n', '')
        # Parse the JSON response
        response_dict = json.loads(content)
        ranked_node_ids = response_dict.get("ranked_actions", [])
        explanation = response_dict.get("explanation", "")

        # Rank actions
        # ranked_actions = sorted(ranked_actions, key=lambda x: x['llm_rank'], reverse=False)
        ranked_actions = []
        rank = 1
        for node_id in ranked_node_ids:
            ui_element = uitree.ui_element_dict_processed.get(node_id)
            if ui_element:
                ranked_actions.append({
                    "node_id": node_id,
                    "llm_rank": rank,
                    "description": ui_element.get("description"),
                    "heuristic_score": ui_element.get("heuristic_score"),
                    "attributes": ui_element.get("attributes")
                })
                rank += 1
        logging.info(f"requestid :: {request_id} :: LLM prioritized; returning order based on llm rank. Number of ranked actions: {len(ranked_actions)}")
        return ranked_actions, explanation
    else:
        # logging.error(f"requestid :: {request_id} :: LLM failed to prioritize; returning order based on heuristic score")
        # ranked_clickable_elements = sorted(elements_to_prioritize, key=lambda x: x['heuristic_score'], reverse=True)
        logging.error(f"requestid :: {request_id} :: LLM failed to prioritize; returning order based on cooridnates of the top-left of the element")
        ranked_clickable_elements = sort_elements_top_to_bottom(elements_to_prioritize)
        for i in range(0, len(ranked_clickable_elements)):
            ranked_clickable_elements[i]["llm_rank"] = i + 1
        
        return ranked_clickable_elements, "LLM failed to prioritize; returning order based on heuristic score"

def filter_elements(request_id, uitree, ui_elements):

    fields_to_check = ["clickable", "enabled", "displayed"]
    try:
        selected_elements = []
        for element in ui_elements:
            attributes = element.get("attributes")
            
            if all(field in attributes and 'true' == attributes.get(field)  for field in fields_to_check):
                node_id = element.get('node_id', None)
                if node_id is not None:
                    is_leaf_element = check_if_leaf_element(request_id, uitree, node_id)
                    if is_leaf_element:
                        selected_elements.append(element)

        return selected_elements
    except Exception as e:
        return [element for element in ui_elements if element.get('heuristic_score') > 0 or all(field in element.get("attributes") and 'true' == element.get("attributes").get(field)  for field in fields_to_check)]

def trim_element_jsons(request_id, elements_to_trim):
    # attributes_to_trim = ["index", "package", "class", "checkable", "checked", "clickable", "enabled", "focusable", "focused", "long-clickable", "password", "resource_id", "scrollable", "selected", "bounds", "displayed", "xpath"]
    # fields_to_trim = ["is_external", "is_ad", "heuristic_score", "attributes"]
    try:
        trimmed_elements = []
        for element in elements_to_trim:
            attributes = element.get("attributes")
            trimmed_elements.append({
                "node_id": element.get("node_id"),
                "description": element.get("description"),
                "element_type": attributes.get("class"),
                "bounds": attributes.get("bounds")
            })

        return trimmed_elements
            
    except Exception as e:
        logging.error(f"requestid :: {request_id} :: Exception in trimming tokens in filtered elements before prioritization; returning as is.")
        return elements_to_trim

def check_if_leaf_element(request_id, uitree, node_id):
    children = list(uitree.graph.successors(node_id))
    if children is None or len(children) == 0:
        return True
    return True

def sort_elements_top_to_bottom(ui_elements):
    """
    Sort UI elements based on their top (y) and left (x) coordinates.

    Args:
    - ui_elements: List of UI elements, each with a 'bounds' attribute.

    Returns:
    - A sorted list of UI elements.
    """
    def extract_coordinates(bounds):
        # Parse bounds string like "[0,0][100,100]"
        coords = bounds.replace("][", ",").strip("[]").split(",")
        if len(coords) == 4:
            x1, y1, x2, y2 = map(int, coords)
            return y1, x1
        return float('inf'), float('inf')  # Default to large values if parsing fails

    # Sort elements based on y1 (top) and x1 (left) coordinates
    sorted_elements = sorted(ui_elements, key=lambda element: extract_coordinates(element['attributes'].get('bounds', '')))

    return sorted_elements

def annotate_image(base64_image, ui_elements):
    """
    Annotate the image with bounding boxes and element IDs for all interactable elements.
    
    Args:
        base64_image (str): Base64 encoded image string
        xml_data (dict): Processed XML data containing interactable elements
        
    Returns:
        str: Base64 encoded annotated image
    """

    if not base64_image:
        return None

    # Decode base64 image
    image_data = base64.b64decode(base64_image)
    image = Image.open(BytesIO(image_data))

    if image.mode == 'RGBA':
        image = image.convert('RGB')
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, use default if not available
    try:
        font = ImageFont.truetype("Arial.ttf", 50)
    except IOError:
        font = ImageFont.load_default()
    

    # Draw bounding boxes and element IDs for all interactable elements
    for element in ui_elements:
        attributes = element.get("attributes", {})
        bounds = attributes.get("bounds")
        element_id = element.get("node_id")

        if isinstance(bounds, str):
            # Parse bounds string like "[0,0][100,100]"
            coords = bounds.replace("][", ",").strip("[]").split(",")
            if len(coords) == 4:
                x1, y1, x2, y2 = map(int, coords)
                # Draw rectangle
                draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=3)  # Increased outline width
                # Draw element ID
                draw.text((x1-30, y1-30), str(element_id), fill="red", font=font)  # Position text at top-left corner


    
    # plt.figure(figsize=(8, 8))
    # plt.imshow(image)
    # plt.axis('off')  # Hide the axis
    # plt.show()
    # Convert back to base64
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    annotated_base64 = base64.b64encode(buffered.getvalue()).decode()

    # Ensure the directory exists
    os.makedirs("screenshot_combined_debug", exist_ok=True)

    # Generate a unique filename using a timestamp and UUID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex
    filename = f"screenshot_combined_debug/annotated_image_{timestamp}_{unique_id}.jpg"

    # Save the annotated image
    try:
        image.save(filename)
        print(f"Annotated image saved as {filename}")
    except Exception as e:
        print(f"Error saving annotated image: {e}")

    return annotated_base64

def encode_image(input_source):
    """
    Encodes an image from a file path, file object, or URL into a base64 string.

    Args:
    input_source (str or file-like object): The image file path, file object, or URL.

    Returns:
    str: Base64 encoded string of the image.
    """
    try:
        if isinstance(input_source, str):
            # Check if it's a URL
            if input_source.startswith('http://') or input_source.startswith('https://'):
                response = requests.get(input_source)
                response.raise_for_status()
                image_data = response.content
            # Check if it's a file path
            elif os.path.isfile(input_source):
                with open(input_source, 'rb') as image_file:
                    image_data = image_file.read()
            else:
                raise ValueError("Invalid file path or URL.")
        else:
            # Assume it's a file-like object
            image_data = input_source.read()

        # Encode the image data
        encoded_image = base64.b64encode(image_data).decode()
        return encoded_image

    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

def transform_popup_to_ranked_action(request_id, pop_up_element):
    # Transforming the popup element output to action format
    try:
        bounds = parse_bounds(pop_up_element.get('bounds', '[0,0][0,0]'))
        
        description = pop_up_element.get("text", "") + " " + pop_up_element.get("content-desc", "")
        attributes = {
                "element_type": pop_up_element.get('element_type'),
                "bounds": bounds,
                "content_desc": pop_up_element.get('element_details'),
                "text": pop_up_element.get('text'),
                "clickable": pop_up_element.get('clickable', 'False').lower() == 'true',
                "focused": pop_up_element.get('focused', 'False').lower() == 'true',
                "enabled": pop_up_element.get('enabled', 'False').lower() == 'true',
                "resource_id": pop_up_element.get('resource_id'),
                "class_name": pop_up_element.get('class_name'),
                "xpath": pop_up_element.get('xpath'),
                "is_external": False,
                "is_ad": False
            }
        # Create a dictionary for the UI element
        transformed_action = {
            "description": description.strip(),
            "heuristic_score": 0,
            "attributes" : attributes,
            "llm_rank": 1
        }
        logging.info(f"requestid :: {request_id} :: Pop Up detected; Returning - {transformed_action}")
        return transformed_action
    except Exception as e:
        logging.error(f"requestid :: {request_id} :: Exception in formatting the popup element found into prioritized action - {pop_up_element}")
        logging.error(f"requestid :: {request_id} :: Exception in formatting the popup element found into prioritized action - Stacktrace - {traceback.format_exc()}")
        return {"description": "", "heuristic_score": 0, "attributes" : {}, "llm_rank": 1}

@traceable
def map_data_fields_to_ranked_actions(request_id, ranked_actions, data_fields):
    try:
        logging.info("requestid :: {request_id} :: Mapping generated data fields to prioritized actions")
        for action in ranked_actions:
            action_identifier = get_element_identifier(action.get("attributes", {}))
            if action_identifier:
                # Check for data only if action element has an identifier
                for data_field in data_fields:
                    if "metadata" in data_field:
                        data_field_identifier = get_element_identifier(data_field.get("metadata", {}))
                        if data_field_identifier:
                            # Check for a match only if data field has an identifier
                            if action_identifier == data_field_identifier:
                                # Add generated data info to the action
                                action["generated_data"] = data_field
                                # Remove the matched data_field from the list
                                data_fields.remove(data_field)
                                break # Assuming one-to-one mapping, break after finding a match 
        
    except Exception as e:
        logging.error("requestid :: {request_id} :: Exception in mapping data fields to prioritized actions; returning ranked actions without generated data")
    finally:
        return ranked_actions

def get_element_identifier(element_dict) -> str:

    if element_dict:
        # resource_id = element_dict.get('resource_id')
        # resource_id = resource_id.strip() if resource_id is not None else ""

        # text = element_dict.get("text")
        # text = text.strip() if text is not None else ""

        # content_desc = element_dict.get("content_desc")
        # content_desc = content_desc.strip() if content_desc is not None else ""

        # return (resource_id + text + content_desc).strip()
        return element_dict.get('bounds', None)
    else:
        return ""

def get_file_content(file_path_or_url: str, is_image: bool = False) -> str:
    if file_path_or_url.startswith(('http://', 'https://')):
        # It's a URL
        try:
            response = requests.get(file_path_or_url)
            response.raise_for_status()
            content = response.content
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Error fetching file from URL: {e}")
    else:
        # It's a local file path
        if not os.path.exists(file_path_or_url):
            raise HTTPException(status_code=400, detail=f"File not found: {file_path_or_url}")
        try:
            with open(file_path_or_url, 'rb') as file:
                content = file.read()
        except IOError as e:
            raise HTTPException(status_code=400, detail=f"Error reading file: {e}")

    if is_image:
        # Return base64-encoded string for images
        return base64.b64encode(content).decode('utf-8')
    else:
        # Return string for XML content
        return content.decode('utf-8')
