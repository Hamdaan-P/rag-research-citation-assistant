import { useState } from 'react'
import './App.css'
import UploadPaper from './components/UploadPaper'
import QueryPapers from './components/QueryPapers'
import PapersList from './components/PapersList'

function splitIntoParagraphs(text) {
  if (!text) return []

  const byDoubleNewline = text.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean)
  if (byDoubleNewline.length > 1) return byDoubleNewline

  return text.split(/\n/).map((p) => p.trim()).filter(Boolean)
}

function App() {
  const [libraryExpanded, setLibraryExpanded] = useState(false)
  const [queryResult, setQueryResult] = useState(null)
  const [queryError, setQueryError] = useState('')

  return (
    <div className="app-container">
      <div className="app-header">
        <h1>Research Citation Assistant</h1>
        <p className="app-subtitle">
          Upload papers, search your library, and generate cited related work summaries.
        </p>
      </div>

      <div className="app-top-row">
        <div>
          <PapersList onExpandedChange={setLibraryExpanded} />
        </div>
        <div>
          <h4 className="section-label">Search your library</h4>
          <QueryPapers onResult={setQueryResult} onError={setQueryError} />
        </div>
        <div>
          <h4 className="section-label">Add a paper</h4>
          <UploadPaper />
        </div>
      </div>

      {(queryResult !== null || queryError !== '') && (
        <div className="app-summary-section">
          {queryError && <p style={{ color: 'red' }}>{queryError}</p>}
          {queryResult && (
            <div className="result-card">
              <h3 className="result-heading">Related Work Summary</h3>
              {splitIntoParagraphs(queryResult.summary).map((paragraph, index) => (
                <p key={index} className="result-summary" style={{ marginBottom: '16px' }}>
                  {paragraph}
                </p>
              ))}
              <h4 className="source-label">Source Papers</h4>
              <div className="source-pills">
                {queryResult.source_papers.map((title) => (
                  <span key={title} className="pill">{title}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default App
