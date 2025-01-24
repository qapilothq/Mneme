# Mneme - Mobile App Exploration Guidance Agent

## Description

This project is a FastAPI-based application designed to process XML layouts and images to prioritize actions using a large language model. It leverages OpenAI's GPT-4o for reasoning-based prioritization and provides a RESTful API for interaction.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/yourproject.git
   cd yourproject
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
   ```

## Usage

To run the application, use the following command:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```


## API Endpoints

- **POST /invoke**: Processes the input XML or image and returns prioritized actions.
  - **Request Body**: 
    - `image`: Base64 encoded image string (optional).
    - `user_prompt`: Custom user prompt (optional).
    - `xml`: XML string (optional).
    - `history`: List of previous actions (optional).
    - `xml_url`: URL to fetch XML (optional).
    - `image_url`: URL to fetch image (optional).
  - **Response**:
    - `status`: Success or error message.
    - `agent_response`: List of ranked actions.
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