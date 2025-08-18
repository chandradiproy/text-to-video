import { useState, useRef, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
// The CSS import is removed from here and moved to main.jsx

function App() {
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('Cinematic');
  const [video, setVideo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState('Ready to generate your video');
  const [progress, setProgress] = useState(0);

  const websocket = useRef(null);

  // --- Wake up the backend on initial page load ---
  useEffect(() => {
    // Use process.env for environment variables
    const wsUrl = "wss://text-to-video-p960.onrender.com/api/v1/ws/generate-video"
    const httpUrl = wsUrl.replace('wss://', 'https://').replace('ws://', 'http://').split('/api/v1/ws/generate-video')[0];
    const healthCheckUrl = `${httpUrl}/api/v1/health`;

    console.log("Pinging backend to wake it up...");
    fetch(healthCheckUrl)
      .then(res => {
        if (res.ok) {
          console.log("Backend is awake.");
        } else {
          console.warn("Backend ping failed, it might be starting up.");
        }
      })
      .catch(err => console.error("Error pinging backend:", err));
  }, []); // Empty dependency array ensures this runs only once on mount

  // Effect to show toast notification when an error occurs
  useEffect(() => {
    if (error) {
      toast.error(error);
      setError(null);
    }
  }, [error]);

  // Simulate progress for better UX
  useEffect(() => {
    let interval;
    if (loading) {
      interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) return prev;
          return prev + Math.random() * 10;
        });
      }, 1000);
    } else {
      setProgress(0);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim()) {
      setError('Please enter a valid prompt.');
      return;
    }

    setLoading(true);
    setVideo(null);
    setProgress(0);
    setStatus('Connecting to AI server...');

    const wsUrl = "wss://text-to-video-p960.onrender.com/api/v1/ws/generate-video";
    websocket.current = new WebSocket(wsUrl);

    websocket.current.onopen = () => {
      console.log("WebSocket connection established.");
      setStatus('Connected! Sending your prompt...');
      websocket.current.send(JSON.stringify({ prompt, style }));
    };

    websocket.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.status) {
        setStatus(data.status);
      }
      
      if (data.video) {
        setVideo(`data:video/mp4;base64,${data.video}`);
        setLoading(false);
        setProgress(100);
        setStatus('Video generated successfully!');
        websocket.current.close();
      }
      
      if (data.error) {
        setError(data.error);
        setStatus('Generation failed. Please try again.');
        setLoading(false);
      }
    };

    websocket.current.onerror = (event) => {
      console.error("WebSocket error:", event);
      setError('Unable to connect to server. Is it running?');
      setLoading(false);
      setStatus('Connection failed');
    };

    websocket.current.onclose = () => {
      console.log("WebSocket connection closed.");
      if (loading) {
        setLoading(false);
        setStatus('Connection interrupted');
      }
    };
  };

  const clearVideo = () => {
    setVideo(null);
    setStatus('Ready to generate your video');
  };

  return (
    <>
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
      />
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
        {/* Header */}
        <div className="pt-8 pb-4 px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent mb-3">
              AI Video Generator
            </h1>
            <p className="text-gray-300 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
              Transform your ideas into stunning videos with the power of AI
            </p>
          </div>
        </div>

        {/* Main Content */}
        <div className="px-4 pb-8">
          <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              
              {/* Input Section */}
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-700/50 p-6 md:p-8">
                <form onSubmit={handleSubmit} className="space-y-6">
                  
                  {/* Prompt Input */}
                  <div className="space-y-3">
                    <label htmlFor="prompt" className="block text-sm font-semibold text-cyan-300 uppercase tracking-wide">
                      Your Creative Prompt
                    </label>
                    <div className="relative">
                      <textarea
                        id="prompt"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder="Describe your vision... e.g., A majestic dragon soaring through clouds at sunset"
                        rows={4}
                        className="w-full bg-gray-700/70 text-white rounded-xl p-4 focus:outline-none focus:ring-3 focus:ring-cyan-500/50 focus:bg-gray-700 transition-all duration-300 border border-gray-600/50 resize-none placeholder-gray-400"
                        disabled={loading}
                      />
                      <div className="absolute bottom-3 right-3 text-xs text-gray-400">
                        {prompt.length}/500
                      </div>
                    </div>
                  </div>

                  {/* Style Selection */}
                  <div className="space-y-3">
                    <label htmlFor="style" className="block text-sm font-semibold text-cyan-300 uppercase tracking-wide">
                      Video Style
                    </label>
                    <select
                      id="style"
                      value={style}
                      onChange={(e) => setStyle(e.target.value)}
                      className="w-full bg-gray-700/70 text-white rounded-xl p-4 focus:outline-none focus:ring-3 focus:ring-cyan-500/50 focus:bg-gray-700 transition-all duration-300 border border-gray-600/50 cursor-pointer"
                      disabled={loading}
                    >
                      <option value="Default">Default</option>
                      <option value="Cinematic">Cinematic</option>
                      <option value="Anime">Anime</option>
                      <option value="Pixel Art">Pixel Art</option>
                      <option value="Documentary">Documentary</option>
                      <option value="Fantasy">Fantasy</option>
                      <option value="Sci-Fi">Sci-Fi</option>
                    </select>
                  </div>

                  {/* Generate Button */}
                  <button
                    type="submit"
                    disabled={loading || !prompt.trim()}
                    className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold py-4 px-6 rounded-xl transition-all duration-300 ease-in-out disabled:cursor-not-allowed transform hover:scale-[1.02] hover:shadow-lg hover:shadow-cyan-500/25 disabled:scale-100 disabled:shadow-none"
                  >
                    {loading ? (
                      <div className="flex items-center justify-center space-x-3">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                        </svg>
                        <span>Generating Magic...</span>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center space-x-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span>Generate Video</span>
                      </div>
                    )}
                  </button>
                </form>

                {/* Status Section */}
                {(loading || status !== 'Ready to generate your video') && (
                  <div className="mt-6 p-4 bg-gray-700/30 rounded-xl border border-gray-600/30">
                    <div className="flex items-center space-x-3 mb-3">
                      {loading && (
                        <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
                      )}
                      <span className="text-sm font-medium text-gray-300">{status}</span>
                    </div>
                    
                    {loading && (
                      <div className="w-full bg-gray-600 rounded-full h-2 overflow-hidden">
                        <div 
                          className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full rounded-full transition-all duration-500 ease-out"
                          style={{ width: `${Math.min(progress, 100)}%` }}
                        ></div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Video Display Section */}
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-700/50 p-6 md:p-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-cyan-300">Generated Video</h2>
                  {video && (
                    <button
                      onClick={clearVideo}
                      className="text-gray-400 hover:text-white transition-colors duration-200 p-2 hover:bg-gray-700/50 rounded-lg"
                      title="Clear video"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>

                <div className="relative">
                  <div className="w-full aspect-video bg-gray-700/50 rounded-xl border-2 border-dashed border-gray-600/50 flex items-center justify-center overflow-hidden">
                    {loading ? (
                      <div className="flex flex-col items-center space-y-4 p-8 text-center">
                        <div className="relative">
                          <div className="w-16 h-16 border-4 border-gray-600 border-t-cyan-400 rounded-full animate-spin"></div>
                          <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-blue-400 rounded-full animate-spin animation-delay-75"></div>
                        </div>
                        <div>
                          <p className="text-gray-300 font-medium">AI is creating your video...</p>
                          <p className="text-gray-400 text-sm mt-1">This may take a few moments</p>
                        </div>
                      </div>
                    ) : video ? (
                      <div className="w-full h-full relative group">
                        <video 
                          controls 
                          autoPlay 
                          loop 
                          src={video} 
                          className="w-full h-full object-contain rounded-lg"
                        />
                        <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                          <a 
                            href={video} 
                            download="ai-generated-video.mp4"
                            className="bg-black/50 backdrop-blur-sm text-white px-3 py-2 rounded-lg text-sm hover:bg-black/70 transition-colors duration-200 flex items-center space-x-2"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <span>Download</span>
                          </a>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center p-8">
                        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-700/50 flex items-center justify-center">
                          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                        </div>
                        <p className="text-gray-400 font-medium">Your video will appear here</p>
                        <p className="text-gray-500 text-sm mt-1">Enter a prompt and click generate to start</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Video Info */}
                {video && (
                  <div className="mt-4 p-4 bg-gray-700/30 rounded-xl">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Style:</span>
                        <span className="text-white ml-2 font-medium">{style}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Status:</span>
                        <span className="text-green-400 ml-2 font-medium">Ready</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
