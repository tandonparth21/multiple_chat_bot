import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import PDFUploader from './components/PDFUploader';
import ChatWindow from './components/ChatWindow';
import ThemeToggle from './components/ThemeToggle';
import './index.css';
import './App.css';

const SUGGESTION_LIST = [
  "Summarize this PDF.",
  "List key takeaways.",
  "Who is the author?",
  "Explain this section.",
  "Show all tables.",
  "What are the main arguments?",
];

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(SUGGESTION_LIST);
  const chatEndRef = useRef(null);

  const handlePDFUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      setIsLoading(true);
      const response = await axios.post('/api/upload_pdf/', formData);
      setSessionId(response.data.session_id);
      setMessages([
        { role: 'bot', content: "PDF uploaded successfully! You can now ask questions about the document." }
      ]);
    } catch (error) {
      setMessages([{ role: 'bot', content: 'Error uploading PDF: ' + error.message }]);
    } finally {
      setIsLoading(false);
    }
  };

 const handleSendMessage = async () => {
  if (!input.trim() || !sessionId) return;
  const userMessage = { role: 'user', content: input };
  setMessages((prev) => [...prev, userMessage]);
  setInput('');
  setIsLoading(true);

  try {
    const response = await axios.post('/api/chat/', {
      user_message: input,
      session_id: sessionId,
    });

    // Beautify / format bot response
    let botText = response.data.bot_response || '';
    botText = botText.trim();

    // Capitalize first letter
    if (botText.length > 0) {
      botText = botText.charAt(0).toUpperCase() + botText.slice(1);
    }

    // Replace multiple spaces with single space
    botText = botText.replace(/\s+/g, ' ');

    // Optionally add period if missing
    if (!/[.!?]$/.test(botText)) {
      botText += '.';
    }

    setMessages((prev) => [...prev, { role: 'bot', content: botText }]);
  } catch (error) {
    setMessages((prev) => [...prev, { role: 'bot', content: 'Error: ' + error.message }]);
  } finally {
    setIsLoading(false);
  }
};


  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!input.trim()) {
      setSuggestions(SUGGESTION_LIST);
    } else {
      setSuggestions(
        SUGGESTION_LIST.filter(s => s.toLowerCase().includes(input.trim().toLowerCase()))
      );
    }
  }, [input]);

  return (
    <>
      {/* Theme toggle fixed at top right */}
      <ThemeToggle className="theme-toggle top-right" />

      <div className="container">
        <h1 className="header rainbow-text popin">PDF Chatbot</h1>
        <div className="card glass">
          <PDFUploader onUpload={handlePDFUpload} isLoading={isLoading} />
          <ChatWindow
            messages={messages}
            input={input}
            setInput={setInput}
            onSend={handleSendMessage}
            isLoading={isLoading}
            suggestions={suggestions}
            useSuggestion={handleSendMessage}
          />
          <div ref={chatEndRef} />
        </div>
        <footer className="footer fadein">
          <span>✨ Powered by React</span>
        </footer>
      </div>
    </>
  );
}

export default App;
