from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from prompts import action_prioritization_template, screen_context_generation_template
from llm import initialize_llm
import xml.etree.ElementTree as ET
import json
import os
 
load_dotenv()

# Use LangChain for reasoning-based prioritization
def llm_prioritize_actions(screen_context, actions, history, llm):
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
    prompt_template = PromptTemplate(input_variables=["screen_context", "actions", "history"], template=action_prioritization_template)
    # Fill the prompt template
    filled_prompt = prompt_template.format(
        screen_context=screen_context,
        actions=actions,
        history=history
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
    score = 0
    if attributes.get("is_external", False):
        score -= 10
    if attributes.get("is_ad", False):
        score -= 15
    if len(action_description.strip()) <= 1:
        score -= 50
    elif "login" in action_description.lower() or "submit" in action_description.lower():
        score += 20
    elif "button" in attributes.get("element_type", "").lower():
        score += 10
    
    return score

# Prioritize actions with LangChain LLM
def prioritize_actions(screen_context, actions, history, llm):
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
        [action for action in actions if action['heuristic_score'] > 0],
        history,
        llm
    )

    print(f"LLM response: {llm_response}")
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

def parse_layout(xml):
        """
        Parse XML layout into UIElement objects
        Returns:
        - A list of dictionaries representing UI elements
        """
        elements = []
        
        def parse_bounds(bounds_str: str):
            """Parse bounds string '[left,top][right,bottom]' into tuple"""
            try:
                coords = bounds_str.strip('[]').split('][')
                left, top = map(int, coords[0].split(','))
                right, bottom = map(int, coords[1].split(','))
                return (left, top, right, bottom)
            except Exception as e:
                self.logger.error(f"Failed to parse bounds '{bounds_str}': {str(e)}")
                return (0, 0, 0, 0)

        def check_if_element_is_ad(node: ET.Element) -> bool:
            return False

        def check_if_element_is_external(node: ET.Element) -> bool:
            return False

        def extract_element(node: ET.Element) -> None:
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

# Example usage
if __name__ == "__main__":
    # Initialize the LLM (can be switched to Anthropic, etc.)
    llm_key = os.getenv("OPENAI_API_KEY")
    if not llm_key:
        raise HTTPException(status_code=500, detail="API key not found. Please check your environment variables.")
    llm = initialize_llm(llm_key)

    # Screen context (mock example)
    screen_context = "Login screen with options to sign in, register, or skip."

    # List of actions with metadata
    actions = [
        {"description": "Click 'Sign In'", "attributes": {"element_type": "button", "is_ad": False, "is_external": False}},
        {"description": "Click 'Register'", "attributes": {"element_type": "button", "is_ad": False, "is_external": False}},
        {"description": "Click 'Skip'", "attributes": {"element_type": "button", "is_ad": False, "is_external": False}},
        {"description": "Click 'Sponsored Ad'", "attributes": {"element_type": "image", "is_ad": True, "is_external": True}}
    ]

    # Action history (mock example)
    history = ["Visited Home Screen", "Clicked 'Get Started'"]

    # Prioritize actions
    ranked_actions = prioritize_actions(screen_context, actions, history, llm)

    # Output ranked actions
    for action in ranked_actions:
        print(f"Action: {action['description']}")
        print(f"  Final Score: {action['final_score']}")
        print(f"  Explanation: {action['explanation']}")
        print()
