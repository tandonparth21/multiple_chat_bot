import MessageBubble from './MessageBubble';

function ChatWindow({ messages, input, setInput, onSend, isLoading, suggestions, useSuggestion }) {
  return (
    <div className="chat-window fadein">
      <div className="chat-container">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        {isLoading && (
          <div className="spinner"></div>
        )}
      </div>

      <ul className="suggestions">
        {suggestions.slice(0, 4).map((suggestion, idx) => (
          <li key={idx} onClick={() => useSuggestion(suggestion)}>
            {suggestion}
          </li>
        ))}
      </ul>

      <div className="input-container">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && onSend()}
          placeholder="Ask a question about the PDF..."
          disabled={isLoading}
        />
        <button onClick={onSend} disabled={isLoading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatWindow;
