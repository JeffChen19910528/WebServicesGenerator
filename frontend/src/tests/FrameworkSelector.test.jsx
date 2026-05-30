import { screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import FrameworkSelector from '../components/FrameworkSelector'
import { renderWithLang } from './testUtils'

const mockFrameworks = {
  soap: [
    { id: 'soap-java-spring-ws', label: 'Java (Spring-WS)' },
    { id: 'soap-python-spyne', label: 'Python (spyne)' }
  ],
  rest: [
    { id: 'rest-python-fastapi', label: 'Python (FastAPI)' },
    { id: 'rest-nodejs-express', label: 'Node.js (Express)' }
  ]
}

const defaultProps = {
  frameworks: mockFrameworks,
  selected: [],
  onChange: vi.fn(),
  service: { service_type: 'REST' },
  error: null
}

describe('FrameworkSelector', () => {
  let mockOnChange

  beforeEach(() => {
    mockOnChange = vi.fn()
  })

  describe('section visibility by service_type', () => {
    it('shows REST frameworks when service_type is REST', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'REST' }}
        />
      )
      expect(screen.getByText('Python (FastAPI)')).toBeInTheDocument()
      expect(screen.getByText('Node.js (Express)')).toBeInTheDocument()
    })

    it('hides SOAP frameworks when service_type is REST', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'REST' }}
        />
      )
      expect(screen.queryByText('Java (Spring-WS)')).not.toBeInTheDocument()
      expect(screen.queryByText('Python (spyne)')).not.toBeInTheDocument()
    })

    it('shows SOAP frameworks when service_type is SOAP', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'SOAP' }}
        />
      )
      expect(screen.getByText('Java (Spring-WS)')).toBeInTheDocument()
      expect(screen.getByText('Python (spyne)')).toBeInTheDocument()
    })

    it('hides REST frameworks when service_type is SOAP', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'SOAP' }}
        />
      )
      expect(screen.queryByText('Python (FastAPI)')).not.toBeInTheDocument()
      expect(screen.queryByText('Node.js (Express)')).not.toBeInTheDocument()
    })

    it('shows both SOAP and REST sections when service_type is BOTH', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'BOTH' }}
        />
      )
      expect(screen.getByText('Java (Spring-WS)')).toBeInTheDocument()
      expect(screen.getByText('Python (spyne)')).toBeInTheDocument()
      expect(screen.getByText('Python (FastAPI)')).toBeInTheDocument()
      expect(screen.getByText('Node.js (Express)')).toBeInTheDocument()
    })

    it('renders "SOAP Frameworks" group title when SOAP is visible', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'SOAP' }}
        />
      )
      expect(screen.getByText('SOAP Frameworks')).toBeInTheDocument()
    })

    it('renders "REST Frameworks" group title when REST is visible', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'REST' }}
        />
      )
      expect(screen.getByText('REST Frameworks')).toBeInTheDocument()
    })
  })

  describe('checkbox state', () => {
    it('selected framework checkbox is checked', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'REST' }}
          selected={['rest-python-fastapi']}
        />
      )
      const fastapiLabel = screen.getByText('Python (FastAPI)').closest('label')
      const checkbox = fastapiLabel.querySelector('input[type="checkbox"]')
      expect(checkbox).toBeChecked()
    })

    it('unselected framework checkbox is not checked', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'REST' }}
          selected={['rest-python-fastapi']}
        />
      )
      const expressLabel = screen.getByText('Node.js (Express)').closest('label')
      const checkbox = expressLabel.querySelector('input[type="checkbox"]')
      expect(checkbox).not.toBeChecked()
    })

    it('all checkboxes unchecked when selected is empty', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'REST' }}
          selected={[]}
        />
      )
      const checkboxes = screen.getAllByRole('checkbox')
      checkboxes.forEach(cb => expect(cb).not.toBeChecked())
    })
  })

  describe('onChange interactions', () => {
    it('clicking an unchecked checkbox calls onChange with the framework id added', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'REST' }}
          selected={[]}
        />
      )
      const fastapiLabel = screen.getByText('Python (FastAPI)').closest('label')
      const checkbox = fastapiLabel.querySelector('input[type="checkbox"]')
      fireEvent.click(checkbox)
      expect(mockOnChange).toHaveBeenCalledTimes(1)
      expect(mockOnChange).toHaveBeenCalledWith(['rest-python-fastapi'])
    })

    it('clicking a checked checkbox calls onChange with the framework id removed', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'REST' }}
          selected={['rest-python-fastapi']}
        />
      )
      const fastapiLabel = screen.getByText('Python (FastAPI)').closest('label')
      const checkbox = fastapiLabel.querySelector('input[type="checkbox"]')
      fireEvent.click(checkbox)
      expect(mockOnChange).toHaveBeenCalledTimes(1)
      expect(mockOnChange).toHaveBeenCalledWith([])
    })

    it('clicking a second framework adds it to the existing selection', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'REST' }}
          selected={['rest-python-fastapi']}
        />
      )
      const expressLabel = screen.getByText('Node.js (Express)').closest('label')
      const checkbox = expressLabel.querySelector('input[type="checkbox"]')
      fireEvent.click(checkbox)
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.arrayContaining(['rest-python-fastapi', 'rest-nodejs-express'])
      )
    })
  })

  describe('selected summary', () => {
    it('shows a summary of selected frameworks when at least one is selected', () => {
      const { container } = renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'REST' }}
          selected={['rest-python-fastapi']}
        />
      )
      const summary = container.querySelector('.selected-summary')
      expect(summary).toBeInTheDocument()
      expect(summary.textContent).toContain('rest-python-fastapi')
    })

    it('does not show selected summary when nothing is selected', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          service={{ service_type: 'REST' }}
          selected={[]}
        />
      )
      expect(screen.queryByText(/selected:/i)).not.toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('shows error alert when error prop is provided', () => {
      renderWithLang(
        <FrameworkSelector
          {...defaultProps}
          onChange={mockOnChange}
          error="Failed to load frameworks from server."
        />
      )
      expect(screen.getByText(/failed to load frameworks/i)).toBeInTheDocument()
    })

    it('shows loading message when no error and no frameworks loaded', () => {
      renderWithLang(
        <FrameworkSelector
          frameworks={{ soap: [], rest: [] }}
          selected={[]}
          onChange={mockOnChange}
          service={{ service_type: 'REST' }}
          error={null}
        />
      )
      expect(screen.getByText(/loading available frameworks/i)).toBeInTheDocument()
    })
  })
})
