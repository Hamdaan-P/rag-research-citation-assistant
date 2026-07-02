import { useState } from 'react'

function UploadPaper() {
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(false)

  const handleUpload = async () => {
    setLoading(true)

    const formData = new FormData()
    formData.append('paper_title', title)
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (response.ok) {
        setStatus(
          `Uploaded successfully: ${data.paper_title}, ${data.chunks_stored} chunks stored`
        )
      } else {
        setStatus(data.detail)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxWidth: '400px' }}>
      <input
        type="text"
        className="text-input"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Paper title"
      />
      <input
        type="file"
        className="file-input"
        accept="application/pdf"
        onChange={(e) => setFile(e.target.files[0])}
      />
      <button type="button" className="primary-btn" onClick={handleUpload} disabled={loading}>
        Upload Paper
      </button>
      <p>{status}</p>
    </div>
  )
}

export default UploadPaper
