import React, { useState } from 'react'
import { editImage, uploadFile, getImageUrl } from '../services/api'
import './common.css'
import './EditingTab.css'

function EditingTab({ apiKey }) {
  const [images, setImages] = useState([])
  const [prompt, setPrompt] = useState('')
  const [model, setModel] = useState('flash')
  const [resolution, setResolution] = useState('')
  const [negativePrompt, setNegativePrompt] = useState('')
  const [aspectRatio, setAspectRatio] = useState('1:1')
  const [cropToAspect, setCropToAspect] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState(null)

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files)
    if (files.length === 0) return

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

  const handleEdit = async () => {
    if (!apiKey) {
      alert('Введите API ключ!')
      return
    }

    if (images.length === 0) {
      alert('Загрузите изображения!')
      return
    }

    if (!prompt.trim()) {
      alert('Введите инструкции по редактированию!')
      return
    }

    setIsEditing(true)
    setError(null)
    setResults([])

    try {
      const editPromises = images.map(img => 
        editImage(apiKey, {
          image_path: img.path,
          prompt: prompt.trim(),
          model,
          resolution: resolution || null,
          negative_prompt: negativePrompt.trim() || null,
          aspect_ratio: aspectRatio,
          crop_to_aspect: cropToAspect
        })
      )

      const responses = await Promise.all(editPromises)
      
      const successful = responses
        .filter(r => r.success)
        .map(r => ({
          image_url: getImageUrl(r.image_path),
          image_path: r.image_path,
          id: r.id
        }))
      
      setResults(successful)
      
      if (successful.length === 0) {
        setError('Не удалось отредактировать ни одного изображения')
      }
    } catch (err) {
      setError(err.message || 'Ошибка редактирования')
    } finally {
      setIsEditing(false)
    }
  }

  return (
    <div className="editing-tab">
      <div className="form-card">
      <div className="form-group">
        <label>Изображения для редактирования:</label>
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileUpload}
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
        <div className="image-count">Изображений: {images.length}</div>
      </div>

      <div className="form-group">
        <label>Инструкции по редактированию:</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Опишите, как нужно изменить изображения..."
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
          <label>Модель:</label>
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            <option value="flash">Flash (быстро)</option>
            <option value="pro">Pro (качественно)</option>
          </select>
        </div>

        <div className="form-group">
          <label>Разрешение (оставить пустым для исходного):</label>
          <select value={resolution} onChange={(e) => setResolution(e.target.value)}>
            <option value="">Исходное</option>
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
        onClick={handleEdit}
        disabled={isEditing || images.length === 0 || !prompt.trim()}
        className="btn btn-primary btn-large"
      >
        {isEditing ? 'Редактирование...' : 'Редактировать все изображения'}
      </button>

      {error && (
        <div className="error-message">
          Ошибка: {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="results">
          <h3>Результаты ({results.length}):</h3>
          <div className="results-grid">
            {results.map((result, idx) => (
              <div key={idx} className="result-item">
                <img src={result.image_url} alt={`Result ${idx + 1}`} />
                <a href={result.image_url} download className="btn btn-secondary">
                  Скачать
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default EditingTab
