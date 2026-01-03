import React, { useState, useEffect } from 'react'
import { getGallery, deleteGeneration, getStatistics, getImageUrl } from '../services/api'
import ImageViewer from './ImageViewer'
import './GalleryTab.css'

function GalleryTab() {
  const [generations, setGenerations] = useState([])
  const [statistics, setStatistics] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [selectedImage, setSelectedImage] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const loadGallery = async () => {
    setIsLoading(true)
    try {
      const params = {}
      if (searchQuery.trim()) {
        params.search = searchQuery.trim()
      }
      if (typeFilter) {
        params.type = typeFilter
      }

      const [galleryResponse, statsResponse] = await Promise.all([
        getGallery(params),
        getStatistics()
      ])

      if (galleryResponse.success) {
        setGenerations(galleryResponse.generations)
      }

      if (statsResponse.success) {
        setStatistics(statsResponse.statistics)
      }
    } catch (err) {
      console.error('Ошибка загрузки галереи:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadGallery()
  }, [searchQuery, typeFilter])

  const handleDelete = async (genId, imagePath) => {
    if (!confirm('Вы уверены, что хотите удалить это изображение?')) {
      return
    }

    try {
      const response = await deleteGeneration(genId)
      if (response.success) {
        loadGallery()
      } else {
        alert('Ошибка удаления')
      }
    } catch (err) {
      alert(`Ошибка удаления: ${err.message}`)
    }
  }

  const typeMap = {
    'generate': 'Генерация',
    'edit': 'Редактирование',
    'combine': 'Комбинирование'
  }

  return (
    <div className="gallery-tab">
      <div className="gallery-controls">
        <div className="search-group">
          <label>Поиск:</label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Поиск по промпту..."
          />
        </div>

        <div className="filter-group">
          <label>Тип:</label>
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
            <option value="">Все</option>
            <option value="generate">Генерация</option>
            <option value="edit">Редактирование</option>
            <option value="combine">Комбинирование</option>
          </select>
        </div>

        <button onClick={loadGallery} className="btn btn-secondary">
          Обновить
        </button>
      </div>

      {statistics && (
        <div className="statistics">
          Всего: {statistics.total} | 
          Генераций: {statistics.by_type?.generate || 0} | 
          Редактирований: {statistics.by_type?.edit || 0} | 
          Комбинирований: {statistics.by_type?.combine || 0}
        </div>
      )}

      {isLoading ? (
        <div className="loading">Загрузка...</div>
      ) : generations.length === 0 ? (
        <div className="empty-gallery">Галерея пуста</div>
      ) : (
        <div className="gallery-grid">
          {generations.map((gen) => (
            <div key={gen.id} className="gallery-item">
              <div className="gallery-item-image">
                {gen.image_url ? (
                  <img
                    src={getImageUrl(gen.image_path)}
                    alt={gen.prompt?.substring(0, 50)}
                    onClick={() => setSelectedImage(getImageUrl(gen.image_path))}
                  />
                ) : (
                  <div className="no-image">Нет изображения</div>
                )}
              </div>
              <div className="gallery-item-info">
                <div className="gallery-item-type">{typeMap[gen.type] || gen.type}</div>
                <div className="gallery-item-prompt">
                  {gen.prompt?.substring(0, 50)}
                  {gen.prompt?.length > 50 ? '...' : ''}
                </div>
              </div>
              <div className="gallery-item-actions">
                <button
                  onClick={() => setSelectedImage(getImageUrl(gen.image_path))}
                  className="btn btn-secondary btn-small"
                >
                  Просмотр
                </button>
                {gen.image_url && (
                  <a
                    href={getImageUrl(gen.image_path)}
                    download
                    className="btn btn-secondary btn-small"
                  >
                    Скачать
                  </a>
                )}
                <button
                  onClick={() => handleDelete(gen.id, gen.image_path)}
                  className="btn btn-danger btn-small"
                >
                  Удалить
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedImage && (
        <ImageViewer
          imageUrl={selectedImage}
          onClose={() => setSelectedImage(null)}
        />
      )}
    </div>
  )
}

export default GalleryTab
