import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import App from '../App'
import axios from 'axios'

vi.mock('axios')

const mockFrameworksResponse = {
  data: {
    soap: [{ id: 'soap-java-spring-ws', label: 'Java (Spring-WS)' }],
    rest: [{ id: 'rest-python-fastapi', label: 'Python (FastAPI)' }]
  }
}

beforeEach(() => {
  // Provide a default resolved value for the frameworks fetch.
  // Individual tests can override this before rendering.
  axios.get.mockResolvedValue(mockFrameworksResponse)
  // Suppress jsdom URL API warnings from DownloadPanel
  vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:mock')
  vi.spyOn(window.URL, 'revokeObjectURL').mockReturnValue(undefined)
})

afterEach(() => {
  vi.restoreAllMocks()
})

// Helper: click Next n times
function clickNext(times = 1) {
  for (let i = 0; i < times; i++) {
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
  }
}

describe('App', () => {
  describe('initial render', () => {
    it('renders the page heading', async () => {
      render(<App />)
      expect(screen.getByText('Web Services Generator')).toBeInTheDocument()
    })

    it('renders the subtitle', async () => {
      render(<App />)
      expect(
        screen.getByText(/define your service and generate production-ready code/i)
      ).toBeInTheDocument()
    })

    it('renders step 1 (BasicInfo) by default', async () => {
      render(<App />)
      // BasicInfo renders a card with "Basic Service Information" heading
      expect(screen.getByText(/basic service information/i)).toBeInTheDocument()
    })

    it('renders the StepIndicator', async () => {
      render(<App />)
      // StepIndicator renders step labels
      expect(screen.getByText('Basic Info')).toBeInTheDocument()
      expect(screen.getByText('Methods')).toBeInTheDocument()
      expect(screen.getByText('Data Models')).toBeInTheDocument()
      expect(screen.getByText('Frameworks')).toBeInTheDocument()
      expect(screen.getByText('Download')).toBeInTheDocument()
    })

    it('renders the Next button on step 1', async () => {
      render(<App />)
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument()
    })

    it('Previous button is disabled on step 1', async () => {
      render(<App />)
      const prevButton = screen.getByRole('button', { name: /previous/i })
      expect(prevButton).toBeDisabled()
    })
  })

  describe('framework fetch on mount', () => {
    it('calls axios.get with /api/frameworks on mount', async () => {
      render(<App />)
      await waitFor(() =>
        expect(axios.get).toHaveBeenCalledWith('/api/frameworks')
      )
    })

    it('calls axios.get exactly once on mount', async () => {
      render(<App />)
      await waitFor(() => expect(axios.get).toHaveBeenCalledTimes(1))
    })

    it('handles framework fetch failure gracefully', async () => {
      axios.get.mockRejectedValueOnce(new Error('Network Error'))
      render(<App />)
      // Navigate to step 4 to see the error message from FrameworkSelector
      await waitFor(() => expect(axios.get).toHaveBeenCalledTimes(1))
      clickNext() // step 2
      clickNext() // step 3
      clickNext() // step 4
      expect(
        await screen.findByText(/failed to load frameworks/i)
      ).toBeInTheDocument()
    })
  })

  describe('step navigation', () => {
    it('clicking Next advances from step 1 to step 2 (MethodBuilder)', async () => {
      render(<App />)
      clickNext()
      expect(screen.getByText(/service methods/i)).toBeInTheDocument()
    })

    it('clicking Next twice shows step 3 (ModelBuilder)', async () => {
      render(<App />)
      clickNext(2)
      expect(screen.getByText(/data models/i)).toBeInTheDocument()
    })

    it('clicking Next three times shows step 4 (FrameworkSelector)', async () => {
      render(<App />)
      clickNext(3)
      expect(screen.getByText(/select frameworks/i)).toBeInTheDocument()
    })

    it('clicking Next four times shows step 5 (DownloadPanel)', async () => {
      render(<App />)
      clickNext(4)
      expect(screen.getByText(/generate & download/i)).toBeInTheDocument()
    })

    it('Next button is not rendered on step 5', async () => {
      render(<App />)
      clickNext(4)
      expect(screen.queryByRole('button', { name: /next/i })).not.toBeInTheDocument()
    })

    it('clicking Previous from step 2 goes back to step 1 (BasicInfo)', async () => {
      render(<App />)
      clickNext()
      // Now on step 2; click Previous
      fireEvent.click(screen.getByRole('button', { name: /previous/i }))
      expect(screen.getByText(/basic service information/i)).toBeInTheDocument()
    })

    it('clicking Previous from step 3 goes back to step 2 (MethodBuilder)', async () => {
      render(<App />)
      clickNext(2)
      fireEvent.click(screen.getByRole('button', { name: /previous/i }))
      expect(screen.getByText(/service methods/i)).toBeInTheDocument()
    })

    it('Previous button is enabled on step 2', async () => {
      render(<App />)
      clickNext()
      expect(screen.getByRole('button', { name: /previous/i })).not.toBeDisabled()
    })

    it('Previous button is enabled on step 5', async () => {
      render(<App />)
      clickNext(4)
      expect(screen.getByRole('button', { name: /previous/i })).not.toBeDisabled()
    })
  })

  describe('step indicator updates with navigation', () => {
    it('step 1 has "active" class when on step 1', async () => {
      const { container } = render(<App />)
      const stepItems = container.querySelectorAll('.step-item')
      expect(stepItems[0]).toHaveClass('active')
    })

    it('step 2 has "active" class after clicking Next once', async () => {
      const { container } = render(<App />)
      clickNext()
      const stepItems = container.querySelectorAll('.step-item')
      expect(stepItems[1]).toHaveClass('active')
    })

    it('step 1 has "completed" class after advancing to step 2', async () => {
      const { container } = render(<App />)
      clickNext()
      const stepItems = container.querySelectorAll('.step-item')
      expect(stepItems[0]).toHaveClass('completed')
    })

    it('step 5 has "active" class after clicking Next four times', async () => {
      const { container } = render(<App />)
      clickNext(4)
      const stepItems = container.querySelectorAll('.step-item')
      expect(stepItems[4]).toHaveClass('active')
    })
  })

  describe('service state persistence across steps', () => {
    it('service name typed in step 1 is reflected when returning to step 1', async () => {
      render(<App />)
      // Type a service name on step 1
      fireEvent.change(screen.getByLabelText(/service name/i), {
        target: { value: 'PersistedService' }
      })
      // Go to step 2 and back
      clickNext()
      fireEvent.click(screen.getByRole('button', { name: /previous/i }))
      expect(screen.getByLabelText(/service name/i)).toHaveValue('PersistedService')
    })

    it('method added in step 2 persists when navigating away and back', async () => {
      render(<App />)
      clickNext() // go to step 2
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      clickNext() // go to step 3
      fireEvent.click(screen.getByRole('button', { name: /previous/i })) // back to step 2
      expect(screen.getByText(/method 1/i)).toBeInTheDocument()
    })
  })

  describe('FrameworkSelector receives loaded frameworks', () => {
    it('shows REST framework label on step 4 after fetch resolves', async () => {
      render(<App />)
      await waitFor(() => expect(axios.get).toHaveBeenCalledTimes(1))
      clickNext(3) // advance to step 4
      expect(await screen.findByText('Python (FastAPI)')).toBeInTheDocument()
    })
  })
})
