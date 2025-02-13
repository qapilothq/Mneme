# Mneme - Mobile App Exploration Guidance Agent

## Description

This project is a FastAPI-based application designed to process XML layouts and images to prioritize actions using a large language model. It leverages OpenAI's GPT-4o for reasoning-based prioritization and provides a RESTful API for interaction.

This agent integrates with [PopUp Handler](https://github.com/qapilothq/Valetudo) and [Test Data Generator](https://github.com/qapilothq/Euporie) to help the exploration be more contextual and provide data wherever required.

Current integration works like a microservice architecture. Stay tuned for a true multi-agent architecture.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/qapilothq/Mneme.git
   cd Mneme
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the root directory and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key
   POPUP_HANDLER_URL=popup_handler_API_endpoint
   TEST_DATA_GENERATOR_URL=test_data_generator_API_endpoint
   ```

## Usage

To run the application, use the following command:

    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```


## API Endpoints

- **POST /invoke**: Processes the input XML or image and returns prioritized actions.
  - **Request Body**: 
    - `image`: string | Base64 encoded image string (optional).
    - `user_prompt`: string | Custom user prompt (optional).
    - `xml`: string | XML string (optional).
    - `history`: list | List of previous actions (optional).
    - `xml_url`: URL string | URL to fetch XML (optional).
    - `image_url`: URL string | URL to fetch image (optional).
    - `config_data`: dict | Configuration data for test data generation (optional).
  - **Response**:
    - `status`: Success or error message.
    - `agent_response`: List of ranked elements to act on with metadata to identify the element, ordered with ranking using field `llm_rank`. Also has test data to fill based on the filed type
    - `explanation`: Explanation of the prioritization.

- **GET /health**: Returns the health status of the application.

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Contact
For questions or support, please contact **[contactus@qapilot.com](mailto:contactus@qapilot.com)**.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.