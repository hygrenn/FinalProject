import { useAuthTokenRef } from '@/lib/api'

describe('useAuthTokenRef', () => {
  afterEach(() => useAuthTokenRef.clearToken())

  it('getToken returns null by default', () => {
    expect(useAuthTokenRef.getToken()).toBeNull()
  })

  it('setToken stores token', () => {
    useAuthTokenRef.setToken('abc123')
    expect(useAuthTokenRef.getToken()).toBe('abc123')
  })

  it('clearToken resets to null', () => {
    useAuthTokenRef.setToken('abc123')
    useAuthTokenRef.clearToken()
    expect(useAuthTokenRef.getToken()).toBeNull()
  })
})
