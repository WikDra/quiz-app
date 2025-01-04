import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { useQuiz } from '../context/QuizContext';
import { 
  faSearch, faBell, faUser, faClock, 
  faTrophy, faCheck, faCalendar, faSignOut,
  faPlus, faPlay, faTrash, faPencilAlt
} from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '../context/AuthContext';
import '../styles/HomePage.css';

const HomePage = () => {
  const { user, logout } = useAuth();
  const { quizzes, deleteQuiz, loading, error, refreshQuizzes } = useQuiz();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState([
    { id: 1, text: 'Nowy quiz dostępny: "Cyberbezpieczeństwo 2024"', unread: true },
    { id: 2, text: 'Gratulacje! Zdobyłeś nowe osiągnięcie!', unread: true },
    { id: 3, text: 'Przypomnienie o quizie: "Podstawy Sieci"', unread: false }
  ]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [selectedQuiz, setSelectedQuiz] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('');

  // Odświeżanie quizów przy pierwszym renderowaniu
  useEffect(() => {
    refreshQuizzes();
  }, [refreshQuizzes]);

  const sortedQuizzes = [...(quizzes || [])].sort((a, b) => 
    new Date(b.createdAt) - new Date(a.createdAt)
  );

  const promotedQuizzes = sortedQuizzes.map(quiz => ({
    ...quiz,
    duration: `${quiz.timeLimit || 30} s`,
    participants: 0,
    difficulty: quiz.difficulty === 'easy' ? 'Łatwy' : quiz.difficulty === 'medium' ? 'Średni' : 'Trudny'
  }));

  const onlineUsers = [
    { id: 1, name: 'Anna K.', avatar: 'https://i.pravatar.cc/100?img=1', status: 'Rozwiązuje quiz' },
    { id: 2, name: 'Tomek W.', avatar: 'https://i.pravatar.cc/100?img=2', status: 'Przegląda osiągnięcia' },
    { id: 3, name: 'Kasia M.', avatar: 'https://i.pravatar.cc/100?img=3', status: 'Dostępny' },
    { id: 4, name: 'Piotr B.', avatar: 'https://i.pravatar.cc/100?img=4', status: 'Rozwiązuje quiz' },
    { id: 5, name: 'Ewa N.', avatar: 'https://i.pravatar.cc/100?img=5', status: 'Dostępny' }
  ];

  const achievements = [
    { id: 1, name: 'Comeback', icon: '🏆', description: 'Powrót po 30 dniach nieobecności', progress: 100 },
    { id: 2, name: 'Zwycięzca', icon: '⭐', description: 'Ukończ 10 quizów z wynikiem 100%', progress: 60 },
    { id: 3, name: 'Farciarz', icon: '🎯', description: 'Odpowiedz poprawnie na 50 pytań z rzędu', progress: 30 }
  ];

  const reminders = [
    { id: 1, title: 'Control Your Account', date: 'Due Today', icon: faUser, urgent: true },
    { id: 2, title: 'Clear Desk Policy', date: 'Due Next Week', icon: faCalendar, urgent: false },
    { id: 3, title: 'Use of Flash Drives', date: 'Due May 15th', icon: faClock, urgent: false },
    { id: 4, title: 'Reporting an Incident', date: 'Due June 23rd', icon: faCheck, urgent: false }
  ];

  const categories = [
    { id: '', name: 'Wszystkie' },
    { id: 'cybersecurity', name: 'Cyberbezpieczeństwo' },
    { id: 'programming', name: 'Programowanie' },
    { id: 'networking', name: 'Sieci komputerowe' },
    { id: 'other', name: 'Inne' }
  ];

  const filteredQuizzes = promotedQuizzes
    .filter(quiz => {
      const matchesSearch = !searchQuery.trim() || 
        quiz.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        quiz.difficulty.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesCategory = !selectedCategory || quiz.category === selectedCategory;
      
      return matchesSearch && matchesCategory;
    });

  const handleSearch = () => {
    // Wyszukiwanie jest automatyczne przez filteredQuizzes
  };

  const isCustomQuiz = useCallback((quizId) => {
    // W nowym API wszystkie quizy są edytowalne
    return true;
  }, []);

  const handleQuizClick = (quiz) => {
    setSelectedQuiz(quiz);
  };

  const handleDeleteQuiz = async (e, quiz) => {
    e.stopPropagation();
    if (window.confirm(`Czy na pewno chcesz usunąć quiz "${quiz.title}"? Tej operacji nie można cofnąć.`)) {
      try {
        await deleteQuiz(quiz.id);
        if (selectedQuiz?.id === quiz.id) {
          setSelectedQuiz(null);
        }
        refreshQuizzes(); // Odśwież listę quizów po usunięciu
      } catch (error) {
        alert('Wystąpił błąd podczas usuwania quizu. Spróbuj ponownie.');
      }
    }
  };

  const handleStartQuiz = () => {
    if (selectedQuiz) {
      navigate(`/solve-quiz/${selectedQuiz.id}`);
      setSelectedQuiz(null);
    }
  };

  const handleNotificationClick = (notificationId) => {
    setNotifications(notifications.map(notif => 
      notif.id === notificationId ? { ...notif, unread: false } : notif
    ));
  };

  const handleCreateQuiz = () => {
    navigate('/create-quiz');
  };

  const handleEditQuiz = (e, quiz) => {
    e.stopPropagation();
    navigate('/create-quiz', { state: { quiz } });
  };

  const unreadNotificationsCount = notifications.filter(n => n.unread).length;

  return (
    <div className="home-container">
      {/* Navigation */}
      <nav className="nav-bar">
        <div className="logo">
          <span className="logo-icon">🌐</span>
          <span className="logo-text">CyberQuiz</span>
        </div>
        <div className="search-bar">
          <FontAwesomeIcon icon={faSearch} className="search-icon" />
          <input 
            type="text" 
            placeholder="Szukaj quizów" 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="search-button" onClick={handleSearch}>
            Szukaj
          </button>
        </div>
        <div className="nav-right">
          <div className="notifications-container">
            <button 
              className="notification-button"
              onClick={() => setShowNotifications(!showNotifications)}
            >
              <FontAwesomeIcon icon={faBell} />
              {unreadNotificationsCount > 0 && (
                <span className="notification-badge">{unreadNotificationsCount}</span>
              )}
            </button>
            {showNotifications && (
              <div className="notifications-dropdown">
                <h3>Powiadomienia</h3>
                {notifications.map(notification => (
                  <div 
                    key={notification.id}
                    className={`notification-item ${notification.unread ? 'unread' : ''}`}
                    onClick={() => handleNotificationClick(notification.id)}
                  >
                    <p>{notification.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="user-profile">
            <img src={user.avatar} alt="Profile" />
            <span>{user.name}</span>
          </div>
          <button 
            className="logout-button"
            onClick={() => {
              logout();
              navigate('/');
            }}
          >
            <FontAwesomeIcon icon={faSignOut} />
          </button>
        </div>
      </nav>

      <div className="main-content">
        <div className="content-left">
          {/* User Stats */}
          <div className="user-stats">
            <img src={user.avatar} alt="Profile" className="large-avatar" />
            <div className="stats-info">
              <h2>{user.name}</h2>
              <p className="user-level">{user.level}</p>
              <div className="progress-bar">
                <div className="progress" style={{ width: '70%' }}></div>
              </div>
              <div className="stats-grid">
                <div className="stat-item">
                  <h3>{user.stats.quizzes}</h3>
                  <p>Rozwiązanych quizów</p>
                </div>
                <div className="stat-item">
                  <h3>{user.stats.bestTime}</h3>
                  <p>Najlepszy czas</p>
                </div>
                <div className="stat-item">
                  <h3>{user.stats.correctAnswers}</h3>
                  <p>Poprawnych odpowiedzi</p>
                </div>
              </div>
            </div>
          </div>

          {/* Promoted Quizzes */}
          <div className="promoted-section">
            <div className="section-header">
              <div className="section-header-left">
                <h2>Promowane quizy</h2>
                <div className="category-filter">
                  {categories.map(category => (
                    <button
                      key={category.id}
                      className={`category-button ${selectedCategory === category.id ? 'active' : ''}`}
                      onClick={() => setSelectedCategory(category.id)}
                    >
                      {category.name}
                    </button>
                  ))}
                </div>
                <p className="quiz-count">
                  {filteredQuizzes.length} {filteredQuizzes.length === 1 ? 'quiz' : 'quizy'}
                </p>
              </div>
              <button className="create-quiz-button" onClick={handleCreateQuiz}>
                <FontAwesomeIcon icon={faPlus} /> Stwórz quiz
              </button>
            </div>
            <div className="quiz-grid">
              {filteredQuizzes.length === 0 ? (
                <div className="no-quizzes">
                  <p>Nie znaleziono quizów spełniających kryteria wyszukiwania</p>
                </div>
              ) : (
                filteredQuizzes.map(quiz => (
                  <div 
                    key={quiz.id} 
                    className={`quiz-card ${selectedQuiz?.id === quiz.id ? 'selected' : ''}`}
                    onClick={() => handleQuizClick(quiz)}
                  >
                    <img 
                      src={quiz.image || 'https://images.unsplash.com/photo-1606326608606-aa0b62935f2b'} 
                      alt={quiz.title}
                      onError={(e) => {
                        e.target.src = 'https://images.unsplash.com/photo-1606326608606-aa0b62935f2b';
                      }}
                    />
                    <div className="quiz-info">
                      <span className="duration">{quiz.duration}</span>
                      <h3>{quiz.title}</h3>
                      <div className="quiz-details">
                        <span>{quiz.questions?.length || quiz.questions} pytań</span>
                        <span>{quiz.difficulty}</span>
                        <span>{quiz.participants} uczestników</span>
                        {quiz.createdAt && (
                          <span>Utworzono: {new Date(quiz.createdAt).toLocaleDateString()}</span>
                        )}
                        {quiz.lastModified && quiz.lastModified !== quiz.createdAt && (
                          <span>Zmodyfikowano: {new Date(quiz.lastModified).toLocaleDateString()}</span>
                        )}
                      </div>
                      {selectedQuiz?.id === quiz.id && (
                        <div className="quiz-actions">
                          <button className="start-quiz-button" onClick={handleStartQuiz}>
                            <FontAwesomeIcon icon={faPlay} /> Rozpocznij
                          </button>
                          {isCustomQuiz(quiz.id) && (
                            <>
                              <button 
                                className="edit-quiz-button" 
                                onClick={(e) => handleEditQuiz(e, quiz)}
                              >
                                <FontAwesomeIcon icon={faPencilAlt} size="sm" />
                              </button>
                              <button 
                                className="delete-quiz-button" 
                                onClick={(e) => handleDeleteQuiz(e, quiz)}
                              >
                                <FontAwesomeIcon icon={faTrash} size="sm" />
                              </button>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="content-right">
          {/* Online Users */}
          <div className="online-users-section">
            <h3>Inni użytkownicy online</h3>
            <div className="online-users-list">
              {onlineUsers.map(user => (
                <div key={user.id} className="online-user-item">
                  <img src={user.avatar} alt={user.name} className="online-user-avatar" />
                  <div className="online-user-info">
                    <span className="online-user-name">{user.name}</span>
                    <span className="online-user-status">{user.status}</span>
                  </div>
                </div>
              ))}
              <div className="more-users">20+ innych użytkowników</div>
            </div>
          </div>

          {/* Achievements */}
          <div className="achievements-section">
            <h3>Osiągnięcia</h3>
            <div className="achievements-grid">
              {achievements.map(achievement => (
                <div key={achievement.id} className="achievement-card">
                  <span className="achievement-icon">{achievement.icon}</span>
                  <div className="achievement-info">
                    <span className="achievement-name">{achievement.name}</span>
                    <div className="achievement-progress">
                      <div 
                        className="progress-bar" 
                        style={{ width: `${achievement.progress}%` }}
                      ></div>
                    </div>
                    <span className="achievement-description">{achievement.description}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Reminders */}
          <div className="reminders-section">
            <h3>Przypomnienia</h3>
            <div className="reminders-list">
              {reminders.map(reminder => (
                <div 
                  key={reminder.id} 
                  className={`reminder-item ${reminder.urgent ? 'urgent' : ''}`}
                  onClick={() => alert(`Otwieranie przypomnienia: ${reminder.title}`)}
                >
                  <FontAwesomeIcon icon={reminder.icon} className="reminder-icon" />
                  <div className="reminder-info">
                    <h4>{reminder.title}</h4>
                    <p>{reminder.date}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;