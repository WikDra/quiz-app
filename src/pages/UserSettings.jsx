import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faUser, faEnvelope, faLock } from '@fortawesome/free-solid-svg-icons';
import { API_BASE_URL } from '../utils/constants';
import '../styles/Auth.css';
import '../styles/UserSettings.css';

const UserSettings = () => {
  const { user, updateUserAvatar, updateUserData } = useAuth();
  const navigate = useNavigate();
  
  // Stan dla zakładek ustawień
  const [activeTab, setActiveTab] = useState('avatar');
  
  // Stan dla pola awatara
  const [avatarUrl, setAvatarUrl] = useState('');
  
  // Stan dla pól danych użytkownika
  const [fullName, setFullName] = useState(user?.fullName || '');
  const [email, setEmail] = useState(user?.email || '');
  
  // Stan dla pól hasła
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // Stan komunikatów i ładowania
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const handleAvatarChange = async (e) => {
    e.preventDefault();
    
    if (!avatarUrl.trim()) {
      setMessage('Proszę podać URL awatara.');
      return;
    }
    
    setIsLoading(true);
    
    try {
      const result = await updateUserAvatar(user.id, avatarUrl);
      
      if (result.success) {
        setMessage('Awatar został pomyślnie zaktualizowany.');
        setAvatarUrl('');
      } else {
        setMessage(`Błąd: ${result.error}`);
      }
    } catch (err) {
      setMessage(`Błąd: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleUserDataChange = async (e) => {
    e.preventDefault();
    
    if (!fullName.trim() || !email.trim()) {
      setMessage('Wszystkie pola są wymagane.');
      return;
    }
    
    setIsLoading(true);
    
    try {
      const result = await updateUserData(user.id, {
        fullName,
        email
      });
      
      if (result.success) {
        setMessage('Dane zostały pomyślnie zaktualizowane.');
      } else {
        setMessage(`Błąd: ${result.error}`);
      }
    } catch (err) {
      setMessage(`Błąd: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };
    const handlePasswordChange = async (e) => {
    e.preventDefault();
    
    if (!currentPassword.trim() || !newPassword.trim() || !confirmPassword.trim()) {
      setMessage('Wszystkie pola są wymagane.');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setMessage('Nowe hasła muszą być identyczne.');
      return;
    }
    
    if (newPassword.length < 6) {
      setMessage('Hasło musi mieć co najmniej 6 znaków.');
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Używamy osobnego zapytania API do zmiany hasła zamiast standardowego updateUserData
      const response = await fetch(`${API_BASE_URL}/api/users/${user.id}/change-password`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          currentPassword, 
          newPassword 
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setMessage('Hasło zostało pomyślnie zmienione.');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
      } else {
        setMessage(`Błąd: ${data.error || 'Nie udało się zmienić hasła'}`);
      }
    } catch (err) {
      setMessage(`Błąd: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setMessage('');
  };
  
  const handleBackClick = () => {
    navigate('/');
  };
  
  // Jeśli użytkownik nie jest zalogowany, pokaż stosowny komunikat
  if (!user) {
    return (
      <div className="settings-container">
        <h2>Ustawienia konta</h2>
        <p>Musisz być zalogowany, aby uzyskać dostęp do ustawień konta.</p>
      </div>
    );
  }
  
  // Renderowanie aktywnego formularza na podstawie wybranej zakładki
  const renderActiveForm = () => {
    switch (activeTab) {
      case 'avatar':
        return (
          <form onSubmit={handleAvatarChange}>
            <div className="form-group">
              <label htmlFor="avatarUrl">URL awatara</label>
              <input 
                type="url" 
                id="avatarUrl"
                value={avatarUrl}
                onChange={(e) => setAvatarUrl(e.target.value)}
                placeholder="https://przyklad.com/awatar.jpg"
              />
              <p className="input-hint">
                Wpisz bezpośredni link do obrazu z Internetu lub użyj serwisu jak 
                <a href="https://gravatar.com" target="_blank" rel="noopener noreferrer"> Gravatar</a>.
              </p>
            </div>
            
            <button 
              type="submit" 
              className="btn-primary" 
              disabled={isLoading}
            >
              {isLoading ? 'Aktualizowanie...' : 'Aktualizuj awatar'}
            </button>
          </form>
        );
      
      case 'user-data':
        return (
          <form onSubmit={handleUserDataChange}>
            <div className="form-group">
              <label htmlFor="fullName">
                <FontAwesomeIcon icon={faUser} /> Imię i nazwisko
              </label>
              <input 
                type="text" 
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jan Kowalski"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="email">
                <FontAwesomeIcon icon={faEnvelope} /> Adres e-mail
              </label>
              <input 
                type="email" 
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jan.kowalski@example.com"
              />
            </div>
            
            <button 
              type="submit" 
              className="btn-primary" 
              disabled={isLoading}
            >
              {isLoading ? 'Aktualizowanie...' : 'Aktualizuj dane'}
            </button>
          </form>
        );
      
      case 'password':
        return (
          <form onSubmit={handlePasswordChange}>
            <div className="form-group">
              <label htmlFor="currentPassword">
                <FontAwesomeIcon icon={faLock} /> Obecne hasło
              </label>
              <input 
                type="password" 
                id="currentPassword"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="newPassword">
                <FontAwesomeIcon icon={faLock} /> Nowe hasło
              </label>
              <input 
                type="password" 
                id="newPassword"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="confirmPassword">
                <FontAwesomeIcon icon={faLock} /> Potwierdź nowe hasło
              </label>
              <input 
                type="password" 
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
              />
              <p className="input-hint">
                Hasło musi mieć co najmniej 6 znaków.
              </p>
            </div>
            
            <button 
              type="submit" 
              className="btn-primary" 
              disabled={isLoading}
            >
              {isLoading ? 'Aktualizowanie...' : 'Zmień hasło'}
            </button>
          </form>
        );
      
      default:
        return null;
    }
  };
  
  return (
    <div className="settings-container">
      <button 
        className="back-button" 
        onClick={handleBackClick}
        aria-label="Powrót"
      >
        <FontAwesomeIcon icon={faArrowLeft} /> Powrót
      </button>
      
      <h2>Ustawienia konta</h2>
      
      <div className="user-profile">
        <div className="avatar-section">
          <img 
            src={user.avatar} 
            alt={`Awatar ${user.fullName}`} 
            className="profile-avatar" 
          />
          <h3>{user.fullName}</h3>
          <p>{user.email}</p>
        </div>
        
        <div className="settings-tabs-container">
          <div className="settings-tabs">
            <button 
              className={`settings-tab ${activeTab === 'avatar' ? 'active' : ''}`}
              onClick={() => handleTabChange('avatar')}
            >
              Zmień awatar
            </button>
            <button 
              className={`settings-tab ${activeTab === 'user-data' ? 'active' : ''}`}
              onClick={() => handleTabChange('user-data')}
            >
              Dane osobowe
            </button>
            <button 
              className={`settings-tab ${activeTab === 'password' ? 'active' : ''}`}
              onClick={() => handleTabChange('password')}
            >
              Zmień hasło
            </button>
          </div>
          
          <div className="settings-section">
            <h3>
              {activeTab === 'avatar' && 'Zmień awatar'}
              {activeTab === 'user-data' && 'Dane osobowe'}
              {activeTab === 'password' && 'Zmień hasło'}
            </h3>
            
            {renderActiveForm()}
            
            {message && (
              <div className={message.includes('Błąd') ? 'error-message' : 'success-message'}>
                {message}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserSettings;
