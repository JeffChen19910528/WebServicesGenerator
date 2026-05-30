import { screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import BasicInfo from '../components/BasicInfo'
import { renderWithLang } from './testUtils'

const initialService = {
  service_name: '',
  service_type: 'REST',
  namespace: 'http://example.com/service',
  description: '',
  version: '1.0',
  methods: [],
  models: []
}

describe('BasicInfo', () => {
  let mockSetService

  beforeEach(() => {
    mockSetService = vi.fn()
  })

  it('renders service name input', () => {
    renderWithLang(<BasicInfo service={initialService} setService={mockSetService} />)
    const input = screen.getByLabelText(/service name/i)
    expect(input).toBeInTheDocument()
    expect(input).toHaveAttribute('type', 'text')
  })

  it('renders service type radio buttons for SOAP, REST, and BOTH', () => {
    renderWithLang(<BasicInfo service={initialService} setService={mockSetService} />)
    const soapRadio = screen.getByRole('radio', { name: /soap/i })
    const restRadio = screen.getByRole('radio', { name: /rest/i })
    const bothRadio = screen.getByRole('radio', { name: /both/i })
    expect(soapRadio).toBeInTheDocument()
    expect(restRadio).toBeInTheDocument()
    expect(bothRadio).toBeInTheDocument()
  })

  it('REST radio is checked by default when service_type is REST', () => {
    renderWithLang(<BasicInfo service={initialService} setService={mockSetService} />)
    expect(screen.getByRole('radio', { name: /rest/i })).toBeChecked()
    expect(screen.getByRole('radio', { name: /soap/i })).not.toBeChecked()
    expect(screen.getByRole('radio', { name: /both/i })).not.toBeChecked()
  })

  it('renders namespace input with the default value', () => {
    renderWithLang(<BasicInfo service={initialService} setService={mockSetService} />)
    const namespaceInput = screen.getByLabelText(/namespace/i)
    expect(namespaceInput).toBeInTheDocument()
    expect(namespaceInput).toHaveValue('http://example.com/service')
  })

  it('calls setService with updated service_name when text is typed', () => {
    renderWithLang(<BasicInfo service={initialService} setService={mockSetService} />)
    const nameInput = screen.getByLabelText(/service name/i)
    fireEvent.change(nameInput, { target: { value: 'MyNewService' } })
    expect(mockSetService).toHaveBeenCalledTimes(1)
    const updater = mockSetService.mock.calls[0][0]
    const result = updater(initialService)
    expect(result.service_name).toBe('MyNewService')
  })

  it('calls setService with service_type SOAP when SOAP radio is clicked', () => {
    renderWithLang(<BasicInfo service={initialService} setService={mockSetService} />)
    fireEvent.click(screen.getByRole('radio', { name: /soap/i }))
    expect(mockSetService).toHaveBeenCalledTimes(1)
    const updater = mockSetService.mock.calls[0][0]
    const result = updater(initialService)
    expect(result.service_type).toBe('SOAP')
  })

  it('calls setService with service_type BOTH when BOTH radio is clicked', () => {
    renderWithLang(<BasicInfo service={initialService} setService={mockSetService} />)
    fireEvent.click(screen.getByRole('radio', { name: /both/i }))
    expect(mockSetService).toHaveBeenCalledTimes(1)
    const updater = mockSetService.mock.calls[0][0]
    const result = updater(initialService)
    expect(result.service_type).toBe('BOTH')
  })

  it('renders description textarea', () => {
    renderWithLang(<BasicInfo service={initialService} setService={mockSetService} />)
    const textarea = screen.getByLabelText(/description/i)
    expect(textarea).toBeInTheDocument()
    expect(textarea.tagName).toBe('TEXTAREA')
  })

  it('calls setService with updated description when textarea is changed', () => {
    renderWithLang(<BasicInfo service={initialService} setService={mockSetService} />)
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: 'A great service' }
    })
    const updater = mockSetService.mock.calls[0][0]
    const result = updater(initialService)
    expect(result.description).toBe('A great service')
  })

  it('renders version input with default value of 1.0', () => {
    renderWithLang(<BasicInfo service={initialService} setService={mockSetService} />)
    const versionInput = screen.getByLabelText(/version/i)
    expect(versionInput).toBeInTheDocument()
    expect(versionInput).toHaveValue('1.0')
  })

  it('calls setService with updated version when version input is changed', () => {
    renderWithLang(<BasicInfo service={initialService} setService={mockSetService} />)
    fireEvent.change(screen.getByLabelText(/version/i), { target: { value: '2.0' } })
    const updater = mockSetService.mock.calls[0][0]
    const result = updater(initialService)
    expect(result.version).toBe('2.0')
  })

  it('calls setService with updated namespace when namespace input is changed', () => {
    renderWithLang(<BasicInfo service={initialService} setService={mockSetService} />)
    fireEvent.change(screen.getByLabelText(/namespace/i), {
      target: { value: 'http://my.company.com/api' }
    })
    const updater = mockSetService.mock.calls[0][0]
    const result = updater(initialService)
    expect(result.namespace).toBe('http://my.company.com/api')
  })

  it('reflects the current service_name value in the input', () => {
    const serviceWithName = { ...initialService, service_name: 'ExistingService' }
    renderWithLang(<BasicInfo service={serviceWithName} setService={mockSetService} />)
    expect(screen.getByLabelText(/service name/i)).toHaveValue('ExistingService')
  })
})
