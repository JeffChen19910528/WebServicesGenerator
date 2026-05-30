import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import React from 'react'
import { LanguageProvider, useLanguage } from '../i18n/LanguageContext.jsx'
import translations from '../i18n/translations.js'

// Helper component to expose context values for testing
function LanguageConsumer() {
  const { lang, setLang, t } = useLanguage()
  return (
    <div>
      <span data-testid="lang">{lang}</span>
      <span data-testid="title">{t('appTitle')}</span>
      <span data-testid="stepLabel0">{t('stepLabels')[0]}</span>
      <button onClick={() => setLang('zh-TW')}>zh-TW</button>
      <button onClick={() => setLang('en')}>en</button>
    </div>
  )
}

describe('translations', () => {
  it('has identical keys for en and zh-TW', () => {
    const enKeys = Object.keys(translations.en).sort()
    const zhKeys = Object.keys(translations['zh-TW']).sort()
    expect(enKeys).toEqual(zhKeys)
  })

  it('en translations are non-empty strings or arrays', () => {
    for (const [key, val] of Object.entries(translations.en)) {
      expect(val, `key "${key}" should not be empty`).toBeTruthy()
    }
  })

  it('zh-TW translations are non-empty strings or arrays', () => {
    for (const [key, val] of Object.entries(translations['zh-TW'])) {
      expect(val, `key "${key}" should not be empty`).toBeTruthy()
    }
  })

  it('stepLabels has 5 items in both locales', () => {
    expect(translations.en.stepLabels).toHaveLength(5)
    expect(translations['zh-TW'].stepLabels).toHaveLength(5)
  })
})

describe('LanguageProvider', () => {
  it('provides default language "en"', () => {
    render(
      <LanguageProvider>
        <LanguageConsumer />
      </LanguageProvider>
    )
    expect(screen.getByTestId('lang').textContent).toBe('en')
  })

  it('t() returns English text by default', () => {
    render(
      <LanguageProvider>
        <LanguageConsumer />
      </LanguageProvider>
    )
    expect(screen.getByTestId('title').textContent).toBe('Web Services Generator')
  })

  it('t() returns array for stepLabels in English', () => {
    render(
      <LanguageProvider>
        <LanguageConsumer />
      </LanguageProvider>
    )
    expect(screen.getByTestId('stepLabel0').textContent).toBe('Basic Info')
  })

  it('switching to zh-TW changes lang', () => {
    render(
      <LanguageProvider>
        <LanguageConsumer />
      </LanguageProvider>
    )
    fireEvent.click(screen.getByRole('button', { name: 'zh-TW' }))
    expect(screen.getByTestId('lang').textContent).toBe('zh-TW')
  })

  it('switching to zh-TW changes appTitle translation', () => {
    render(
      <LanguageProvider>
        <LanguageConsumer />
      </LanguageProvider>
    )
    fireEvent.click(screen.getByRole('button', { name: 'zh-TW' }))
    expect(screen.getByTestId('title').textContent).toBe('Web Services 產生器')
  })

  it('switching to zh-TW changes stepLabel', () => {
    render(
      <LanguageProvider>
        <LanguageConsumer />
      </LanguageProvider>
    )
    fireEvent.click(screen.getByRole('button', { name: 'zh-TW' }))
    expect(screen.getByTestId('stepLabel0').textContent).toBe('基本資訊')
  })

  it('switching back to en restores English text', () => {
    render(
      <LanguageProvider>
        <LanguageConsumer />
      </LanguageProvider>
    )
    fireEvent.click(screen.getByRole('button', { name: 'zh-TW' }))
    fireEvent.click(screen.getByRole('button', { name: 'en' }))
    expect(screen.getByTestId('title').textContent).toBe('Web Services Generator')
  })

  it('t() returns key as fallback for unknown keys', () => {
    function FallbackConsumer() {
      const { t } = useLanguage()
      return <span data-testid="fallback">{t('nonExistentKey')}</span>
    }
    render(
      <LanguageProvider>
        <FallbackConsumer />
      </LanguageProvider>
    )
    expect(screen.getByTestId('fallback').textContent).toBe('nonExistentKey')
  })

  it('throws when useLanguage is used outside LanguageProvider', () => {
    const original = console.error
    console.error = () => {}
    expect(() => render(<LanguageConsumer />)).toThrow()
    console.error = original
  })
})

describe('language switcher in App header', () => {
  it('EN button is rendered', async () => {
    const { default: App } = await import('../App.jsx')
    const axios = (await import('axios')).default
    const { vi } = await import('vitest')
    vi.spyOn(axios, 'get').mockResolvedValue({ data: { soap: [], rest: [] } })

    render(<App />)
    expect(screen.getByRole('button', { name: /switch to english/i })).toBeInTheDocument()
  })

  it('繁中 button is rendered', async () => {
    const { default: App } = await import('../App.jsx')
    render(<App />)
    expect(screen.getByRole('button', { name: /切換為繁體中文/i })).toBeInTheDocument()
  })

  it('clicking 繁中 changes title to Chinese', async () => {
    const { default: App } = await import('../App.jsx')
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: /切換為繁體中文/i }))
    expect(screen.getByText('Web Services 產生器')).toBeInTheDocument()
  })

  it('clicking EN restores English title', async () => {
    const { default: App } = await import('../App.jsx')
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: /切換為繁體中文/i }))
    fireEvent.click(screen.getByRole('button', { name: /switch to english/i }))
    expect(screen.getByText('Web Services Generator')).toBeInTheDocument()
  })
})
