from llm import initialize_llm
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from utils import parse_layout, encode_image, get_file_content, prioritize_actions, llm_generate_screen_context

from dotenv import load_dotenv
import os
import json  


load_dotenv()

app = FastAPI()

class APIRequest(BaseModel):
    image: Optional[str] = None
    user_prompt: Optional[str] = ""
    xml: Optional[str] = None
    history: Optional[list] = []
    xml_url: Optional[str] = None
    image_url: Optional[str] = None

def process_xml(xml, history, llm):
    ui_elements = parse_layout(xml)
    # screen_context = llm_generate_screen_context(xml, llm)
    screen_context = ""

    # Prioritize actions
    ranked_actions, explanation = prioritize_actions(screen_context=screen_context, 
                                        actions=ui_elements, 
                                        history=history, 
                                        llm=llm)
    return ranked_actions, explanation

@app.post("/invoke")
async def run_service(request: APIRequest):
    try:
        llm_key = os.getenv("OPENAI_API_KEY")
        if not llm_key:
            raise HTTPException(status_code=500, detail="API key not found. Please check your environment variables.")
        llm = initialize_llm(llm_key)

        if request.xml_url:
            xml = get_file_content(request.xml_url, is_image=False)
            ranked_actions, explanation = process_xml(xml, request.history, llm)
        elif request.xml:
            ranked_actions, explanation = process_xml(xml, request.history, llm)
        elif request.image_url:
            base64_image = get_file_content(request.image_url, is_image=True)
            encoded_image = encode_image(base64_image)
            ranked_actions = []
        elif request.image:
            encoded_image = encode_image(request.image)
            ranked_actions = []
        else:
            raise HTTPException(status_code=400, detail="Either image or xml must be provided.")

        # Output ranked actions
        # for action in ranked_actions:
        #     print(f"Action: {action['description']}")
        #     print(f"  Final Score: {action['final_score']}")
        #     print(f"  Explanation: {action['explanation']}")
        #     print()
        print(f"No of Actions: {len(ranked_actions)}")
        
        # Return the parsed output in the API response
        return {
            "status": "success",
            "agent_response": ranked_actions,
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
