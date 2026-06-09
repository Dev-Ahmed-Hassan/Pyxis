export type User = {
  id: string
  full_name: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

export type TokenResponse = {
  access_token: string
  token_type: string
}
