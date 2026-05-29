import React, { useState } from 'react'
import axios from 'axios'

const ALL_TEST_TYPES = [
  { id: 'soap-xml', label: 'SOAP XML Envelopes', soapOnly: true },
  { id: 'soapui', label: 'SoapUI Project', soapOnly: true },
  { id: 'postman', label: 'Postman Collection', soapOnly: false }
]

function triggerDownload(data, filename) {
  const url = window.URL.createObjectURL(new Blob([data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export default function DownloadPanel({ service, selectedFrameworks, frameworks }) {
  const [loadingFramework, setLoadingFramework] = useState(null)
  const [frameworkErrors, setFrameworkErrors] = useState({})
  const [selectedTestTypes, setSelectedTestTypes] = useState(['postman'])
  const [loadingTests, setLoadingTests] = useState(false)
  const [testsError, setTestsError] = useState(null)
  const [testsSuccess, setTestsSuccess] = useState(false)

  const showSoap = service.service_type === 'SOAP' || service.service_type === 'BOTH'

  const availableTestTypes = ALL_TEST_TYPES.filter(t => {
    if (t.soapOnly && !showSoap) return false
    return true
  })

  const allFrameworks = [...(frameworks.soap || []), ...(frameworks.rest || [])]

  const getFrameworkLabel = (id) => {
    const fw = allFrameworks.find(f => f.id === id)
    return fw ? fw.label : id
  }

  const handleDownloadFramework = async (frameworkId) => {
    setLoadingFramework(frameworkId)
    setFrameworkErrors(prev => ({ ...prev, [frameworkId]: null }))

    try {
      const response = await axios.post(
        '/api/generate',
        { service, framework: frameworkId },
        { responseType: 'blob' }
      )
      const filename = `${service.service_name || 'service'}-${frameworkId}.zip`
      triggerDownload(response.data, filename)
    } catch (err) {
      const msg = err.response
        ? `Server error: ${err.response.status}`
        : 'Network error. Is the backend running?'
      setFrameworkErrors(prev => ({ ...prev, [frameworkId]: msg }))
    } finally {
      setLoadingFramework(null)
    }
  }

  const toggleTestType = (id) => {
    setSelectedTestTypes(prev =>
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    )
  }

  const handleDownloadTests = async () => {
    if (selectedTestTypes.length === 0) return
    setLoadingTests(true)
    setTestsError(null)
    setTestsSuccess(false)

    try {
      const response = await axios.post(
        '/api/generate-tests',
        { service, test_types: selectedTestTypes },
        { responseType: 'blob' }
      )
      const filename = `${service.service_name || 'service'}-tests.zip`
      triggerDownload(response.data, filename)
      setTestsSuccess(true)
    } catch (err) {
      const msg = err.response
        ? `Server error: ${err.response.status}`
        : 'Network error. Is the backend running?'
      setTestsError(msg)
    } finally {
      setLoadingTests(false)
    }
  }

  return (
    <div>
      <div className="section-header">
        <div>
          <h2 className="section-title">Generate &amp; Download</h2>
          <p className="section-description">Download your generated project code and test files.</p>
        </div>
      </div>

      {/* Service Summary */}
      <div className="card summary-card">
        <h3 className="card-subtitle">Service Summary</h3>
        <div className="summary-grid">
          <div className="summary-item">
            <span className="summary-label">Name</span>
            <span className="summary-value">{service.service_name || <em>Unnamed</em>}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Type</span>
            <span className="summary-value">{service.service_type}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Version</span>
            <span className="summary-value">{service.version}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Methods</span>
            <span className="summary-value">{service.methods.length}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Models</span>
            <span className="summary-value">{service.models.length}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Frameworks</span>
            <span className="summary-value">
              {selectedFrameworks.length > 0 ? selectedFrameworks.join(', ') : <em>None selected</em>}
            </span>
          </div>
        </div>
      </div>

      {/* Download Projects */}
      <div className="card">
        <h3 className="card-subtitle">Download Projects</h3>
        <p className="card-description">Download a ZIP containing the generated project for each framework.</p>

        {selectedFrameworks.length === 0 && (
          <div className="alert alert-warning">
            No frameworks selected. Go back to step 4 to choose at least one framework.
          </div>
        )}

        <div className="download-buttons">
          {selectedFrameworks.map(fwId => (
            <div key={fwId} className="download-item">
              <button
                className="btn btn-primary download-btn"
                onClick={() => handleDownloadFramework(fwId)}
                disabled={loadingFramework === fwId}
              >
                {loadingFramework === fwId ? (
                  <>
                    <span className="spinner" />
                    Generating...
                  </>
                ) : (
                  <>
                    &#8681; Download {getFrameworkLabel(fwId)}
                  </>
                )}
              </button>
              {frameworkErrors[fwId] && (
                <p className="error-msg">{frameworkErrors[fwId]}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Download Tests */}
      <div className="card">
        <h3 className="card-subtitle">Download Tests</h3>
        <p className="card-description">Select the test artifact types to include in the download.</p>

        <div className="test-type-options">
          {availableTestTypes.map(testType => (
            <label key={testType.id} className={`test-type-card ${selectedTestTypes.includes(testType.id) ? 'selected' : ''}`}>
              <input
                type="checkbox"
                checked={selectedTestTypes.includes(testType.id)}
                onChange={() => toggleTestType(testType.id)}
              />
              <span>{testType.label}</span>
            </label>
          ))}
        </div>

        <button
          className="btn btn-primary download-btn"
          onClick={handleDownloadTests}
          disabled={loadingTests || selectedTestTypes.length === 0}
        >
          {loadingTests ? (
            <>
              <span className="spinner" />
              Generating Tests...
            </>
          ) : (
            <>&#8681; Download Tests ZIP</>
          )}
        </button>

        {testsError && (
          <p className="error-msg" style={{ marginTop: '0.75rem' }}>{testsError}</p>
        )}
        {testsSuccess && (
          <p className="success-msg" style={{ marginTop: '0.75rem' }}>Tests downloaded successfully!</p>
        )}
      </div>
    </div>
  )
}
