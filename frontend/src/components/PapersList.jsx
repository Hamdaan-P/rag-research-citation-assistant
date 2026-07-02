import { useState, useEffect } from 'react'

function PapersList({ onExpandedChange } = {}) {
  const [papers, setPapers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deletingTitle, setDeletingTitle] = useState(null)
  const [expanded, setExpanded] = useState(false)

  const fetchPapers = async () => {
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/papers')
      const data = await response.json()

      if (response.ok) {
        setPapers(data.papers)
        setError('')
      } else {
        setError(data.detail)
        setPapers([])
      }
    } catch (err) {
      setError(err.message)
      setPapers([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPapers()
  }, [])

  const handleDelete = async (title) => {
    setDeletingTitle(title)

    try {
      const response = await fetch(
        `http://localhost:8000/papers/${encodeURIComponent(title)}`,
        { method: 'DELETE' }
      )

      if (response.ok) {
        await fetchPapers()
      }
    } finally {
      setDeletingTitle(null)
    }
  }

  const toggleExpanded = () => {
    const next = !expanded
    setExpanded(next)
    onExpandedChange?.(next)
  }

  const paperItem = (paper) => (
    <div key={paper.paper_title} className="paper-item">
      <div className="paper-info">
        <span>{paper.paper_title}</span>
      </div>
      <button
        type="button"
        className="delete-btn"
        onClick={() => handleDelete(paper.paper_title)}
        disabled={deletingTitle === paper.paper_title}
      >
        Delete
      </button>
    </div>
  )

  return (
    <div>
      <div className="papers-header">
        <h3>Reference Library</h3>
        <button type="button" className="toggle-btn" onClick={toggleExpanded}>
          {expanded ? 'Collapse' : `View all (${papers.length})`}
        </button>
      </div>

      {loading && <p>Loading papers...</p>}

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {!loading && !error && papers.length === 0 && (
        <p>No papers uploaded yet.</p>
      )}

      {expanded && !loading && !error && papers.length > 0 && (
        <div className="papers-scroll">
          {papers.map((paper) => paperItem(paper))}
        </div>
      )}
    </div>
  )
}

export default PapersList
