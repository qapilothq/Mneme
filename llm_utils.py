from langsmith import traceable
from langchain.prompts import PromptTemplate
from prompts import action_prioritization_template, screen_context_generation_template, action_prioritization_template_with_annotated_image

import traceback
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@traceable
# Use LangChain for reasoning-based prioritization
def llm_prioritize_actions(request_id, screen_context, base64_image, actions, history, user_prompt, llm):
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
    prompt_template = PromptTemplate(input_variables=["screen_context", "actions", "history", "user_prompt"], template=action_prioritization_template)
    # Fill the prompt template
    filled_prompt = prompt_template.format(
        screen_context=screen_context,
        actions=actions,
        history=history,
        user_prompt=user_prompt
    )
    messages = [("system", filled_prompt)]
    if base64_image:
        messages.append(("human", [
                        {"type": "text", "text": "Here is the screenshot of the mobile app screen with actionable elements annotated on the image with node_id. Please create an understanding of the screen to give a prioritization to the elements to act on and the order to act on."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]))

    try:
        # Invoke the LLM
        response = llm.invoke(input=messages)
        logging.info(f"requestid :: {request_id} :: LLM invokation succesfull")
        return response
    except Exception as e:
        logging.error(f"requestid :: {request_id} :: LLM invokation failed; couldn't prioritize - {str(e)} -- {traceback.format_exc()}")
        return None
    
@traceable
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
