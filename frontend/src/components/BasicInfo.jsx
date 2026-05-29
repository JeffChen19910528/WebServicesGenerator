import React from 'react'

export default function BasicInfo({ service, setService }) {
  const update = (field, value) => {
    setService(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="card">
      <h2 className="card-title">Basic Service Information</h2>
      <p className="card-description">Define the fundamental properties of your web service.</p>

      <div className="form-group">
        <label className="form-label" htmlFor="service_name">
          Service Name <span className="required">*</span>
        </label>
        <input
          id="service_name"
          type="text"
          className="form-input"
          placeholder="e.g. UserManagementService"
          value={service.service_name}
          onChange={e => update('service_name', e.target.value)}
          required
        />
      </div>

      <div className="form-group">
        <label className="form-label">Service Type</label>
        <div className="radio-group">
          {['SOAP', 'REST', 'BOTH'].map(type => (
            <label key={type} className="radio-label">
              <input
                type="radio"
                name="service_type"
                value={type}
                checked={service.service_type === type}
                onChange={() => update('service_type', type)}
              />
              <span className="radio-text">{type}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="namespace">Namespace</label>
        <input
          id="namespace"
          type="text"
          className="form-input"
          placeholder="http://example.com/service"
          value={service.namespace}
          onChange={e => update('namespace', e.target.value)}
        />
        <p className="form-hint">Used for SOAP services (e.g. http://example.com/service)</p>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="description">Description</label>
        <textarea
          id="description"
          className="form-textarea"
          placeholder="Describe what this service does..."
          value={service.description}
          onChange={e => update('description', e.target.value)}
          rows={4}
        />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="version">Version</label>
        <input
          id="version"
          type="text"
          className="form-input form-input-short"
          placeholder="1.0"
          value={service.version}
          onChange={e => update('version', e.target.value)}
        />
      </div>
    </div>
  )
}
