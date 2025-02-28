import xml.etree.ElementTree as ET
from langsmith import traceable
from lxml import etree
import networkx as nx

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Heuristic scoring remains unchanged
# def heuristic_score(action_description, attributes):
#     """Assign a heuristic score to an action based on its attributes."""
#     important_buttons = ["login", "signup", "sign up", "sign-up", "submit", "btn"]
#     input_fields = ["input", "email", "password", "otp", "pass", "phone", "mobile", "name"]
#     score = 0
#     if attributes.get("is_external", False):
#         score -= 10
#     if attributes.get("is_ad", False):
#         score -= 15
#     # if len(action_description.strip()) <= 1:
#     #     score -= 50
#     if check_if_important(description=action_description, resource_id=attributes.get("resource_id"), patterns=important_buttons):
#         score += 20
#     elif check_if_important(description=action_description, resource_id=attributes.get("resource_id"), patterns=input_fields):
#         score += 30
#     elif "button" in attributes.get("tag", "").lower():
#         score += 10
#     elif "edittext" in attributes.get("tag", "").lower():
#         score += 15
#     elif "checkbox" in attributes.get("tag", "").lower():
#         score += 15
    
#     return score



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

def check_if_element_is_ad(node):
    return False

def check_if_element_is_external(node):
    return False

@traceable
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


    def extract_element(node):
        """Recursively extract elements from XML tree"""
        bounds = parse_bounds(node.get('bounds', '[0,0][0,0]'))
        
        description = node.get("text", "") + " " + node.get("content-desc", "")
        attributes = {
                "tag": node.tag,
                "bounds": bounds,
                "content_desc": node.get('content-desc'),
                "text": node.get('text'),
                "clickable": node.get('clickable') == 'true',
                "focused": node.get('focused') == 'true',
                "enabled": node.get('enabled') == 'true',
                "resource_id": node.get('resource-id'),
                "class": node.get('class'),
                # "xpath": get_xpath(node),
                "is_external": check_if_element_is_external(node),
                "is_ad": check_if_element_is_ad(node)
            }
        # Create a dictionary for the UI element
        ui_element_dict = {
            "description": description.strip(),
            "heuristic_score": calculate_heuristic_score(description.strip(), attributes),
            "attributes" : attributes
        }

        # Append the dictionary to the elements list
        elements.append(ui_element_dict)
        
        for child in node:
            extract_element(child)

    layout_tree = ET.fromstring(xml)
    extract_element(layout_tree)
    return elements


def calculate_heuristic_score(node_id, node_data):
        """Assign a heuristic score to an action based on its attributes."""
        
        score = 0
        if node_data.get("is_external", False):
            score -= 10
        if node_data.get("is_ad", False):
            score -= 15
        
        # score = apply_content_description_text_rules(score, node_id, node_data)
        score = apply_keyword_rules(score, node_id, node_data)
        score = apply_tag_rules(score, node_id, node_data)    
    
        return score

def apply_tag_rules(score, node_id, node_data):
    if "button" in node_data.get('attributes').get("tag", "").lower():
        score += 10
    elif "edittext" in node_data.get('attributes').get("tag", "").lower():
        score += 15
    elif "checkbox" in node_data.get('attributes').get("tag", "").lower():
        score += 30

    return score

def apply_content_description_text_rules(score, node_id, node_data):
    if len(node_data.get('description', '').strip()) <= 1:
        score -= 50
    return score

def apply_keyword_rules(score, node_id, node_data):
    important_buttons = ["login", "signup", "sign up", "sign-up", "submit", "btn", "register"]
    input_fields = ["input", "email", "password", "otp", "pass", "phone", "mobile", "name"]

    if check_if_important(description=node_data.get('description', '').strip(), resource_id=node_data.get('attributes').get("resource_id"), patterns=important_buttons):
        score += 20
    elif check_if_important(description=node_data.get('description', '').strip(), resource_id=node_data.get('attributes').get("resource_id"), patterns=input_fields):
        score += 30

    return score

def check_if_important(description, resource_id, patterns):
    # Ensure action_description and resource_id are not None or empty
    if not description:
        description = ""
    if not resource_id:
        resource_id = ""

    if description or resource_id:
        # Check if any pattern is in action_description or resource_id
        for pattern in patterns:
            if pattern in description.lower() or pattern in resource_id.lower():
                return True

    return False