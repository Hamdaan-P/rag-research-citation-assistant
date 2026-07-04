import { useState } from 'react'

function QueryPapers({ onResult, onError }) {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    setLoading(true)
    onResult(null)
    onError('')

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })

      const data = await response.json()

      if (response.ok) {
        onResult(data)
        onError('')
      } else {
        onError(data.detail)
        onResult(null)
      }
    } catch (err) {
      onError('Could not reach the server. Please check your connection and try again.')
      onResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ textAlign: 'left' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxWidth: '400px' }}>
        <textarea
          className="textarea-input"
          style={{ width: '100%', height: '80px' }}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Describe your research topic..."
        />
        <button
          type="button"
          className="primary-btn"
          onClick={handleSearch}
          disabled={loading || !query.trim()}
        >
          Search
        </button>
      </div>
    </div>
  )
}

export default QueryPapers
