from typing import Any
from langchain.prompts import PromptTemplate
from fastapi import HTTPException
from dotenv import load_dotenv
from prompts import action_prioritization_template, screen_context_generation_template
from llm import initialize_llm
import xml.etree.ElementTree as ET
import json
import os
import requests
import base64
 
load_dotenv()

# Use LangChain for reasoning-based prioritization
def llm_prioritize_actions(screen_context, base64_image, actions, history, user_prompt, llm):
    """
    Use an LLM to prioritize actions based on screen context and history.
    Args:
    - screen_context: Textual representation of the current screen.
    - actions: List of available actions with descriptions.
    - history: Log of previously performed actions.
    - llm: LangChain LLM object.

    Returns:
    - List of actions ranked by priority with explanations.
    """
    # Create a chain with the LLM and prompt template
    prompt_template = PromptTemplate(input_variables=["screen_context", "base64_image", "actions", "history", "user_prompt"], template=action_prioritization_template)
    # Fill the prompt template
    filled_prompt = prompt_template.format(
        screen_context=screen_context,
        base64_image=base64_image,
        actions=actions,
        history=history,
        user_prompt=user_prompt
    )

    # Invoke the LLM
    response = llm.invoke(filled_prompt)
    return response

def llm_generate_screen_context(xml, llm):
    """
    Use an LLM to generate screen context based on the xml.
    Args:
    - xml: pagesource of the screen
    - llm: LangChain LLM object.

    Returns:
    - Short description of the text in natural language
    """
    # Create a chain with the LLM and prompt template
    prompt_template = PromptTemplate(input_variables=["xml"], template=screen_context_generation_template)
    # Fill the prompt template
    filled_prompt = prompt_template.format(
        xml=xml
    )

    # Invoke the LLM
    response = llm.invoke(filled_prompt)
    return response

# Heuristic scoring remains unchanged
def heuristic_score(action_description, attributes):
    """Assign a heuristic score to an action based on its attributes."""
    important_buttons = ["login", "signup", "sign up", "sign-up", "submit"]
    input_fields = ["input", "email", "password", "otp", "pass", "phone", "mobile", "name"]
    score = 0
    if attributes.get("is_external", False):
        score -= 10
    if attributes.get("is_ad", False):
        score -= 15
    if len(action_description.strip()) <= 1:
        score -= 50
    if check_if_important(action_description=action_description, resource_id=attributes.get("resource_id"), patterns=important_buttons):
        score += 20
    elif check_if_important(action_description=action_description, resource_id=attributes.get("resource_id"), patterns=input_fields):
        score += 30
    elif "button" in attributes.get("element_type", "").lower():
        score += 10
    elif "edittext" in attributes.get("element_type", "").lower():
        score += 15
    
    return score

def check_if_important(action_description, resource_id, patterns):
    # Ensure action_description and resource_id are not None or empty
    if not action_description:
        action_description = ""
    if not resource_id:
        resource_id = ""

    if action_description or resource_id:
        # Check if any pattern is in action_description or resource_id
        for pattern in patterns:
            if pattern in action_description.lower() or pattern in resource_id.lower():
                return True

    return False

# Prioritize actions with LangChain LLM
def prioritize_actions(screen_context, image, actions, history, user_prompt, llm):
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

    # LLM reasoning
    llm_response = llm_prioritize_actions(
        screen_context,
        image,
        [action for action in actions if action['heuristic_score'] > 0 or action.get("attributes").get("clickable")],
        history,
        user_prompt,
        llm
    )

    # print(f"LLM response: {llm_response}")
    content = llm_response.content.replace('```json\n', '').replace('\n```', '').replace('\n', '')
    # Parse the JSON response
    response_dict = json.loads(content)
    ranked_actions = response_dict.get("ranked_actions", [])
    explanation = response_dict.get("explanation", "")
    # Parse LLM response for ranking (mock parsing for this example)
    # for i, action in enumerate(actions):
    #     action['llm_score'] = len(actions) - i  # Simulated LLM ranking
    #     action['explanation'] = llm_response

    # Combine scores
    # for action in actions:
    #     action['final_score'] = action['heuristic_score'] + action['llm_score']

    # Rank actions
    ranked_actions = sorted(ranked_actions, key=lambda x: x['llm_rank'], reverse=False)
    return ranked_actions, explanation

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

def parse_bounds(bounds_str: str):
    """Parse bounds string '[left,top][right,bottom]' into tuple"""
    try:
        coords = bounds_str.strip('[]').split('][')
        left, top = map(int, coords[0].split(','))
        right, bottom = map(int, coords[1].split(','))
        return (left, top, right, bottom)
    except Exception as e:
        print(f"Failed to parse bounds '{bounds_str}': {str(e)}")
        return (0, 0, 0, 0)

def parse_layout(xml):
    """
    Parse XML layout into UIElement objects
    Returns:
    - A list of dictionaries representing UI elements
    """
    elements = []
    
    def get_xpath(node):
        """
        Generate the XPath for a given XML node.
        
        Args:
        - node: An lxml etree Element object.

        Returns:
        - A string representing the XPath of the node.
        """
        path = []
        while node is not None:
            parent = node.getparent()
            if parent is not None:
                siblings = parent.findall(node.tag)
                if len(siblings) > 1:
                    index = siblings.index(node) + 1
                    path.append(f"{node.tag}[{index}]")
                else:
                    path.append(node.tag)
            else:
                path.append(node.tag)
            node = parent
        return '/' + '/'.join(reversed(path))

    def check_if_element_is_ad(node):
        return False

    def check_if_element_is_external(node):
        return False

    def extract_element(node):
        """Recursively extract elements from XML tree"""
        bounds = parse_bounds(node.get('bounds', '[0,0][0,0]'))
        
        description = node.get("text", "") + " " + node.get("content-desc", "")
        attributes = {
                "element_type": node.tag,
                "bounds": bounds,
                "content_desc": node.get('content-desc'),
                "text": node.get('text'),
                "clickable": node.get('clickable') == 'true',
                "focused": node.get('focused') == 'true',
                "enabled": node.get('enabled') == 'true',
                "resource_id": node.get('resource-id'),
                "class_name": node.get('class'),
                # "xpath": get_xpath(node),
                "is_external": check_if_element_is_external(node),
                "is_ad": check_if_element_is_ad(node)
            }
        # Create a dictionary for the UI element
        ui_element_dict = {
            "description": description.strip(),
            "heuristic_score": heuristic_score(description.strip(), attributes),
            "attributes" : attributes
        }

        # Append the dictionary to the elements list
        elements.append(ui_element_dict)
        
        for child in node:
            extract_element(child)

    layout_tree = ET.fromstring(xml)
    extract_element(layout_tree)
    return elements

def transform_popup_to_ranked_action(pop_up_element):
    # Transforming the popup element output to action format
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
    
    return transformed_action

def map_data_fields_to_ranked_actions(ranked_actions, data_fields):
    try:
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
        print("exception in mapping data fields to prioritized actions")
    finally:
        return ranked_actions

def get_element_identifier(element_dict) -> str:

    if element_dict:
        resource_id = element_dict.get('resource_id')
        resource_id = resource_id.strip() if resource_id is not None else ""

        text = element_dict.get("text")
        text = text.strip() if text is not None else ""

        content_desc = element_dict.get("content_desc")
        content_desc = content_desc.strip() if content_desc is not None else ""

        return (resource_id + text + content_desc).strip()
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

