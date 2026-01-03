/**
 * API клиент для взаимодействия с бэкендом
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * Проверка баланса кредитов
 */
export const checkBalance = async (apiKey) => {
  const response = await api.post('/balance', { api_key: apiKey })
  return response.data
}

/**
 * Генерация изображения
 */
export const generateImage = async (apiKey, params) => {
  const response = await api.post('/generate', {
    api_key: apiKey,
    ...params
  })
  return response.data
}

/**
 * Редактирование изображения
 */
export const editImage = async (apiKey, params) => {
  const response = await api.post('/edit', {
    api_key: apiKey,
    ...params
  })
  return response.data
}

/**
 * Комбинирование изображений
 */
export const combineImages = async (apiKey, params) => {
  const response = await api.post('/combine', {
    api_key: apiKey,
    ...params
  })
  return response.data
}

/**
 * Загрузка файла на сервер
 */
export const uploadFile = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}

/**
 * Получить список генераций для галереи
 */
export const getGallery = async (params = {}) => {
  const response = await api.get('/gallery', { params })
  return response.data
}

/**
 * Получить конкретную генерацию
 */
export const getGeneration = async (genId) => {
  const response = await api.get(`/gallery/${genId}`)
  return response.data
}

/**
 * Удалить генерацию
 */
export const deleteGeneration = async (genId) => {
  const response = await api.delete(`/gallery/${genId}`)
  return response.data
}

/**
 * Получить статистику
 */
export const getStatistics = async () => {
  const response = await api.get('/gallery/statistics')
  return response.data
}

/**
 * Получить URL изображения
 */
export const getImageUrl = (imagePath) => {
  if (!imagePath) return ''
  
  // Если уже полный URL, возвращаем как есть
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath
  }
  
  // Если путь начинается с /api/images, используем его напрямую
  if (imagePath.startsWith('/api/images/')) {
    const baseUrl = API_BASE_URL.replace('/api', '')
    return `${baseUrl}${imagePath}`
  }
  
  // Если относительный путь (generated/ или user/), добавляем /api/images
  return `${API_BASE_URL.replace('/api', '')}/api/images/${imagePath}`
}

export default api
