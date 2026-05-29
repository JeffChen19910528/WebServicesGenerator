import React from 'react'

const PRIMITIVE_TYPES = ['string', 'int', 'float', 'boolean', 'date', 'datetime']

const blankField = () => ({
  name: '',
  type: 'string',
  required: false
})

const blankModel = () => ({
  name: '',
  fields: []
})

export default function ModelBuilder({ service, setService }) {
  const addModel = () => {
    setService(prev => ({
      ...prev,
      models: [...prev.models, blankModel()]
    }))
  }

  const removeModel = (index) => {
    setService(prev => ({
      ...prev,
      models: prev.models.filter((_, i) => i !== index)
    }))
  }

  const updateModel = (index, field, value) => {
    setService(prev => {
      const models = prev.models.map((m, i) =>
        i === index ? { ...m, [field]: value } : m
      )
      return { ...prev, models }
    })
  }

  const addField = (modelIndex) => {
    setService(prev => {
      const models = prev.models.map((m, i) => {
        if (i !== modelIndex) return m
        return { ...m, fields: [...m.fields, blankField()] }
      })
      return { ...prev, models }
    })
  }

  const removeField = (modelIndex, fieldIndex) => {
    setService(prev => {
      const models = prev.models.map((m, i) => {
        if (i !== modelIndex) return m
        return { ...m, fields: m.fields.filter((_, j) => j !== fieldIndex) }
      })
      return { ...prev, models }
    })
  }

  const updateField = (modelIndex, fieldIndex, field, value) => {
    setService(prev => {
      const models = prev.models.map((m, i) => {
        if (i !== modelIndex) return m
        const fields = m.fields.map((f, j) =>
          j === fieldIndex ? { ...f, [field]: value } : f
        )
        return { ...m, fields }
      })
      return { ...prev, models }
    })
  }

  return (
    <div>
      <div className="section-header">
        <div>
          <h2 className="section-title">Data Models</h2>
          <p className="section-description">Define reusable data structures used by your service methods.</p>
        </div>
        <button className="btn btn-primary" onClick={addModel}>
          + Add Model
        </button>
      </div>

      {service.models.length === 0 && (
        <div className="empty-state">
          <p>No data models defined. Models are optional — add them if your methods use complex types.</p>
        </div>
      )}

      {service.models.map((model, modelIndex) => (
        <div key={modelIndex} className="card method-card">
          <div className="card-header">
            <h3 className="card-subtitle">Model {modelIndex + 1}</h3>
            <button
              className="btn btn-danger btn-sm"
              onClick={() => removeModel(modelIndex)}
            >
              Remove Model
            </button>
          </div>

          <div className="form-group">
            <label className="form-label">Model Name</label>
            <input
              type="text"
              className="form-input form-input-medium"
              placeholder="e.g. User"
              value={model.name}
              onChange={e => updateModel(modelIndex, 'name', e.target.value)}
            />
          </div>

          <div className="params-section">
            <div className="params-header">
              <h4 className="params-title">Fields</h4>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => addField(modelIndex)}
              >
                + Add Field
              </button>
            </div>

            {model.fields.length === 0 && (
              <p className="empty-params">No fields defined for this model.</p>
            )}

            {model.fields.map((field, fieldIndex) => (
              <div key={fieldIndex} className="param-row">
                <div className="param-fields">
                  <div className="form-group">
                    <label className="form-label form-label-sm">Field Name</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="fieldName"
                      value={field.name}
                      onChange={e => updateField(modelIndex, fieldIndex, 'name', e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label form-label-sm">Type</label>
                    <select
                      className="form-select"
                      value={field.type}
                      onChange={e => updateField(modelIndex, fieldIndex, 'type', e.target.value)}
                    >
                      {PRIMITIVE_TYPES.map(t => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group form-group-checkbox">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={field.required}
                        onChange={e => updateField(modelIndex, fieldIndex, 'required', e.target.checked)}
                      />
                      <span>Required</span>
                    </label>
                  </div>
                </div>

                <button
                  className="btn btn-danger btn-sm btn-icon"
                  onClick={() => removeField(modelIndex, fieldIndex)}
                  title="Remove field"
                >
                  &times;
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
