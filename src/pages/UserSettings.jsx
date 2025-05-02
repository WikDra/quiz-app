import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

const UserSettings = () => {
  const { user, updateUserAvatar } = useAuth();
  const [avatarUrl, setAvatarUrl] = useState('');
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
  
  // Jeśli użytkownik nie jest zalogowany, pokaż stosowny komunikat
  if (!user) {
    return (
      <div className="settings-container">
        <h2>Ustawienia konta</h2>
        <p>Musisz być zalogowany, aby uzyskać dostęp do ustawień konta.</p>
      </div>
    );
  }
  
  return (
    <div className="settings-container">
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
        
        <div className="settings-section">
          <h3>Zmień awatar</h3>
          
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
            
            {message && (
              <div className={message.includes('Błąd') ? 'error-message' : 'success-message'}>
                {message}
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default UserSettings;
