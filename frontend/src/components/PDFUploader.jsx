import { useState } from "react";

function PDFUploader({ onUpload, isLoading }) {
  const [drag, setDrag] = useState(false);

  const handleFileChange = e => {
    const file = e.target.files[0];
    if (file && file.type === "application/pdf") {
      onUpload(file);
    } else {
      alert("Please upload a valid PDF file.");
    }
  };

  const handleDragOver = e => {
    e.preventDefault();
    setDrag(true);
  };
  const handleDragLeave = e => {
    e.preventDefault();
    setDrag(false);
  };
  const handleDrop = e => {
    e.preventDefault();
    setDrag(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
      onUpload(file);
    } else {
      alert("Please upload a valid PDF file.");
    }
  };

  return (
    <div
      className={`uploader${drag ? " dragging" : ""}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      tabIndex={0}
    >
      <label>
        {isLoading ? "Uploading..." : (drag ? "Drop PDF here!" : "📄 Upload PDF")}
      </label>
      <input
        type="file"
        accept="application/pdf"
        onChange={handleFileChange}
        disabled={isLoading}
      />
    </div>
  );
}

export default PDFUploader;
