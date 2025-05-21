import React, { useState, useCallback, useEffect, useMemo, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { useQuiz } from '../context/QuizContext';
import { 
  faSearch, faBell, faUser, faClock, 
  faTrophy, faCheck, faCalendar, faSignOut,
  faPlus, faPlay, faTrash, faPencilAlt
} from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '../context/AuthContext';
import { QUIZ_CATEGORIES, DIFFICULTY_MAP } from '../utils/constants';
import '../styles/HomePage.css';
import StripeCheckout from '../components/StripeCheckout'; // Import StripeCheckout

// Komponent powiadomień
const NotificationsDropdown = memo(({ notifications, onNotificationClick }) => (
  <div className="notifications-dropdown">
    <h3>Powiadomienia</h3>
    {notifications.length > 0 ? (
      notifications.map(notification => (
        <div 
          key={notification.id}
          className={`notification-item ${notification.unread ? 'unread' : ''}`}
          onClick={() => onNotificationClick(notification.id)}
        >
          <p>{notification.text}</p>
        </div>
      ))
    ) : (
      <p className="no-notifications">Brak powiadomień</p>
    )}
  </div>
));

// Komponent nawigacji
const NavigationBar = memo(({ 
  searchQuery, 
  onSearchChange, 
  onSearch, 
  notifications, 
  showNotifications,
  toggleNotifications,
  onNotificationClick,
  user,
  onLogout,
  showUserMenu,
  toggleUserMenu,
  onSettingsClick
}) => {
  const unreadNotificationsCount = useMemo(
    () => notifications.filter(n => n.unread).length,
    [notifications]
  );
  
  return (
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
          onChange={onSearchChange}
          onKeyDown={(e) => e.key === 'Enter' && onSearch()}
        />
        <button className="search-button" onClick={onSearch}>
          Szukaj
        </button>
      </div>
      <div className="nav-right">
        <div className="notifications-container">
          <button 
            className="notification-button"
            onClick={toggleNotifications}
            aria-label="Powiadomienia"
          >
            <FontAwesomeIcon icon={faBell} />
            {unreadNotificationsCount > 0 && (
              <span className="notification-badge">{unreadNotificationsCount}</span>
            )}
          </button>
          {showNotifications && (
            <NotificationsDropdown 
              notifications={notifications} 
              onNotificationClick={onNotificationClick} 
            />
          )}
        </div>        <div className="user-profile-container">
          <button 
            className="user-profile"
            onClick={toggleUserMenu}
            aria-label="Profil użytkownika"
          >
            <img src={user.avatar} alt={`Awatar ${user.fullName}`} />
            <span>{user.fullName}</span>
          </button>
          {showUserMenu && (
            <div className="user-menu-dropdown">
              <button onClick={onSettingsClick} className="user-menu-item">
                <FontAwesomeIcon icon={faUser} />
                <span>Ustawienia konta</span>
              </button>
              <button onClick={onLogout} className="user-menu-item">
                <FontAwesomeIcon icon={faSignOut} />
                <span>Wyloguj się</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
});

// Komponent statystyk użytkownika
const UserStats = memo(({ user }) => {
  // Safety check - if user is null/undefined, show loading state
  if (!user) {
    return (
      <div className="user-stats loading">
        <div className="spinner"></div>
        <p>Loading user data...</p>
      </div>
    );
  }

  // Ensure stats object exists with default values
  const stats = user?.stats || { quizzes: 0, bestTime: '0min', correctAnswers: 0 };
  
  return (
  <div className="user-stats">
    <img 
      src={user.avatar || user.avatar_url || 'https://i.pravatar.cc/150?img=3'} 
      alt={`Awatar ${user.fullName || user.username || 'User'}`} 
      className="large-avatar" 
      onError={(e) => {
        e.target.src = 'https://i.pravatar.cc/150?img=3'; // Fallback avatar on error
      }}
    />
    <div className="stats-info">
      <h2>{user.fullName || user.username || 'User'}</h2>
      <p className="user-level">{user.level || 'Początkujący'}</p>
      <div className="progress-bar">
        <div className="progress" style={{ width: '70%' }}></div>
      </div>
      <div className="stats-grid">
        <div className="stat-item">
          <h3>{stats.quizzes}</h3>
          <p>Rozwiązanych quizów</p>
        </div>
        <div className="stat-item">
          <h3>{stats.bestTime}</h3>
          <p>Najlepszy czas</p>
        </div>
        <div className="stat-item">
          <h3>{stats.correctAnswers}</h3>
          <p>Poprawnych odpowiedzi</p>
        </div>
      </div>
    </div>
  </div>
)});

// Komponent filtru kategorii
const CategoryFilter = memo(({ categories, selectedCategory, onSelectCategory }) => (
  <div className="category-filter">
    {categories.map(category => (
      <button
        key={category.id}
        className={`category-button ${selectedCategory === category.id ? 'active' : ''}`}
        onClick={() => onSelectCategory(category.id)}
      >
        {category.name}
      </button>
    ))}
  </div>
));

// Komponent karty quizu
const QuizCard = memo(({ 
  quiz, 
  isSelected, 
  onSelect, 
  onStart, 
  onEdit, 
  onDelete 
}) => (
  <div 
    className={`quiz-card ${isSelected ? 'selected' : ''}`}
    onClick={() => onSelect(quiz)}
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
        <span>{(quiz.questions?.length || 0)} pytań</span>
        <span>{quiz.difficulty}</span>
        <span>{quiz.createdAt && `Utworzono: ${new Date(quiz.createdAt).toLocaleDateString()}`}</span>
        {quiz.lastModified && quiz.lastModified !== quiz.createdAt && (
          <span>Zmodyfikowano: {new Date(quiz.lastModified).toLocaleDateString()}</span>
        )}
      </div>
      {isSelected && (
        <div className="quiz-actions">
          <button 
            className="start-quiz-button" 
            onClick={(e) => {
              e.stopPropagation();
              onStart(quiz);
            }}
          >
            <FontAwesomeIcon icon={faPlay} /> Rozpocznij
          </button>
          <button 
            className="edit-quiz-button" 
            onClick={(e) => {
              e.stopPropagation();
              onEdit(e, quiz);
            }}
          >
            <FontAwesomeIcon icon={faPencilAlt} size="sm" />
          </button>
          <button 
            className="delete-quiz-button" 
            onClick={(e) => {
              e.stopPropagation();
              onDelete(e, quiz);
            }}
          >
            <FontAwesomeIcon icon={faTrash} size="sm" />
          </button>
        </div>
      )}
    </div>
  </div>
));

// Komponenty sekcji bocznej
const OnlineUsersSection = memo(({ users }) => (
  <div className="online-users-section">
    <h3>Inni użytkownicy online</h3>
    <div className="online-users-list">
      {users.map(user => (
        <div key={user.id} className="online-user-item">
          <img src={user.avatar} alt={user.fullName} className="online-user-avatar" />
          <div className="online-user-info">
            <span className="online-user-name">{user.fullName}</span>
            <span className="online-user-status">{user.status}</span>
          </div>
        </div>
      ))}
      <div className="more-users">20+ innych użytkowników</div>
    </div>
  </div>
));

const AchievementsSection = memo(({ achievements }) => (
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
));

const RemindersSection = memo(({ reminders }) => (
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
));  // Główny komponent strony
const HomePage = () => {
  const { user, logout, verifyAuthState } = useAuth();
  const { quizzes, deleteQuiz, loading, error, refreshQuizzes, filterQuizzes } = useQuiz();
  const navigate = useNavigate();
  const [showPremiumModal, setShowPremiumModal] = React.useState(false); // State for premium modal

  // Guard against missing user or invalid auth
  useEffect(() => {
    async function checkAuth() {
      if (!user) {
        console.log("User not found, redirecting to login");
        navigate('/login');
        return;
      }
      
      // Dodatkowo sprawdź, czy token jest nadal ważny
      try {
        const isAuthenticated = await verifyAuthState();
        if (!isAuthenticated) {
          console.log("Authentication invalid, redirecting to login");
          navigate('/login');
        }
      } catch (error) {
        console.error("Error verifying auth state:", error);
      }
    }
    
    checkAuth();
  }, [user, navigate, verifyAuthState]);
  
  // Stany komponentu
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState([
    { id: 1, text: 'Nowy quiz dostępny: "Cyberbezpieczeństwo 2024"', unread: true },
    { id: 2, text: 'Gratulacje! Zdobyłeś nowe osiągnięcie!', unread: true },
    { id: 3, text: 'Przypomnienie o quizie: "Podstawy Sieci"', unread: false }
  ]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [selectedQuiz, setSelectedQuiz] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('');

  // Dane statyczne (używamy stałych z pliku constants.js)
  const categories = useMemo(() => QUIZ_CATEGORIES, []);

  const onlineUsers = useMemo(() => [
    { id: 1, name: 'Anna K.', avatar: 'https://i.pravatar.cc/100?img=1', status: 'Rozwiązuje quiz' },
    { id: 2, name: 'Tomek W.', avatar: 'https://i.pravatar.cc/100?img=2', status: 'Przegląda osiągnięcia' },
    { id: 3, name: 'Kasia M.', avatar: 'https://i.pravatar.cc/100?img=3', status: 'Dostępny' },
    { id: 4, name: 'Piotr B.', avatar: 'https://i.pravatar.cc/100?img=4', status: 'Rozwiązuje quiz' },
    { id: 5, name: 'Ewa N.', avatar: 'https://i.pravatar.cc/100?img=5', status: 'Dostępny' }
  ], []);

  const achievements = useMemo(() => [
    { id: 1, name: 'Comeback', icon: '🏆', description: 'Powrót po 30 dniach nieobecności', progress: 100 },
    { id: 2, name: 'Zwycięzca', icon: '⭐', description: 'Ukończ 10 quizów z wynikiem 100%', progress: 60 },
    { id: 3, name: 'Farciarz', icon: '🎯', description: 'Odpowiedz poprawnie na 50 pytań z rzędu', progress: 30 }
  ], []);

  const reminders = useMemo(() => [
    { id: 1, title: 'Control Your Account', date: 'Due Today', icon: faUser, urgent: true },
    { id: 2, title: 'Clear Desk Policy', date: 'Due Next Week', icon: faCalendar, urgent: false },
    { id: 3, title: 'Use of Flash Drives', date: 'Due May 15th', icon: faClock, urgent: false },
    { id: 4, title: 'Reporting an Incident', date: 'Due June 23rd', icon: faCheck, urgent: false }
  ], []);

  // Efekty
  useEffect(() => {
    refreshQuizzes();
    // Pusta tablica zależności, żeby wywołać tylko raz przy montowaniu komponentu
  }, []); // Usunięto refreshQuizzes z zależności
  // Zamknij powiadomienia i menu użytkownika po kliknięciu poza nimi
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showNotifications && !event.target.closest('.notifications-container')) {
        setShowNotifications(false);
      }
      if (showUserMenu && !event.target.closest('.user-profile-container')) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [showNotifications, showUserMenu]);

  // Memoizowane wartości
  const sortedQuizzes = useMemo(() => 
    [...(quizzes || [])].sort((a, b) => 
      new Date(b.createdAt || 0) - new Date(a.createdAt || 0)
    ),
    [quizzes]
  );

  const promotedQuizzes = useMemo(() => 
    sortedQuizzes.map(quiz => ({
      ...quiz,
      duration: `${quiz.timeLimit || 30} s`,
      difficulty: DIFFICULTY_MAP[quiz.difficulty] || 'Nieznany'
    })),
    [sortedQuizzes]
  );

  const filteredQuizzes = useMemo(() => 
    filterQuizzes(searchQuery, selectedCategory),
    [filterQuizzes, searchQuery, selectedCategory]
  );

  // Funkcje obsługi zdarzeń
  const handleSearch = useCallback(() => {
    // Wyszukiwanie jest automatyczne przez filterQuizzes
  }, []);

  const handleSearchChange = useCallback((e) => {
    setSearchQuery(e.target.value);
    // Resetowanie wybranego quizu przy zmianie wyszukiwania
    setSelectedQuiz(null);
  }, []);

  const handleQuizClick = useCallback((quiz) => {
    setSelectedQuiz(prevSelected => prevSelected?.id === quiz.id ? null : quiz);
  }, []);

  const handleCategorySelect = useCallback((categoryId) => {
    setSelectedCategory(categoryId);
    setSelectedQuiz(null); // Resetowanie wybranego quizu przy zmianie kategorii
  }, []);

  const handleDeleteQuiz = useCallback(async (e, quiz) => {
    e.stopPropagation();
    if (window.confirm(`Czy na pewno chcesz usunąć quiz "${quiz.title}"? Tej operacji nie można cofnąć.`)) {
      try {
        await deleteQuiz(quiz.id);
        if (selectedQuiz?.id === quiz.id) {
          setSelectedQuiz(null);
        }
        await refreshQuizzes();
      } catch (error) {
        alert(`Wystąpił błąd podczas usuwania quizu: ${error.message}`);
      }
    }
  }, [deleteQuiz, refreshQuizzes, selectedQuiz]);

  const handleStartQuiz = useCallback((quiz) => {
    navigate(`/solve-quiz/${quiz.id}`);
  }, [navigate]);

  const handleNotificationClick = useCallback((notificationId) => {
    setNotifications(prev => prev.map(notif => 
      notif.id === notificationId ? { ...notif, unread: false } : notif
    ));
  }, []);

  const handleToggleNotifications = useCallback((e) => {
    e.stopPropagation();
    setShowNotifications(prev => !prev);
  }, []);

  const handleCreateQuiz = useCallback(() => {
    navigate('/create-quiz');
  }, [navigate]);

  const handleEditQuiz = useCallback((e, quiz) => {
    e.stopPropagation();
    navigate('/create-quiz', { state: { quiz } });
  }, [navigate]);

  const toggleUserMenu = useCallback(() => {
    setShowUserMenu(prev => !prev);
  }, []);
  
  const handleSettingsClick = useCallback(() => {
    navigate('/user-settings');
    setShowUserMenu(false);
  }, [navigate]);

  const handleLogout = useCallback(() => {
    logout();
    navigate('/');
  }, [logout, navigate]);

  const handleGoPremium = () => {
    // Option 1: Navigate to a dedicated premium page
    navigate('/premium'); 
    // Option 2: Show a modal (requires StripeCheckout to be rendered conditionally)
    // setShowPremiumModal(true);
  };

  // Wyświetlanie ładowania/błędu
  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Ładowanie quizów...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h3>Błąd</h3>
        <p>{error}</p>
        <button onClick={refreshQuizzes} className="retry-button">
          Spróbuj ponownie
        </button>
      </div>
    );
  }

  return (
    <div className="home-container">
      {/* Navigation */}      <NavigationBar 
        searchQuery={searchQuery}
        onSearchChange={handleSearchChange}
        onSearch={handleSearch}
        notifications={notifications}
        showNotifications={showNotifications}
        toggleNotifications={handleToggleNotifications}
        onNotificationClick={handleNotificationClick}
        user={user}
        onLogout={handleLogout}
        showUserMenu={showUserMenu}
        toggleUserMenu={toggleUserMenu}
        onSettingsClick={handleSettingsClick}
      />

      <div className="main-content">
        <div className="content-left">
          {/* User Stats */}
          <UserStats user={user} />

          {/* Promoted Quizzes */}
          <div className="promoted-section">
            <div className="section-header">
              <div className="section-header-left">
                <h2>Promowane quizy</h2>
                <CategoryFilter 
                  categories={categories}
                  selectedCategory={selectedCategory}
                  onSelectCategory={handleCategorySelect}
                />
                <p className="quiz-count">
                  {filteredQuizzes.length} {filteredQuizzes.length === 1 ? 'quiz' : 'quizy'}
                </p>
              </div>
              {!user?.has_premium_access && (
                <button className="go-premium-button" onClick={handleGoPremium}>
                  Przejdź na Premium
                </button>
              )}
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
                  <QuizCard
                    key={quiz.id}
                    quiz={quiz}
                    isSelected={selectedQuiz?.id === quiz.id}
                    onSelect={handleQuizClick}
                    onStart={handleStartQuiz}
                    onEdit={handleEditQuiz}
                    onDelete={handleDeleteQuiz}
                  />
                ))
              )}
            </div>
          </div>
        </div>

        <div className="content-right">
          {/* Online Users */}
          <OnlineUsersSection users={onlineUsers} />

          {/* Achievements */}
          <AchievementsSection achievements={achievements} />

          {/* Reminders */}
          <RemindersSection reminders={reminders} />
        </div>
      </div>

      {/* Modal for Premium Checkout - Alternative to dedicated page */}
      {/* {showPremiumModal && (
        <div className=\"modal-overlay\">
          <div className=\"modal-content\">
            <button onClick={() => setShowPremiumModal(false)} className=\"close-modal\">&times;</button>
            <StripeCheckout priceId={import.meta.env.VITE_STRIPE_PREMIUM_PLAN_ID || 'YOUR_PREMIUM_PRICE_ID'} />
          </div>
        </div>
      )} */}

    </div>
  );
};

export default HomePage;