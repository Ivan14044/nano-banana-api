import React, { useState } from 'react'
import { generateImage, uploadFile, getImageUrl } from '../services/api'
import './common.css'
import './GenerationTab.css'

function GenerationTab({ apiKey }) {
  const [prompt, setPrompt] = useState('')
  const [model, setModel] = useState('flash')
  const [resolution, setResolution] = useState('2048')
  const [negativePrompt, setNegativePrompt] = useState('')
  const [aspectRatio, setAspectRatio] = useState('1:1')
  const [cropToAspect, setCropToAspect] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [referenceImages, setReferenceImages] = useState([])

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files)
    if (files.length === 0) return

    if (referenceImages.length + files.length > 8) {
      alert('Максимум 8 референсных изображений!')
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
      
      setReferenceImages([...referenceImages, ...newImages])
    } catch (err) {
      alert(`Ошибка загрузки: ${err.message}`)
    }
  }

  const removeReferenceImage = (index) => {
    setReferenceImages(referenceImages.filter((_, i) => i !== index))
  }

  const handleGenerate = async () => {
    if (!apiKey) {
      alert('Введите API ключ!')
      return
    }

    if (!prompt.trim()) {
      alert('Введите описание изображения!')
      return
    }

    setIsGenerating(true)
    setError(null)
    setResult(null)

    try {
      const params = {
        prompt: prompt.trim(),
        model,
        resolution,
        negative_prompt: negativePrompt.trim() || null,
        aspect_ratio: aspectRatio,
        crop_to_aspect: cropToAspect,
        reference_images: referenceImages.map(img => img.path)
      }

      const response = await generateImage(apiKey, params)
      
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
      setError(err.message || 'Ошибка генерации')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="generation-tab">
      <div className="form-card">
      <div className="form-group">
        <label>Текстовое описание:</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Опишите желаемое изображение..."
          rows={5}
        />
      </div>

      {model === 'pro' && (
        <div className="form-group">
          <label>Референсные изображения (до 8, опционально):</label>
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={handleFileUpload}
            disabled={referenceImages.length >= 8}
          />
          {referenceImages.length > 0 && (
            <div className="reference-images">
              {referenceImages.map((img, idx) => (
                <div key={idx} className="reference-image-item">
                  <img src={getImageUrl(img.path)} alt={`Reference ${idx + 1}`} />
                  <button onClick={() => removeReferenceImage(idx)}>×</button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

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
        onClick={handleGenerate}
        disabled={isGenerating || !prompt.trim()}
        className="btn btn-primary btn-large"
      >
        {isGenerating ? 'Генерация...' : 'Сгенерировать'}
      </button>

      {error && (
        <div className="error-message">
          Ошибка: {error}
        </div>
      )}

      {result && (
        <div className="result">
          <h3>Результат:</h3>
          <img src={result.image_url} alt="Generated" />
          <a href={result.image_url} download className="btn btn-secondary">
            Скачать
          </a>
        </div>
      )}
    </div>
  )
}

export default GenerationTab
