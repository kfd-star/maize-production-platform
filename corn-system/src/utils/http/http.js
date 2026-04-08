import instance from './axios'

const post = (url, data, config = {}) => {
  return new Promise((resolve, reject) => {
    instance
      .post(url, data, config)
      .then((res) => {
        resolve(res)
      })
      .catch((err) => {
        reject(err)
      })
  })
}
const get = (url, config = {}) => {
  return new Promise((resolve, reject) => {
    instance
      .get(url, config)
      .then((res) => resolve(res))
      .catch((err) => reject(err))
  })
}

const put = (url, data, config = {}) => {
  const cfg = Object.assign({ headers: { 'Content-Type': 'application/json' } }, config)
  return new Promise((resolve, reject) => {
    instance
      .put(url, data, cfg)
      .then((res) => {
        resolve(res)
      })
      .catch((err) => {
        reject(err)
      })
  })
}

const del = (url, data) => {
  return new Promise((resolve, reject) => {
    instance
      .delete(url, { params: data })
      .then((res) => {
        resolve(res)
      })
      .catch((err) => {
        reject(err)
      })
  })
}

export default {
  post,
  get,
  put,
  del,
}
