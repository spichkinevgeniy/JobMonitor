import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'

const NativeRequest = globalThis.Request

class BrowserRequest extends NativeRequest {
  constructor(input: RequestInfo | URL, init?: RequestInit) {
    const resolvedInput =
      typeof input === 'string' && input.startsWith('/')
        ? new URL(input, window.location.origin).toString()
        : input
    super(resolvedInput, init)
  }
}

globalThis.Request = BrowserRequest

afterEach(() => {
  cleanup()
  window.history.replaceState({}, '', '/miniapp/react/?mode=onboarding')
  delete window.Telegram
})
