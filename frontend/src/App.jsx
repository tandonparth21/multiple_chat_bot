import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import PDFViewer from "./components/PDFViewer";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]); // Stores { name, pdf_id }
  const [uploadedPdfIds, setUploadedPdfIds] = useState([]); // Stores just the pdf_ids
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [infoMessage, setInfoMessage] = useState("");

  const chatBoxRef = useRef(null);

  // Scroll to the bottom of the chatbox when messages update
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && file.type === "application/pdf") {
      setSelectedFile(file);
      setInfoMessage(""); // Clear previous info messages
    } else {
      setSelectedFile(null);
      setInfoMessage("Please select a valid PDF file.");
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) {
      setInfoMessage("Please select a file first!");
      return;
    }

    setIsLoading(true);
    setInfoMessage("Uploading and processing PDF...");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      // Corrected: Endpoint is /upload/
      const response = await axios.post("http://127.0.0.1:8000/upload/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setInfoMessage(response.data.message || "File uploaded and processed successfully!");
      setUploadedFiles((prevFiles) => [...prevFiles, { name: selectedFile.name, pdf_id: response.data.pdf_id }]);
      setUploadedPdfIds((prevIds) => [...prevIds, response.data.pdf_id]); // Store the unique PDF ID
      setSelectedFile(null); // Clear selected file after upload
    } catch (error) {
      console.error("Error uploading file:", error.response?.data || error.message);
      setInfoMessage("Error uploading file: " + (error.response?.data?.detail || error.message || "Unknown error"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    if (uploadedPdfIds.length === 0) {
      setInfoMessage("Please upload at least one PDF before chatting.");
      return;
    }

    const newMessage = { sender: "user", text: inputMessage };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    setInputMessage("");
    setIsLoading(true);
    setInfoMessage("Getting response...");

    try {
      // Corrected: Request body key is 'question', and 'pdf_ids' are sent
      const response = await axios.post("http://127.0.0.1:8000/chat/", {
        question: inputMessage,
        pdf_ids: uploadedPdfIds, // Send all uploaded PDF IDs
      });

      // Corrected: Backend returns 'answer', not 'response'
      const botMessage = { sender: "bot", text: response.data.answer };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
      setInfoMessage("Response received!");
    } catch (error) {
      console.error("Error getting response:", error.response?.data || error.message);
      setInfoMessage("Error getting response: " + (error.response?.data?.detail || error.message || "Unknown error"));
      setMessages((prevMessages) => [...prevMessages, { sender: "bot", text: "Sorry, I couldn't get a response." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Chat with your PDFs</h1>

      <div className="upload-section">
        <h3>Upload PDF</h3>
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="file-input"
          id="pdf-upload"
        />
        <label htmlFor="pdf-upload" className="upload-label">
          Choose File
        </label>
        {selectedFile && <span> {selectedFile.name}</span>}
        <button onClick={handleFileUpload} disabled={isLoading || !selectedFile}>
          {isLoading ? "Uploading..." : "Upload & Process"}
        </button>
        {infoMessage && <p className="info">{infoMessage}</p>}

        {uploadedFiles.length > 0 && (
          <div className="uploaded-list">
            <h4>Uploaded PDFs:</h4>
            <ul>
              {uploadedFiles.map((file, index) => (
                <li key={file.pdf_id}>
                  {file.name} (ID: {file.pdf_id})
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="chat-section">
        <h3>Chat</h3>
        <div className="chat-box" ref={chatBoxRef}>
          {messages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.sender}`}>
              {msg.text}
            </div>
          ))}
        </div>
        <div className="input-row">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault(); // Prevent new line
                handleSendMessage();
              }
            }}
            placeholder="Type your message here..."
            rows="3"
            disabled={isLoading || uploadedPdfIds.length === 0} // Disable if no PDFs are uploaded
          ></textarea>
          <button onClick={handleSendMessage} disabled={isLoading || !inputMessage.trim() || uploadedPdfIds.length === 0}>
            Send
          </button>
        </div>
      </div>

      {/* Display the selected PDF in the viewer section */}
      <PDFViewer file={selectedFile} />
    </div>
  );
}

export default App;