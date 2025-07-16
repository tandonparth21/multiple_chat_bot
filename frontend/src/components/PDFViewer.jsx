import React from "react";
import { Document, Page } from 'react-pdf';
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

import * as pdfjs from 'pdfjs-dist';

// **NEW CDN APPROACH:**
// This line tells pdf.js to load its worker from an external CDN.
// This completely bypasses Vite's bundling and local serving of the worker.
// We're using pdfjs-dist@4.0.269, a recent stable version that react-pdf v10+ would typically expect.
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@4.0.269/build/pdf.worker.min.js`;

function PDFViewer({ file }) {
  if (!file) {
    return (
      <div className="viewer-section">
        <h3>PDF Viewer</h3>
        <p>Please upload a PDF to view.</p>
      </div>
    );
  }

  const [numPages, setNumPages] = React.useState(null);

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
  }

  return (
    <div className="viewer-section">
      <h3>PDF Viewer</h3>
      <Document
        file={file}
        onLoadSuccess={onDocumentLoadSuccess}
        onLoadError={(error) => {
          console.error("Error loading PDF document:", error);
        }}
      >
        {Array.from(
          new Array(numPages),
          (el, index) => (
            <Page
              key={`page_${index + 1}`}
              pageNumber={index + 1}
            />
          )
        )}
      </Document>
      {numPages && <p>Page 1 of {numPages} (showing all pages for demo)</p>}
    </div>
  );
}

export default PDFViewer;