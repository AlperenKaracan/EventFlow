import { client } from './generated/client.gen'

const browserOrigin = globalThis.location?.origin

client.setConfig({
  baseUrl:
    import.meta.env.VITE_API_BASE_URL ??
    browserOrigin ??
    'http://127.0.0.1:8000',
  credentials: 'include',
})

export { client }
