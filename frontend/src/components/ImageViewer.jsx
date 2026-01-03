import React, { useEffect } from 'react'
import './ImageViewer.css'

function ImageViewer({ imageUrl, onClose }) {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [onClose])

  return (
    <div className="image-viewer-overlay" onClick={onClose}>
      <div className="image-viewer-content" onClick={(e) => e.stopPropagation()}>
        <button className="image-viewer-close" onClick={onClose}>×</button>
        <img src={imageUrl} alt="Full size" />
        <div className="image-viewer-actions">
          <a href={imageUrl} download className="btn btn-primary">
            Скачать
          </a>
        </div>
      </div>
    </div>
  )
}

export default ImageViewer
