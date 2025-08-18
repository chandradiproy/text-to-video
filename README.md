# AI Video Generator 🎬

This project is a web-based AI video generation application that transforms user-provided text prompts into short, dynamic videos. Built with a React frontend and a Python (FastAPI) backend, it leverages the Hugging Face Inference API to power its generative capabilities. The application is designed to be interactive and efficient, incorporating several advanced features to enhance the user experience and performance.

**Repository Link:** [https://github.com/chandradiproy/text-to-video](https://github.com/chandradiproy/text-to-video)

---

## ✨ Features

This application includes a range of features designed to provide a seamless and powerful user experience:

-   **📝 Text-to-Video Generation:** The core functionality allows users to enter a text prompt and generate a unique video.
-   **🎨 RAG-Style Prompt Enhancement:** Users can select a "style" (e.g., Cinematic, Anime, Pixel Art) from a dropdown menu. The backend augments the user's prompt with style-specific keywords to guide the AI model, resulting in more accurate and aesthetically pleasing videos.
-   **⚡ Real-Time Progress with WebSockets:** The entire generation process is communicated to the user in real-time using WebSockets. The UI displays live status updates, from prompt enhancement to the final video encoding, providing a transparent and engaging experience.
-   **🚀 In-Memory Caching:** To improve performance and reduce redundant API calls, the backend maintains an in-memory cache. If a user requests a video with the same prompt and style combination that has been generated before, the cached video is served instantly.
-   **💅 Modern & Responsive UI:** The frontend, built with React and styled with Tailwind CSS, is fully responsive and provides a clean, intuitive interface for users to interact with the application.
-   **🔔 Toast Notifications:** Error messages are displayed as non-intrusive toast notifications, ensuring a smooth user experience even when issues occur.

---

## 🛠️ Tech Stack

-   **Frontend:**
    -   React
    -   Vite
    -   Tailwind CSS
    -   React Toastify
-   **Backend:**
    -   Python 3.10+
    -   FastAPI
    -   Uvicorn
    -   WebSockets
    -   Hugging Face Hub (`huggingface-hub`)

---

## ⚙️ Setup and Installation

Follow these steps to set up and run the project locally.

### Prerequisites

-   Node.js and npm (or yarn)
-   Python 3.10+ and pip
-   A Hugging Face account and API Key

### 1. Clone the Repository

```bash
git clone [https://github.com/chandradiproy/text-to-video.git](https://github.com/chandradiproy/text-to-video.git)
cd text-to-video
```
### 2. Backend Setup
Navigate to the backend directory and create a virtual environment:
``` bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

Install the required Python packages:

pip install -r requirements.txt
```
### 3. Frontend Setup
In a separate terminal, navigate to the frontend directory and install the npm packages:
```
cd frontend
npm install
```
### 4. Environment Variables
The backend requires a Hugging Face API key to interact with the models.

In the backend directory, create a file named .env.

Add your Hugging Face API key to this file:
```
# backend/.env
HUGGING_FACE_API_KEY="hf_YourAccessTokenHere"

Security Note: The .env file is included in the .gitignore to prevent your API key from being committed to the repository.
```
🚀 Running the Application
Start the Backend Server
With your virtual environment activated, run the following command from the backend directory:

```
uvicorn app.main:app --reload
```
The backend server will start on http://localhost:8000.

Start the Frontend Development Server
In your other terminal, run the following command from the frontend directory:
```
npm run dev
```
The frontend development server will start, and you can access the application in your browser, typically at http://localhost:5173.

📂 Project Structure
```
text-to-video/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints.py      # WebSocket endpoint
│   │   ├── core/
│   │   │   └── config.py         # Configuration and environment variables
│   │   ├── services/
│   │   │   └── video_service.py  # Core video generation logic
│   │   └── main.py               # FastAPI application entrypoint
│   ├── .env.example              # Example environment file
│   └── requirements.txt          # Python dependencies
│
└── frontend/
    ├── public/
    ├── src/
    │   ├── App.jsx               # Main React component
    │   └── main.jsx              # Application entrypoint
    ├── index.html
    └── package.json              # Node.js dependencies
```
