import React from 'react'
import { useLanguage } from '../i18n/LanguageContext.jsx'

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
  const { t } = useLanguage()

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
          <h2 className="section-title">{t('modelsTitle')}</h2>
          <p className="section-description">{t('modelsDesc')}</p>
        </div>
        <button className="btn btn-primary" onClick={addModel}>
          {t('addModel')}
        </button>
      </div>

      {service.models.length === 0 && (
        <div className="empty-state">
          <p>{t('noModels')}</p>
        </div>
      )}

      {service.models.map((model, modelIndex) => (
        <div key={modelIndex} className="card method-card">
          <div className="card-header">
            <h3 className="card-subtitle">{t('model')} {modelIndex + 1}</h3>
            <button
              className="btn btn-danger btn-sm"
              onClick={() => removeModel(modelIndex)}
            >
              {t('removeModel')}
            </button>
          </div>

          <div className="form-group">
            <label className="form-label">{t('modelName')}</label>
            <input
              type="text"
              className="form-input form-input-medium"
              placeholder={t('modelNamePlaceholder')}
              value={model.name}
              onChange={e => updateModel(modelIndex, 'name', e.target.value)}
            />
          </div>

          <div className="params-section">
            <div className="params-header">
              <h4 className="params-title">{t('fields')}</h4>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => addField(modelIndex)}
              >
                {t('addField')}
              </button>
            </div>

            {model.fields.length === 0 && (
              <p className="empty-params">{t('noFields')}</p>
            )}

            {model.fields.map((field, fieldIndex) => (
              <div key={fieldIndex} className="param-row">
                <div className="param-fields">
                  <div className="form-group">
                    <label className="form-label form-label-sm">{t('fieldName')}</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder={t('fieldNamePlaceholder')}
                      value={field.name}
                      onChange={e => updateField(modelIndex, fieldIndex, 'name', e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label form-label-sm">{t('fieldType')}</label>
                    <select
                      className="form-select"
                      value={field.type}
                      onChange={e => updateField(modelIndex, fieldIndex, 'type', e.target.value)}
                    >
                      {PRIMITIVE_TYPES.map(type => (
                        <option key={type} value={type}>{type}</option>
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
                      <span>{t('fieldRequired')}</span>
                    </label>
                  </div>
                </div>

                <button
                  className="btn btn-danger btn-sm btn-icon"
                  onClick={() => removeField(modelIndex, fieldIndex)}
                  title={t('removeField')}
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
