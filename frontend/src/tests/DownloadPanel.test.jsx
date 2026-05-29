import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import DownloadPanel from '../components/DownloadPanel'
import axios from 'axios'

vi.mock('axios')

// Suppress jsdom's "Not implemented: window.URL.createObjectURL" noise
beforeEach(() => {
  vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:mock-url')
  vi.spyOn(window.URL, 'revokeObjectURL').mockReturnValue(undefined)
})

afterEach(() => {
  vi.restoreAllMocks()
})

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

const baseService = {
  service_name: 'MyService',
  service_type: 'REST',
  namespace: 'http://example.com/service',
  description: '',
  version: '1.0',
  methods: [],
  models: []
}

const defaultProps = {
  service: baseService,
  selectedFrameworks: [],
  frameworks: mockFrameworks
}

describe('DownloadPanel', () => {
  describe('framework download buttons', () => {
    it('renders no download buttons when no frameworks are selected', () => {
      render(<DownloadPanel {...defaultProps} selectedFrameworks={[]} />)
      // The only download button present should be the "Download Tests ZIP" button
      const downloadButtons = screen.getAllByRole('button')
      const frameworkButtons = downloadButtons.filter(btn =>
        btn.textContent.includes('Download') &&
        !btn.textContent.includes('Tests')
      )
      expect(frameworkButtons).toHaveLength(0)
    })

    it('shows a warning when no frameworks are selected', () => {
      render(<DownloadPanel {...defaultProps} selectedFrameworks={[]} />)
      expect(screen.getByText(/no frameworks selected/i)).toBeInTheDocument()
    })

    it('renders a download button for each selected framework', () => {
      render(
        <DownloadPanel
          {...defaultProps}
          selectedFrameworks={['rest-python-fastapi', 'rest-nodejs-express']}
        />
      )
      expect(screen.getByText(/download python \(fastapi\)/i)).toBeInTheDocument()
      expect(screen.getByText(/download node\.js \(express\)/i)).toBeInTheDocument()
    })

    it('renders download button for a single selected framework', () => {
      render(
        <DownloadPanel
          {...defaultProps}
          selectedFrameworks={['rest-python-fastapi']}
        />
      )
      expect(screen.getByText(/download python \(fastapi\)/i)).toBeInTheDocument()
    })

    it('uses the framework id as the button label when label is not found', () => {
      render(
        <DownloadPanel
          {...defaultProps}
          selectedFrameworks={['unknown-framework']}
          frameworks={{ soap: [], rest: [] }}
        />
      )
      expect(screen.getByText(/download unknown-framework/i)).toBeInTheDocument()
    })
  })

  describe('test type checkboxes', () => {
    it('Postman Collection checkbox is always visible regardless of service_type', () => {
      render(<DownloadPanel {...defaultProps} service={{ ...baseService, service_type: 'REST' }} />)
      expect(screen.getByText('Postman Collection')).toBeInTheDocument()
    })

    it('Postman Collection checkbox is visible for SOAP service_type too', () => {
      render(<DownloadPanel {...defaultProps} service={{ ...baseService, service_type: 'SOAP' }} />)
      expect(screen.getByText('Postman Collection')).toBeInTheDocument()
    })

    it('shows SOAP XML Envelopes checkbox when service_type is SOAP', () => {
      render(
        <DownloadPanel {...defaultProps} service={{ ...baseService, service_type: 'SOAP' }} />
      )
      expect(screen.getByText('SOAP XML Envelopes')).toBeInTheDocument()
    })

    it('shows SoapUI Project checkbox when service_type is SOAP', () => {
      render(
        <DownloadPanel {...defaultProps} service={{ ...baseService, service_type: 'SOAP' }} />
      )
      expect(screen.getByText('SoapUI Project')).toBeInTheDocument()
    })

    it('shows SOAP XML Envelopes checkbox when service_type is BOTH', () => {
      render(
        <DownloadPanel {...defaultProps} service={{ ...baseService, service_type: 'BOTH' }} />
      )
      expect(screen.getByText('SOAP XML Envelopes')).toBeInTheDocument()
    })

    it('hides SOAP XML Envelopes checkbox for REST-only service', () => {
      render(
        <DownloadPanel {...defaultProps} service={{ ...baseService, service_type: 'REST' }} />
      )
      expect(screen.queryByText('SOAP XML Envelopes')).not.toBeInTheDocument()
    })

    it('hides SoapUI Project checkbox for REST-only service', () => {
      render(
        <DownloadPanel {...defaultProps} service={{ ...baseService, service_type: 'REST' }} />
      )
      expect(screen.queryByText('SoapUI Project')).not.toBeInTheDocument()
    })

    it('Postman Collection checkbox is pre-checked by default', () => {
      render(<DownloadPanel {...defaultProps} />)
      const postmanLabel = screen.getByText('Postman Collection').closest('label')
      const checkbox = postmanLabel.querySelector('input[type="checkbox"]')
      expect(checkbox).toBeChecked()
    })
  })

  describe('framework download API call', () => {
    beforeEach(() => {
      axios.post.mockResolvedValue({
        data: new Blob(['fake zip content'], { type: 'application/zip' }),
        headers: { 'content-type': 'application/zip' }
      })
    })

    it('calls axios.post with /api/generate on framework download button click', async () => {
      render(
        <DownloadPanel
          {...defaultProps}
          selectedFrameworks={['rest-python-fastapi']}
        />
      )
      fireEvent.click(screen.getByText(/download python \(fastapi\)/i))
      await waitFor(() => expect(axios.post).toHaveBeenCalledTimes(1))
      expect(axios.post).toHaveBeenCalledWith(
        '/api/generate',
        expect.objectContaining({ framework: 'rest-python-fastapi' }),
        expect.objectContaining({ responseType: 'blob' })
      )
    })

    it('includes the full service object in the POST body', async () => {
      render(
        <DownloadPanel
          {...defaultProps}
          selectedFrameworks={['rest-python-fastapi']}
        />
      )
      fireEvent.click(screen.getByText(/download python \(fastapi\)/i))
      await waitFor(() => expect(axios.post).toHaveBeenCalledTimes(1))
      expect(axios.post).toHaveBeenCalledWith(
        '/api/generate',
        expect.objectContaining({ service: baseService }),
        expect.anything()
      )
    })

    it('shows loading text while the download request is in flight', async () => {
      // Keep the promise pending so we can observe the loading state
      let resolvePost
      axios.post.mockReturnValue(new Promise(resolve => { resolvePost = resolve }))

      render(
        <DownloadPanel
          {...defaultProps}
          selectedFrameworks={['rest-python-fastapi']}
        />
      )
      fireEvent.click(screen.getByText(/download python \(fastapi\)/i))
      expect(await screen.findByText(/generating\.\.\./i)).toBeInTheDocument()

      // Clean up by resolving
      resolvePost({
        data: new Blob(['x'], { type: 'application/zip' }),
        headers: { 'content-type': 'application/zip' }
      })
    })

    it('button is disabled while the download is in progress', async () => {
      let resolvePost
      axios.post.mockReturnValue(new Promise(resolve => { resolvePost = resolve }))

      render(
        <DownloadPanel
          {...defaultProps}
          selectedFrameworks={['rest-python-fastapi']}
        />
      )

      const btn = screen.getByText(/download python \(fastapi\)/i).closest('button')
      fireEvent.click(btn)

      await waitFor(() =>
        expect(screen.getByText(/generating\.\.\./i).closest('button')).toBeDisabled()
      )

      resolvePost({
        data: new Blob(['x'], { type: 'application/zip' }),
        headers: {}
      })
    })
  })

  describe('framework download error handling', () => {
    it('shows a network error message when axios.post rejects without a response', async () => {
      axios.post.mockRejectedValue(new Error('Network Error'))

      render(
        <DownloadPanel
          {...defaultProps}
          selectedFrameworks={['rest-python-fastapi']}
        />
      )
      fireEvent.click(screen.getByText(/download python \(fastapi\)/i))

      expect(await screen.findByText(/network error/i)).toBeInTheDocument()
    })

    it('shows a server error message when axios.post rejects with a response status', async () => {
      const axiosError = new Error('Request failed with status code 500')
      axiosError.response = { status: 500 }
      axios.post.mockRejectedValue(axiosError)

      render(
        <DownloadPanel
          {...defaultProps}
          selectedFrameworks={['rest-python-fastapi']}
        />
      )
      fireEvent.click(screen.getByText(/download python \(fastapi\)/i))

      expect(await screen.findByText(/server error: 500/i)).toBeInTheDocument()
    })

    it('restores the download button after a failed request', async () => {
      axios.post.mockRejectedValue(new Error('Network Error'))

      render(
        <DownloadPanel
          {...defaultProps}
          selectedFrameworks={['rest-python-fastapi']}
        />
      )
      fireEvent.click(screen.getByText(/download python \(fastapi\)/i))

      await waitFor(() =>
        expect(screen.getByText(/download python \(fastapi\)/i)).toBeInTheDocument()
      )
    })
  })

  describe('tests download', () => {
    beforeEach(() => {
      axios.post.mockResolvedValue({
        data: new Blob(['fake test zip'], { type: 'application/zip' }),
        headers: { 'content-type': 'application/zip' }
      })
    })

    it('renders the Download Tests ZIP button', () => {
      render(<DownloadPanel {...defaultProps} />)
      expect(screen.getByText(/download tests zip/i)).toBeInTheDocument()
    })

    it('clicking Download Tests ZIP calls axios.post with /api/generate-tests', async () => {
      render(<DownloadPanel {...defaultProps} />)
      fireEvent.click(screen.getByText(/download tests zip/i))
      await waitFor(() => expect(axios.post).toHaveBeenCalledTimes(1))
      expect(axios.post).toHaveBeenCalledWith(
        '/api/generate-tests',
        expect.objectContaining({ service: baseService }),
        expect.objectContaining({ responseType: 'blob' })
      )
    })

    it('sends selected test types in the POST body', async () => {
      render(<DownloadPanel {...defaultProps} />)
      // Default selection is ['postman']
      fireEvent.click(screen.getByText(/download tests zip/i))
      await waitFor(() => expect(axios.post).toHaveBeenCalledTimes(1))
      expect(axios.post).toHaveBeenCalledWith(
        '/api/generate-tests',
        expect.objectContaining({ test_types: expect.arrayContaining(['postman']) }),
        expect.anything()
      )
    })

    it('shows loading text while tests download is in flight', async () => {
      let resolvePost
      axios.post.mockReturnValue(new Promise(resolve => { resolvePost = resolve }))

      render(<DownloadPanel {...defaultProps} />)
      fireEvent.click(screen.getByText(/download tests zip/i))

      expect(await screen.findByText(/generating tests/i)).toBeInTheDocument()

      resolvePost({
        data: new Blob(['x'], { type: 'application/zip' }),
        headers: {}
      })
    })

    it('shows success message after tests download completes', async () => {
      render(<DownloadPanel {...defaultProps} />)
      fireEvent.click(screen.getByText(/download tests zip/i))
      expect(await screen.findByText(/tests downloaded successfully/i)).toBeInTheDocument()
    })

    it('shows error message when tests download fails', async () => {
      axios.post.mockRejectedValue(new Error('Network Error'))
      render(<DownloadPanel {...defaultProps} />)
      fireEvent.click(screen.getByText(/download tests zip/i))
      expect(await screen.findByText(/network error/i)).toBeInTheDocument()
    })

    it('Download Tests ZIP button is disabled when no test types are selected', () => {
      render(<DownloadPanel {...defaultProps} />)
      // Uncheck the default Postman Collection checkbox
      const postmanLabel = screen.getByText('Postman Collection').closest('label')
      fireEvent.click(postmanLabel.querySelector('input[type="checkbox"]'))
      const testsBtn = screen.getByText(/download tests zip/i).closest('button')
      expect(testsBtn).toBeDisabled()
    })
  })

  describe('service summary', () => {
    it('displays the service name in the summary', () => {
      render(<DownloadPanel {...defaultProps} />)
      expect(screen.getByText('MyService')).toBeInTheDocument()
    })

    it('displays the service type in the summary', () => {
      render(<DownloadPanel {...defaultProps} />)
      expect(screen.getByText('REST')).toBeInTheDocument()
    })

    it('displays "None selected" when no frameworks are selected', () => {
      render(<DownloadPanel {...defaultProps} selectedFrameworks={[]} />)
      expect(screen.getByText(/none selected/i)).toBeInTheDocument()
    })

    it('displays the selected framework ids in the summary', () => {
      render(
        <DownloadPanel
          {...defaultProps}
          selectedFrameworks={['rest-python-fastapi']}
        />
      )
      // Summary section shows the selected frameworks joined by comma
      expect(screen.getAllByText(/rest-python-fastapi/).length).toBeGreaterThan(0)
    })
  })
})
