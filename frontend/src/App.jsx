import React, { useState } from 'react'
import ApiSettings from './components/ApiSettings'
import GenerationTab from './components/GenerationTab'
import EditingTab from './components/EditingTab'
import CombineTab from './components/CombineTab'
import GalleryTab from './components/GalleryTab'
import './App.css'

function App() {
  const [apiKey, setApiKey] = useState(localStorage.getItem('api_key') || '')
  const [activeTab, setActiveTab] = useState('generation')

  const handleApiKeyChange = (key) => {
    setApiKey(key)
    localStorage.setItem('api_key', key)
  }

  return (
    <div className="app">
      <div className="app-header">
        <h1>NanoBanana Pro - Генератор изображений</h1>
      </div>
      
      <ApiSettings apiKey={apiKey} onApiKeyChange={handleApiKeyChange} />
      
      <div className="tabs">
        <button
          className={activeTab === 'generation' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('generation')}
        >
          Генерация
        </button>
        <button
          className={activeTab === 'editing' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('editing')}
        >
          Редактирование
        </button>
        <button
          className={activeTab === 'combine' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('combine')}
        >
          Комбинирование
        </button>
        <button
          className={activeTab === 'gallery' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('gallery')}
        >
          Галерея
        </button>
      </div>
      
      <div className="tab-content">
        {activeTab === 'generation' && <GenerationTab apiKey={apiKey} />}
        {activeTab === 'editing' && <EditingTab apiKey={apiKey} />}
        {activeTab === 'combine' && <CombineTab apiKey={apiKey} />}
        {activeTab === 'gallery' && <GalleryTab />}
      </div>
    </div>
  )
}

export default App
