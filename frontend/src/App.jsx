import { useState } from 'react';

function App() {
  const [prompt, setPrompt] = useState('');
  const [video, setVideo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState('Ready');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt) {
      setError('Please enter a prompt.');
      return;
    }

    setLoading(true);
    setError(null);
    setVideo(null);
    setStatus('Sending prompt to the AI model...');

    try {
      const response = await fetch('http://localhost:8000/api/v1/generate-video', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Something went wrong');
      }

      setStatus('Processing video... This may take a moment.');
      const data = await response.json();
      
      if (data.video) {
        setVideo(`data:video/mp4;base64,${data.video}`);
        setStatus('Video generated successfully!');
      } else {
        throw new Error("No video data received from the server.");
      }

    } catch (err) {
      setError(err.message);
      setStatus('An error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    // Set a fixed screen height to prevent the body's scrollbar
    <div className="h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-4">
      {/* Reduced vertical padding */}
      <div className="w-full max-w-2xl bg-gray-800 rounded-lg shadow-xl p-6">
        <h1 className="text-4xl font-bold text-center mb-2 text-cyan-400">AI Video Generator</h1>
        {/* Reduced bottom margin */}
        <p className="text-center text-gray-400 mb-4">Enter a prompt to generate a short video with a Hugging Face model.</p>
        
        <form onSubmit={handleSubmit}>
          {/* Fixed responsive layout for the form */}
          <div className="flex flex-col sm:flex-row gap-4 mb-4">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., An astronaut riding a horse on the moon"
              className="flex-grow bg-gray-700 text-white rounded-md p-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              disabled={loading}
            />
            <button
              type="submit"
              className="bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-3 px-6 rounded-md transition duration-300 ease-in-out disabled:bg-gray-500 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? 'Generating...' : 'Generate'}
            </button>
          </div>
        </form>

        {error && <div className="bg-red-500/20 text-red-300 p-3 rounded-md mt-4 text-center">{error}</div>}

        {/* Reduced top margin and minimum height */}
        <div className="mt-4 p-4 bg-gray-700/50 rounded-lg min-h-[64px] flex items-center justify-center">
            {/* -- ENHANCED LOADING INDICATOR -- */}
            {loading && (
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="animate-spin mr-3 text-cyan-400">
                    <path d="M5 22h14"/>
                    <path d="M5 2h14"/>
                    <path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22"/>
                    <path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2"/>
                </svg>
            )}
            <p className="text-gray-300 font-mono">{status}</p>
        </div>

        {/* Reduced top margin */}
        <div className="mt-4 flex flex-col items-center">
            <h2 className="text-2xl font-semibold mb-4 text-cyan-300">Generated Video</h2>
            {/* Reduced height of the video container */}
            <div className="w-full h-64 bg-gray-700 rounded-lg flex items-center justify-center overflow-hidden">
                {loading && (
                  <div className="flex flex-col items-center">
                    <div className="loader"></div>
                    <p className="text-gray-400 mt-4">AI is thinking...</p>
                  </div>
                )}
                {video ? (
                    <video controls autoPlay loop src={video} className="w-full h-full object-contain" />
                ) : (
                    !loading && <p className="text-gray-500">Video will appear here</p>
                )}
            </div>
        </div>
      </div>
    </div>
  );
}

export default App;
