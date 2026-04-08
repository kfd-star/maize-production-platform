const legacyApiOrigin = (import.meta.env.VITE_APP_LEGACY_API_ORIGIN || '').replace(/\/$/, '')

export default {
  legacyApiOrigin,
}
