
# **AI Video Generator & WhatsApp Bot 🎬🤖**

This project is a sophisticated, multi-interface AI video generation application. It allows users to transform text prompts into short, dynamic videos through two distinct clients: a modern, real-time **React web application** and a conversational **WhatsApp bot**.

Built with a decoupled architecture, the system features a React frontend and a powerful Python (FastAPI) backend. The backend leverages multiple AI services, a persistent database, and advanced conversational logic to deliver a seamless and feature-rich experience on both platforms.

**Repository Link:** [https://github.com/chandradiproy/text-to-video](https://github.com/chandradiproy/text-to-video)

---

## **✨ Features**

The application is packed with features that enhance user experience, performance, and functionality across both the web and WhatsApp interfaces.

### **Core Backend Features**

- **🤖 Dual Interface Support**: A single backend serves both the web app (via WebSockets) and the WhatsApp bot (via HTTP webhooks).  
- **🧠 LLM-Powered Prompt Analysis**: Uses the **Groq API** (Llama 3.1) to intelligently analyze user prompts, detect artistic styles, and determine if more information is needed, creating a natural conversational flow.  
- **💾 Persistent Data with MongoDB**: User states, generation history, and custom-defined styles are stored in a MongoDB Atlas database.  
- **⚡ Asynchronous Task Handling**: Employs FastAPI's BackgroundTasks to process video generation requests without blocking.  
- **🎬 Media Optimization**: Automatically checks video file sizes and uses **MoviePy** to compress videos that exceed WhatsApp's 16MB limit.  
- **🔒 Secure Configuration**: All API keys and secrets are managed securely using a `.env` file.

### **💻 Web Application Features**

- **🎨 Modern & Responsive UI**: Built with **React** + **Tailwind CSS**, offering a clean, intuitive experience.  
- **⚡ Real-Time Progress with WebSockets**: Streams live status updates—from connection to generation to encoding.  
- **🚀 In-Memory Caching**: Repeated requests for the same prompt/style are served instantly.  
- **🔔 Non-Intrusive Notifications**: Uses `react-toastify` to show user-friendly error messages.

### **📱 WhatsApp Bot Features**

- **💬 Conversational AI Flow**: If a prompt is ambiguous, the bot asks for clarification with style choices.  
- **📜 Command System**:  
  - `/help`: Displays all available commands.  
  - `/history`: Shows last 5 video generations with links.  
  - `/status`: Checks if a video is being generated.  
  - `/styles`: Lists all custom styles created by the user.  
  - `/createstyle <name> "<prompt>"`: Save reusable style prompts.  
  - `/deletestyle <name>`: Deletes a custom style.  
  - `/cancel`: Aborts the current operation.  
- **💡 Smart Caching**: Suggests reusing previously generated videos.  
- **🔄 Proactive Status Updates**: Notifies users at key steps like “AI is working...” or “Compressing your video...”.

---

## **🛠️ Tech Stack**

- **Frontend:**  
  React, Vite, Tailwind CSS, React Toastify  

- **Backend:**  
  Python 3.10+, FastAPI, Uvicorn, WebSockets  

- **AI & External Services:**  
  - Hugging Face (Text-to-Video Model: `fal-ai/Wan-AI/Wan2.2-T2V-A14B`)  
  - Groq (LLM prompt analysis)  
  - Twilio (WhatsApp API integration)  

- **Database:**  
  MongoDB (via MotorDB for async ops)  

- **Media Processing:**  
  MoviePy  

---

## **⚙️ Setup and Installation**

### **Prerequisites**

- Node.js + npm (or yarn)  
- Python 3.10+ and pip  
- **ngrok** (for Twilio webhook tunneling)  
- Accounts & API keys: **Hugging Face**, **Twilio**, **MongoDB Atlas**, **Groq**

---

### **1. Clone the Repository**

```bash
git clone https://github.com/chandradiproy/text-to-video.git
cd text-to-video
````

---

### **2. Backend Setup**

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

* **macOS/Linux**

  ```bash
  source venv/bin/activate
  ```

* **Windows**

  ```powershell
  venv\Scripts\activate
  ```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### **3. Frontend Setup**

```bash
cd ../frontend
npm install
```

---

### **4. Environment Variables**

Create a `.env` file inside `backend/` and add:

```env
HUGGING_FACE_API_KEY="hf_YourHuggingFaceToken"
GROQ_API_KEY="gsk_YourGroqToken"
MONGODB_URI="mongodb+srv://user:password@cluster.mongodb.net/your_db"

TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN="your_twilio_auth_token"
TWILIO_WHATSAPP_NUMBER="+14155238886"  # Twilio Sandbox Number
```

---

### **5. Configure Twilio Webhook (with ngrok)**

1. Start ngrok:

   ```bash
   ngrok http 8000
   ```

2. Copy the `https://<unique-id>.ngrok-free.app` URL.

3. Go to **Twilio Console → Messaging → WhatsApp Sandbox Settings**.

4. Set **WHEN A MESSAGE COMES IN** to:

   ```
   https://<unique-id>.ngrok-free.app/api/v1/bot/webhook/twilio
   ```

   (method: **HTTP POST**)

5. Save changes.

---

## **🚀 Running the Application**

1. **Start Backend**

   ```bash
   cd backend
   python run.py
   ```

   Runs on: [http://localhost:8000](http://localhost:8000)

2. **Start Frontend**

   ```bash
   cd frontend
   npm run dev
   ```

   Access at: [http://localhost:5173](http://localhost:5173)

3. **Interact with WhatsApp Bot**

   * Join Twilio Sandbox (send `join <code>` to sandbox number).
   * Start sending prompts/commands!

---

## **📂 Project Structure**

```
text-to-video/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints.py        # WebSocket router for Web App
│   │   │   └── whatsapp_router.py  # WhatsApp Bot webhook
│   │   ├── core/
│   │   │   └── config.py           # Env config
│   │   ├── db/
│   │   │   └── database.py         # MongoDB connection
│   │   ├── services/
│   │   │   ├── llm_service.py      # Groq prompt analysis
│   │   │   └── video_service.py    # Video generation & messaging
│   │   └── main.py                 # FastAPI entrypoint
│   ├── .env                        # Secret keys (ignored by git)
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   └── App.jsx                 # Main React component
    └── package.json
```

---

