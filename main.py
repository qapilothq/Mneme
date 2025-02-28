from datetime import datetime
from llm import initialize_llm
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Any, Dict
from ui_tree import UITree
from utils import get_file_content, prioritize_actions, map_data_fields_to_ranked_actions, transform_popup_to_ranked_action
from xml_utils import parse_layout
from tools import check_for_popup, generate_test_data
from langsmith import traceable
from dotenv import load_dotenv
import os
import base64
import uuid
import traceback
import asyncio
import uvicorn
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()


app = FastAPI()

class APIRequest(BaseModel):
    request_id: Optional[str] = uuid.uuid4().hex
    image: Optional[str] = None
    user_prompt: Optional[str] = ""
    xml: Optional[str] = None
    history: Optional[list[Any]] = []
    xml_url: Optional[str] = None
    image_url: Optional[str] = None
    config_data: Optional[dict] = {}

def validate_base64(base64_string: str) -> bool:
    try:
        base64.b64decode(base64_string)
        return True
    except Exception:
        return False

@traceable
async def seek_guidance(request_id, xml, image, xml_url, image_url, config_data, user_prompt, history, llm):
    logging.info(f"requestid :: {request_id} :: Parsing XML to extract UI elements")
    # ui_elements_as_list = parse_layout(xml)
    uitree = UITree(request_id=request_id, xml=xml)
    logging.info(f"requestid :: {request_id} :: Number of elements found - {len(list(uitree.ui_element_dict_processed.values()))}")
    # screen_context = llm_generate_screen_context(xml, llm)
    screen_context = ""

    # check if the page has a pop up
    popup_check_start_time = datetime.now()
    popup_detected, pop_up_element = check_for_popup(request_id, xml, xml_url, image, image_url)
    logging.info(f"requestid :: {request_id} :: Time taken to check for popup :: {(datetime.now() - popup_check_start_time).total_seconds() * 1000} milliseconds")
    if popup_detected:
        return [transform_popup_to_ranked_action(request_id, pop_up_element)], "Pop up is identified, so need to close the popup to perform any further actions."
    else:
        # Run prioritize_actions and generate_test_data concurrently
        prioritize_task = asyncio.create_task(prioritize_actions(
            request_id=request_id, uitree=uitree, screen_context=screen_context, 
            image=image, actions=list(uitree.ui_element_dict_processed.values()), history=history,
            user_prompt=user_prompt, llm=llm
        ))
        
        generate_data_task = asyncio.create_task(generate_test_data(
            request_id, xml, xml_url, image, image_url, config_data
        ))

        # Wait for both tasks to complete
        ranked_actions, explanation = await prioritize_task
        data_gen_required, data_fields = await generate_data_task

        if data_gen_required:
            updated_ranked_actions = map_data_fields_to_ranked_actions(request_id, ranked_actions, data_fields)
            return updated_ranked_actions, explanation
        else:
            return ranked_actions, explanation

@traceable
@app.post("/invoke")
async def run_service(request: APIRequest) -> Dict[str, Any]:
    try:
        logging.info(f"requestid :: {request.request_id} :: Request processing starts")
        if request.xml_url:
            try:
                xml = get_file_content(request.xml_url, is_image=False)
            except Exception as e:
                logging.error(f"requestid :: {request.request_id} :: Exception in fetching XML from URL - {request.xml_url} - Exception - {str(e)} -- Stacktrace - {traceback.format_exc()}")
                raise(HTTPException(status_code=400, detail=f"requestid :: {request.request_id} :: Exception in fetching XML from URL - {request.xml_url}"))
        else:
            xml = request.xml

        if request.image_url:
            try:
                base64_image = get_file_content(request.image_url, is_image=True)
            except Exception as e:
                base64_image = None
                logging.error(f"requestid :: {request.request_id} :: Exception in fetching image from URL - {request.image_url} - Exception - {str(e)} -- Stacktrace - {traceback.format_exc()}")
        elif request.image:
            if not validate_base64(request.image):
                logging.error(f"requestid :: {request.request_id} :: Invalid base64 image data")
                raise HTTPException(status_code=400, detail="requestid :: {request_id} :: Invalid base64 image data")
            base64_image = request.image
        else:
            base64_image = None

        if request.config_data:
            config_data = request.config_data
        else:
            config_data = {}
        
        if xml is None:
            logging.error(f"requestid :: {request.request_id} :: Atleast xml or xml_url must be provided for guidance. Returning.")    
            raise HTTPException(status_code=400, detail="Atleast xml or xml_url must be provided for guidance")

        llm_key = os.getenv("OPENAI_API_KEY")
        if not llm_key:
            logging.error(f"requestid :: {request.request_id} :: LLM API key not found. Please check your environment variables")
            raise HTTPException(status_code=500, detail="LLM API key not found. Please check your environment variables.")
        llm = initialize_llm(llm_key)
        logging.info(f"requestid :: {request.request_id} :: LLM initialized")
        
        ranked_actions, explanation = await seek_guidance(request_id=request.request_id, xml=xml, image=base64_image, 
                                                    xml_url=request.xml_url, image_url=request.image_url,
                                                    config_data = config_data, user_prompt=request.user_prompt,
                                                    history=request.history, llm=llm)
        
        # Return the parsed output in the API response
        logging.info(f"requestid :: {request.request_id} :: Request Processing done")
        return {
            "request_id": request.request_id,
            "status": "success",
            "agent_response": {
                "ranked_actions": ranked_actions,
                "explanation": explanation
            }
        }
    except Exception as e:
        logging.error(f"requestid :: {request.request_id} :: Exception in Prioritization agent - {str(e)} -- {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"requestid :: {request.request_id} :: Exception in Prioritization agent - {str(e)} -- {traceback.format_exc()}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
