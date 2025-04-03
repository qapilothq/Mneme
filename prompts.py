action_prioritization_template_v1 = """
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
    {objective}

    General Guidelines:
    Following are a few general guidelines to follow while creating the priority list
    1. Actions that take the exploration out of the app should not done. 
    2. Elements that are ads should not be acted upon
    3. Actions that may lead to loops should be low priority. 
    4. If there are multiple actions to be done on a single screen in the same user journey, then priority order should reflect the order in which the actions are to be performed.
    As an example to this guideline, on a login screen, entering username, entering password and clicking login are all part of the same user journey.
    This journey can be successfull only when the priority ranking of elements to act on reflects the order - enter username, enter password, check any checkboxes before clicking login button. 
    This would not be an meaningful journey in any other order.
    5. Use the annotated image which has actionable elements also to create an understanding of the elements and the order in which they have to be interacted with.
    6. All actions given to you are clickable, enabled and displayed(not hidden) on the screen.
    7. Also you can use the image, if available, to identify which elements are focused and enabled, and are important for the flow of the journey.

    Output format:
    Please generate the output in JSON format with following keys - 
    ranked_actions - this should be a list of dictionaries based on the list of actionable elements provided above. 
        In the output, each dictionary in the list of "ranked_actions" should be the same as the actionable element with one additional field added "llm_rank"
        "llm_rank" should reflect the priority given to that element to act on in ascending order.
    explanation - This should include your understanding of the screen in short based on the elements given. And then the reasoning for the priority order generated.

    Generate the output in JSON only, without any additional text.
"""

action_prioritization_template = """
  Following screen context describes the mobile app screen in short:
{screen_context}
Note: If no screen context is provided, create an understanding of the screen based on the list of actionable elements and any available image descriptions.

These are available actionable elements:
{actions}
Note: Each actionable element includes its node_id and properties (e.g., type, text, label). Use these to determine the appropriate action for each element.

This is the history of actions done previously:
{history}
Note: The history contains the action_description of all interactions performed so far. Use this to determine progress, avoid redundancy, and assess whether the journey is complete.

This is the user prompt provided by the user to help understand the possible user journey:
{user_prompt}
Note: If no user prompt is provided, infer the user journey based on the objective and available information.

Objective:
{objective}

General Guidelines:
1. Avoid actions that exit the app (e.g., closing the app or navigating to external links) unless specified in the objective.
2. Do not interact with elements identified as advertisements.
3. Assign lower priority to actions that may cause loops or redundant states, unless they align with the objective.
4. Include only actions necessary to achieve the objective, ranked in the logical sequence of the user journey. For example, on a login screen, the sequence should be: enter username, enter password, check required checkboxes, then click the login button.
5. Use the annotated image, if available, to understand the layout, identify focused or prominent elements, and determine their importance in the journey.
6. All provided actionable elements are clickable, enabled, and displayed on the screen.
7. Determine actions based on element types and context:
   - Buttons and links: "click"
   - Text fields: "enter text"
   - Checkboxes: "check" or "uncheck" (based on the objective; default to "check" if beneficial, exclude if irrelevant)
   - Radio buttons: "select"
   - Dropdowns: "select an option"
   - Other elements: infer based on common usage patterns
8. Create highly specific action descriptions that include:
   - The exact action to be performed (click, enter text, select, check, uncheck)
   - The specific element being interacted with (including visible text/label)
   - The screen context or location (e.g., "on the Login screen", "in the Payment section")
   - Any relevant purpose or outcome of the action (e.g., "to proceed to checkout", "to confirm order details")
9. Consider dependencies (e.g., filling fields before clicking a submit button) and screen cues (e.g., a focused text field as the next action).
10. Carefully evaluate if the journey is completed based on:
    - The objective has been fully achieved according to the history
    - No further relevant actions are available or necessary
    - The current screen state indicates completion (e.g., confirmation screen)

Output Format:
Generate the output in JSON format with the following keys:
- ranked_actions: A list of objects, each containing:
  - node_id: The integer node_id of the actionable element.
  - action_description: A detailed string describing the action to be performed (e.g., "Click the 'Login' button on the authentication screen to access your account", "Enter email address in the highlighted field on the registration form").
  The list must be ordered from highest to lowest priority, reflecting the sequence to achieve the objective.
  If the journey is completed and no further actions are required, this list should be empty [].
- explanation: A string including:
  - A brief understanding of the screen based on the provided information.
  - Reasoning for the action selection and priority order, explaining their necessity and sequence.
  - If the journey is complete, explain why no further actions are needed.
- journey_completed: A boolean indicating whether the user journey is completed based on the objective and history.
  Set to true when:
  - All necessary actions to achieve the objective have been performed in the history
  - No further actionable elements are necessary to complete the objective
  - Set to false when additional actions are still required to fulfill the objective

Generate the output in JSON only, without additional text.
"""

action_prioritization_template_objective_phase_1 = """
    You are navigating a mobile app. On a given screen there would be a number of elements which are actionable.
    You are intended to help reaching the home screen of the app by performing the necessary next steps by providing a priority order to the actionable elements on the screen.
    Use the history of actions performed till now to optimise the path to reach the home screen in as few steps as possible.
    This priority order should help make the navigation optimised to reach the home screen of the app.
    Some guidelines specific for this objective are - 
    1. Actions that lead to proceeding the particular user journey to reach home screen based on what actions have been done till now(if available) should be given higher priority.
    2. Any actions that would take use away from home screen should be of lower priority.
    3. Any actions that would make the journey to home screen go into loops or make the journey longer should be of lower priority
"""

action_prioritization_template_objective_phase_2_v1 = """
    You are navigating a mobile app. On a given screen there would be a number of elements which are actionable.
    You are intended to help in the exploration of the app by providing a priority order to the actionable elements on the screen.
    This priority order should help make the navigation optimised to explore the meaningful user journeys.
    Some guidelines for this objective are - 
    1. Use 'heuristic_score' mentioned for each action as one of the guides to give priority. Higher the heuristic score, higher the priority.
    
"""

action_prioritization_template_objective_phase_2_v2 = """
    You are navigating a mobile app. On a given screen there would be a number of elements which are actionable.
    You are intended to help in the exploration of the app by providing a priority order to the actionable elements on the screen.
    This priority order should help make the navigation optimised to explore the meaningful user journeys.
    Actions that lead to meaningful user journeys based on what actions have been done till now should be given higher priority.
"""

action_prioritization_template_objective_phase_2_v3 = """
You are on the home screen of a mobile app. Your goal is to identify and prioritize actions that initiate the most important and distinct user journeys.
 These journeys represent the primary functionalities or features of the app, such as logging in, searching, making a purchase, or accessing user settings.
 Prioritize actions that are unique entry points to different significant parts of the app, considering the prominence, labeling, and type of each actionable element. 
 Deprioritize actions that are redundant, lead to trivial interactions, or do not contribute to exploring new functionalities. 
 Since you are starting from the home screen, assume that no specific journey has been initiated yet, and your task is to select actions that begin these key journeys.
"""

action_prioritization_template_objective_phase_3 = """
You are navigating a mobile app. On a given screen there would be a number of elements which are actionable.
You are intended to help in completing the journey based on the history of actions performed till now by providing a priority order to the actionable elements on the screen.
This priority order should help make the navigation optimised to complete the user journey.
Additionally, determine if the user journey is completed based on the history of actions and the current actionable elements.
A journey is considered completed when the sequence of actions performed so far achieves a typical goal for that type of journey, and there are no further actions on the current screen necessary to continue the journey (e.g., after logging in, the user sees the home screen with no login-related elements).
Some guidelines specific for this objective are - 
1. If the journey is not completed, actions that lead to proceeding the particular user journey based on what actions have been done till now should be given higher priority.
2. Any actions that would take the user away from this particular journey should be of lower priority.
3. If the journey is completed, set 'journey_completed' to true in the output and provide an empty 'ranked_actions' list or actions relevant to a new journey, indicating the current journey is finished.
4. If the journey is not completed, set 'journey_completed' to false and prioritize actions to complete it.
"""

action_prioritization_template_objective_phase_2 = action_prioritization_template_objective_phase_2_v3

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


phase_objective_map = {
    "find-home-node" : {
        "stage": "1",
        "user_prompt": "Prioritize next steps to reach home screen in as less steps as possible",
        "objective": action_prioritization_template_objective_phase_1
    },
    "identify-journey-start-nodes" : {
        "stage": "1",
        "user_prompt": "Prioritize the action on the screen to identify the most important journeys",
        "objective": action_prioritization_template_objective_phase_2
    },
    "explore-user-journeys" : {
        "stage": "1",
        "user_prompt": "Complete the journey based on the history of actions performed",
        "objective": action_prioritization_template_objective_phase_3
    }
}