import type { User } from '../types/auth'
import { apiRequest } from './api'
import { setCachedUser } from './auth'

let currentUserRequest: Promise<User> | null = null
let lastValidatedAt = 0
const SESSION_VALIDATION_TTL_MS = 5 * 60 * 1000

export function refreshCurrentUser(force = false) {
  if (!force && Date.now() - lastValidatedAt < SESSION_VALIDATION_TTL_MS) {
    return Promise.resolve(null)
  }

  if (!currentUserRequest) {
    currentUserRequest = apiRequest<User>('/auth/me')
      .then((user) => {
        setCachedUser(user)
        lastValidatedAt = Date.now()
        return user
      })
      .finally(() => {
        currentUserRequest = null
      })
  }

  return currentUserRequest
}
