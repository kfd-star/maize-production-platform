import http from '../utils/http/http.js'

const LEGACY_API_ORIGIN = (import.meta.env.VITE_APP_LEGACY_API_ORIGIN || '').replace(/\/$/, '')

const buildLegacyUrl = (path) => {
  return LEGACY_API_ORIGIN ? `${LEGACY_API_ORIGIN}${path}` : path
}

const all = () => {
  const url = buildLegacyUrl('/hggy/all')
  return http.get(url)
}

const commitAll = (data) => {
  const url = buildLegacyUrl('/hggy/all')
  return http.post(url, data)
}

const login = (data) => {
  const url = '/api/login'
  return http.post(url, data)
}

const register = (data) => {
  const url = '/api/register'
  return http.post(url, data)
}

const getFiles = (filename) => {
  const url = `/api/getFiles?name=${filename}`
  return http.get(url)
}

const savaFileServe = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const url = `/api/upload`
  return http.post(url, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export default {
  login,
  all,
  commitAll,
  register,
  getFiles,
  savaFileServe,
}
