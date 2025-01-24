action_prioritization_template = """
    Following screen context describes the mobile app screen in short:
    {screen_context}
    Note: Ignore the screen context if nothing is given. Please create an understanding of the screen yourself.

    These are available actionable elements:
    {actions}

    This is the history of actions done previously:
    {history}
    Note: Ignore the history if nothing is given. Complete the objective based on the actionable elements provided alone.

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
    This journey can be successfull only when the priority ranking of elements to act on reflects the order - enter username, enter password and click login button. 
    This would not be an meaningful journey in any other order.

    Output format:
    Please generate the output in JSON format with following keys - 
    ranked_actions - this should be a list of dictionaries based on the list of actionable elements provided above. 
        In the output, each dictionary in the list of "ranked_actions" should be the same as the actionable element with one additional field added "llm_rank"
        "llm_rank" should reflect the priority given to that element to act on in ascending order.
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