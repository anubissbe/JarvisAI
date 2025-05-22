# ... existing code ...

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/anubissbe/JarvisAI.git
   cd JarvisAI
   ```

2. Create a `.env` file in the root directory with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   JWT_SECRET_KEY=your_jwt_secret_key
   ```

3. Make the control script executable:
   ```bash
   chmod +x jarvis.sh
   ```

4. Start the application using the control script:
   ```bash
   ./jarvis.sh start
   ```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - MongoDB Express (database UI): http://localhost:8081

### Using the Control Script

JarvisAI comes with a control script (`jarvis.sh`) that helps you manage the application:

- **Start the application**:
  ```bash
  ./jarvis.sh start
  ```
  This will check your environment, start all containers, and optionally monitor for errors.

- **Check application status**:
  ```bash
  ./jarvis.sh status
  ```
  Shows the status of all containers and checks if services are accessible.

- **View logs**:
  ```bash
  ./jarvis.sh logs          # All logs
  ./jarvis.sh logs backend  # Only backend logs
  ./jarvis.sh logs frontend # Only frontend logs
  ```

- **View error logs**:
  ```bash
  ./jarvis.sh errors
  ```
  Shows the contents of the error.log file.

- **Stop the application**:
  ```bash
  ./jarvis.sh stop
  ```

- **Restart the application**:
  ```bash
  ./jarvis.sh restart
  ```

- **Clean up everything**:
  ```bash
  ./jarvis.sh clean
  ```
  Stops containers and removes volumes.

### Required Configuration

After installation, you'll need to configure the following:

1. **OpenAI API Key**: Required for the AI functionality. Get one from [OpenAI's website](https://platform.openai.com/api-keys).

2. **Integration API Keys**: To use specific integrations, you'll need to add API keys in the settings page:
   - Weather: Get an API key from [OpenWeatherMap](https://openweathermap.org/api)
   - Email: Configure your SMTP server details
   - Calendar: Set up OAuth credentials for calendar access
   - Music: Configure music service API keys

3. **Voice Settings**: Customize the voice used for responses in the settings page.

4. **AI Model Settings**: Choose which AI model to use and adjust parameters like temperature.

# ... existing code ...