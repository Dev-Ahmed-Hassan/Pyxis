import type { User } from '../types/auth'

const TOKEN_KEY = 'pyxis_access_token'
const USER_KEY = 'pyxis_cached_user'

export function getAccessToken() {
  return window.localStorage.getItem(TOKEN_KEY)
}

export function setAccessToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token)
}

export function getCachedUser(): User | null {
  const stored = window.localStorage.getItem(USER_KEY)
  if (!stored) return null

  try {
    return JSON.parse(stored) as User
  } catch {
    window.localStorage.removeItem(USER_KEY)
    return null
  }
}

export function setCachedUser(user: User) {
  window.localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function cacheProvisionalUser(email: string) {
  setCachedUser({
    id: '',
    full_name: email.split('@')[0] || 'Student',
    email,
    role: 'student',
    is_active: true,
    created_at: '',
  })
}

export function clearAccessToken() {
  window.localStorage.removeItem(TOKEN_KEY)
  window.localStorage.removeItem(USER_KEY)
}
