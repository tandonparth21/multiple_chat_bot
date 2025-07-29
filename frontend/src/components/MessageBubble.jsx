function MessageBubble({ message }) {
  return (
    <div className={`message-bubble ${message.role}`}>
      {message.content}
    </div>
  );
}
export default MessageBubble;
