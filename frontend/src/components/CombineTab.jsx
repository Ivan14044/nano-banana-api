import React, { useState } from 'react'
import { combineImages, uploadFile, getImageUrl } from '../services/api'
import './common.css'
import './CombineTab.css'

function CombineTab({ apiKey }) {
  const [images, setImages] = useState([])
  const [prompt, setPrompt] = useState('')
  const [resolution, setResolution] = useState('2048')
  const [negativePrompt, setNegativePrompt] = useState('')
  const [aspectRatio, setAspectRatio] = useState('1:1')
  const [cropToAspect, setCropToAspect] = useState(false)
  const [isCombining, setIsCombining] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files)
    if (files.length === 0) return

    if (images.length + files.length > 8) {
      alert('Максимум 8 изображений!')
      return
    }

    try {
      const uploadPromises = files.map(file => uploadFile(file))
      const results = await Promise.all(uploadPromises)
      
      const newImages = results.map(r => ({
        filename: r.filename,
        path: r.path,
        url: r.url
      }))
      
      setImages([...images, ...newImages])
    } catch (err) {
      alert(`Ошибка загрузки: ${err.message}`)
    }
  }

  const removeImage = (index) => {
    setImages(images.filter((_, i) => i !== index))
  }

  const handleCombine = async () => {
    if (!apiKey) {
      alert('Введите API ключ!')
      return
    }

    if (images.length < 2) {
      alert('Добавьте минимум 2 изображения!')
      return
    }

    if (!prompt.trim()) {
      alert('Введите инструкции по комбинированию!')
      return
    }

    setIsCombining(true)
    setError(null)
    setResult(null)

    try {
      const response = await combineImages(apiKey, {
        image_paths: images.map(img => img.path),
        prompt: prompt.trim(),
        model: 'pro',
        resolution,
        negative_prompt: negativePrompt.trim() || null,
        aspect_ratio: aspectRatio,
        crop_to_aspect: cropToAspect
      })
      
      if (response.success) {
        setResult({
          image_url: getImageUrl(response.image_path),
          image_path: response.image_path,
          id: response.id
        })
      } else {
        setError(response.error || 'Неизвестная ошибка')
      }
    } catch (err) {
      setError(err.message || 'Ошибка комбинирования')
    } finally {
      setIsCombining(false)
    }
  }

  return (
    <div className="combine-tab">
      <div className="form-card">
      <div className="form-group">
        <label>Изображения для комбинирования (от 2 до 8):</label>
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileUpload}
          disabled={images.length >= 8}
        />
        {images.length > 0 && (
          <div className="images-list">
            {images.map((img, idx) => (
              <div key={idx} className="image-item">
                <img src={getImageUrl(img.path)} alt={`Image ${idx + 1}`} />
                <button onClick={() => removeImage(idx)}>×</button>
              </div>
            ))}
          </div>
        )}
        <div className="image-count">Изображений: {images.length}/8</div>
      </div>

      <div className="form-group">
        <label>Инструкции по комбинированию:</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Опишите, как нужно объединить изображения..."
          rows={5}
        />
      </div>

      <div className="form-group">
        <label>Негативный промпт (опционально):</label>
        <textarea
          value={negativePrompt}
          onChange={(e) => setNegativePrompt(e.target.value)}
          placeholder="Что не должно быть на изображении..."
          rows={2}
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Разрешение:</label>
          <select value={resolution} onChange={(e) => setResolution(e.target.value)}>
            <option value="1024">1024x1024 (1K)</option>
            <option value="2048">2048x2048 (2K)</option>
            <option value="4096">4096x4096 (4K)</option>
          </select>
        </div>

        <div className="form-group">
          <label>Соотношение сторон:</label>
          <select value={aspectRatio} onChange={(e) => setAspectRatio(e.target.value)}>
            <option value="1:1">1:1 (Квадрат)</option>
            <option value="16:9">16:9 (Широкоформатное)</option>
            <option value="9:16">9:16 (Портретное)</option>
            <option value="4:3">4:3 (Классическое)</option>
            <option value="3:4">3:4 (Портретное классическое)</option>
          </select>
        </div>
      </div>

      <div className="form-group checkbox-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={cropToAspect}
            onChange={(e) => setCropToAspect(e.target.checked)}
          />
          <span>Обрезать до точного соотношения сторон</span>
        </label>
      </div>
      </div>

      <button
        onClick={handleCombine}
        disabled={isCombining || images.length < 2 || !prompt.trim()}
        className="btn btn-primary btn-large"
      >
        {isCombining ? 'Комбинирование...' : 'Объединить изображения'}
      </button>

      {error && (
        <div className="error-message">
          Ошибка: {error}
        </div>
      )}

      {result && (
        <div className="result">
          <h3>Результат:</h3>
          <img src={result.image_url} alt="Combined" />
          <a href={result.image_url} download className="btn btn-secondary">
            Скачать
          </a>
        </div>
      )}
    </div>
  )
}

export default CombineTab
