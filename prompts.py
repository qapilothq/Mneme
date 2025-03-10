action_prioritization_template = """
    Following screen context describes the mobile app screen in short:
    {screen_context}
    Note: Ignore the screen context if nothing is given. Please create an understanding of the screen yourself based on the image given below or the list of actions given below.

    These are available actionable elements:
    {actions}

    This is the history of actions done previously:
    {history}
    Note: Ignore the history if nothing is given. Complete the objective based on the actionable elements provided alone.

    This is the user prompt provided by the user to help us understand what the possible user journey is:
    {user_prompt}
    Note: Ignore the user prompt if nothing is given. Please create an understanding of the user journey yourself.
    
    Objective:
    You are navigating a mobile app. On a given screen there would be a number of elements which are actionable.
    You are intended to help in the exploration of the app by providing a priority order to the actionable elements on the screen.
    This priority order should help make the navigation optimised to explore the meaningful user journeys.
    Following are a few guidelines to follow while creating the priority list
    1. Actions that take the exploration out of the app should not done. 
    2. Elements that are ads should not be acted upon
    3. Actions that may lead to loops should be low priority. 
    4. Actions that lead to meaningful user journeys based on what actions have been done till now should be given higher priority.
    5. If there are multiple actions to be done on a single screen in the same user journey, then priority order should reflect the order in which the actions are to be performed.
    As an example to the 4th guideline, on a login screen, entering username, entering password and clicking login are all part of the same user journey.
    This journey can be successfull only when the priority ranking of elements to act on reflects the order - enter username, enter password, check any checkboxes before clicking login button. 
    This would not be an meaningful journey in any other order.
    6. Use the annotated image which has actionable elements also to create an understanding of the elements and the order in which they have to be interacted with.
    6. Use 'heuristic_score' mentioned for each action as one of the guides to give priority. Higher the heuristic score, higher the priority.
    7. Also, there are boolean fields called 'focused' and 'enabled' inside attributes of each action. Use these values to decide the priority order. Prioritize the enabled and focussed elements over others.
    Also you can use the image, if available, to identify which elements are focused and enabled, and are important for the flow of the journey.

    Output format:
    Please generate the output in JSON format with following keys - 
    ranked_actions - this should be a list of dictionaries based on the list of actionable elements provided above. 
        In the output, each dictionary in the list of "ranked_actions" should be the same as the actionable element with one additional field added "llm_rank"
        "llm_rank" should reflect the priority given to that element to act on in ascending order.
    explanation - This should include your understanding of the screen in short based on the elements given. And then the reasoning for the priority order generated.

    Generate the output in JSON only, without any additional text.
"""

action_prioritization_template_with_annotated_image = """
    Following screen context describes the mobile app screen in short:
    {screen_context}
    Note: Ignore the screen context if nothing is given. Please create an understanding of the screen yourself based on the image given below or the list of actions given below.

    This is the history of actions done previously:
    {history}
    Note: Ignore the history if nothing is given. Complete the objective based on the actionable elements provided alone.

    This is the user prompt provided by the user to help us understand what the possible user journey is:
    {user_prompt}
    Note: Ignore the user prompt if nothing is given. Please create an understanding of the user journey yourself.
    
    These are available actionable elements:
    {actions}

    Objective:
    You are navigating a mobile app. On a given screen there would be a number of elements which are actionable.
    You are intended to help in the exploration of the app by providing a priority order to the actionable elements on the screen.
    This priority order should help make the navigation optimised to explore the meaningful user journeys.
    Following are a few guidelines to follow while creating the priority list
    1. Actions that take the exploration out of the app should not done. For example, in a login flow "Forgot Password" would take you away from the login flow, so it should be of lower priority.
    2. Elements that are ads should not be acted upon
    3. Actions that may lead to loops should be low priority. 
    4. Actions that lead to meaningful user journeys based on what actions have been done till now should be given higher priority.
    5. If there are multiple actions to be done on a single screen in the same user journey, then priority order should reflect the order in which the actions are to be performed.
    6. Use the annotated image which has actionable elements also to create an understanding of the elements and the order in which they have to be interacted with.
    7. If there is a checkbox kind element to act on before an actionable element, then it should prioritized over the actions below them on the screen. Use the image if needed here. 
    For example, checking the privacy policy or terms and conditions could ne necessary before clicking on the login button, so checking the checkbox should be higher priority than the login button click.
    8. Use 'heuristic_score' mentioned for each action as a secondary guide to give priority.
    9. Also you can use the image, if available, to identify which elements are focused and enabled, and are important for the flow of the journey.

    Output format:
    Please generate the output in JSON format with following keys - 
    ranked_actions - This should be a list of node_ids in the order of most prioritized to least prioritized
    explanation - This should include your understanding of the screen in short based on the elements given. And then the reasoning for the priority order generated.

    Generate the output in JSON only, without any additional text.
"""

screen_context_generation_template = """
    You are navigating a mobile app. 
    You are an experienced tester who can summarize the screen functionalities in a short and succint way.
    Given the page source of the screen:
    {xml}

    Generate a short description of the of the screen which can be used as context for a tester 
    to understand what actions are possible and what to test in a given screen.
    Keep the description to less than 20 words.
    """