import React, { useState } from 'react'
import { checkBalance } from '../services/api'
import './ApiSettings.css'

function ApiSettings({ apiKey, onApiKeyChange }) {
  const [inputKey, setInputKey] = useState(apiKey)
  const [isChecking, setIsChecking] = useState(false)
  const [balanceInfo, setBalanceInfo] = useState(null)

  const handleSave = () => {
    onApiKeyChange(inputKey)
    alert('API ключ сохранен!')
  }

  const handleCheckBalance = async () => {
    if (!inputKey.trim()) {
      alert('Введите API ключ!')
      return
    }

    setIsChecking(true)
    try {
      const result = await checkBalance(inputKey)
      if (result.success) {
        setBalanceInfo(result)
      } else {
        alert(`Ошибка: ${result.error || 'Неизвестная ошибка'}`)
        setBalanceInfo(null)
      }
    } catch (error) {
      alert(`Ошибка проверки баланса: ${error.message}`)
      setBalanceInfo(null)
    } finally {
      setIsChecking(false)
    }
  }

  return (
    <div className="api-settings">
      <div className="api-settings-group">
        <label>API ключ:</label>
        <input
          type="password"
          value={inputKey}
          onChange={(e) => setInputKey(e.target.value)}
          placeholder="Введите ваш API ключ от nanobananaapi.ai"
          className="api-key-input"
        />
        <button onClick={handleSave} className="btn btn-primary">
          Сохранить
        </button>
        <button
          onClick={handleCheckBalance}
          disabled={!inputKey.trim() || isChecking}
          className="btn btn-secondary"
        >
          {isChecking ? 'Проверка...' : 'Проверить баланс'}
        </button>
      </div>
      {balanceInfo && (
        <div className="balance-info">
          {balanceInfo.message || `Кредитов: ${balanceInfo.credits || 0}`}
        </div>
      )}
    </div>
  )
}

export default ApiSettings
