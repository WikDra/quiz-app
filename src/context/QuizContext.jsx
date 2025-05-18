import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { API_ENDPOINTS, DEFAULT_QUIZ_VALUES } from '../utils/constants';

const QuizContext = createContext();

export const useQuiz = () => {
  const context = useContext(QuizContext);
  if (!context) {
    throw new Error('useQuiz must be used within a QuizProvider');
  }
  return context;
};

// Pomocnicza funkcja do obsługi odpowiedzi HTTP
const handleResponse = async (response, errorMessage) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || errorMessage);
  }
  return response.json();
};

export const QuizProvider = ({ children }) => {
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastFetch, setLastFetch] = useState(null);
  const CACHE_DURATION = 5000; // 5 sekund cache

  // Pobieranie wszystkich quizów
  const fetchQuizzes = useCallback(async () => {
    // Sprawdź czy dane w cache są wciąż aktualne
    if (lastFetch && Date.now() - lastFetch < CACHE_DURATION) {
      return;
    }

    setLoading(true);    try {
      const response = await fetch(API_ENDPOINTS.QUIZ, {
        credentials: 'include' // Include cookies with request
      });
      const data = await handleResponse(response, 'Failed to fetch quizzes');
      setQuizzes(data.quizzes || []);
      setLastFetch(Date.now());
      setError(null);
    } catch (err) {
      console.error('Error fetching quizzes:', err);
      setError(err.message || 'Nie udało się pobrać quizów');
    } finally {
      setLoading(false);
    }
  }, [lastFetch]);

  // Pobieranie pojedynczego quizu - zoptymalizowane
  const getQuizById = useCallback(async (id) => {
    if (!id) throw new Error('ID is required');
    
    // Najpierw sprawdź w pamięci podręcznej
    const cachedQuiz = quizzes.find(q => q.id === parseInt(id, 10));
    if (cachedQuiz && lastFetch && Date.now() - lastFetch < CACHE_DURATION) {
      return {
        ...cachedQuiz,
        timePerQuestion: cachedQuiz.timeLimit || DEFAULT_QUIZ_VALUES.timeLimit
      };
    }
      try {
      const response = await fetch(API_ENDPOINTS.QUIZ_BY_ID(id), {
        credentials: 'include' // Include cookies with request
      });
      const quiz = await handleResponse(response, 'Quiz not found');
      
      // Aktualizuj cache tylko jeśli quiz się zmienił
      setQuizzes(prev => {
        const index = prev.findIndex(q => q.id === parseInt(id, 10));
        if (index === -1) {
          return [...prev, quiz];
        }
        const updatedQuizzes = [...prev];
        updatedQuizzes[index] = quiz;
        return updatedQuizzes;
      });
      
      return {
        ...quiz,
        timePerQuestion: quiz.timeLimit || DEFAULT_QUIZ_VALUES.timeLimit
      };
    } catch (err) {
      console.error(`Error fetching quiz ID ${id}:`, err);
      throw new Error(err.message || 'Nie udało się pobrać quizu');
    }
  }, [quizzes, lastFetch]);

  // Dodawanie nowego quizu - zoptymalizowane
  const addQuiz = useCallback(async (quiz) => {
    if (!quiz?.title || !quiz?.questions) {
      throw new Error('Quiz title and questions are required');
    }
    
    try {
      const quizWithDefaults = {
        ...DEFAULT_QUIZ_VALUES,
        ...quiz,
        createdAt: new Date().toISOString(),
        lastModified: new Date().toISOString()
      };
        const response = await fetch(API_ENDPOINTS.QUIZ, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', // Include cookies with request
        body: JSON.stringify(quizWithDefaults),
      });
      
      const newQuiz = await handleResponse(response, 'Failed to add quiz');
      setQuizzes(prev => [...prev, newQuiz]);
      return newQuiz;
    } catch (err) {
      console.error('Error adding quiz:', err);
      throw new Error(err.message || 'Nie udało się dodać quizu');
    }
  }, []);

  // Aktualizacja quizu - zoptymalizowane
  const updateQuiz = useCallback(async (id, updatedQuiz) => {
    if (!id || !updatedQuiz) {
      throw new Error('Quiz ID and updated data are required');
    }
    
    try {
      const quizData = {
        ...updatedQuiz,
        lastModified: new Date().toISOString()
      };
        const response = await fetch(API_ENDPOINTS.QUIZ_BY_ID(id), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', // Include cookies with request
        body: JSON.stringify(quizData),
      });
      
      const quiz = await handleResponse(response, 'Failed to update quiz');
      setQuizzes(prev => prev.map(q => q.id === id ? quiz : q));
      return quiz;
    } catch (err) {
      console.error(`Error updating quiz ID ${id}:`, err);
      throw new Error(err.message || 'Nie udało się zaktualizować quizu');
    }
  }, []);

  // Usuwanie quizu - zoptymalizowane
  const deleteQuiz = useCallback(async (id) => {
    if (!id) throw new Error('Quiz ID is required');
    
    try {      const response = await fetch(API_ENDPOINTS.QUIZ_BY_ID(id), {
        method: 'DELETE',
        credentials: 'include', // Include cookies with request
      });
      
      await handleResponse(response, 'Failed to delete quiz');
      setQuizzes(prev => prev.filter(quiz => quiz.id !== id));
      return true;
    } catch (err) {
      console.error(`Error deleting quiz ID ${id}:`, err);
      throw new Error(err.message || 'Nie udało się usunąć quizu');
    }
  }, []);

  useEffect(() => {
    fetchQuizzes();
  }, [fetchQuizzes]);

  // Filtrowanie quizów - zoptymalizowane z memoizacją
  const filterQuizzes = useCallback((searchQuery = '', category = '') => {
    const normalizedSearch = searchQuery.toLowerCase().trim();
    
    return quizzes.filter(quiz => {
      if (category && quiz.category !== category) {
        return false;
      }
      
      if (!normalizedSearch) {
        return true;
      }

      return quiz.title.toLowerCase().includes(normalizedSearch) ||
        (quiz.description && quiz.description.toLowerCase().includes(normalizedSearch));
    });
  }, [quizzes]);

  // Memoizowane wartości do sortowania i grupowania
  const sortedQuizzes = useMemo(() => 
    [...quizzes].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)),
    [quizzes]
  );

  const quizzesByCategory = useMemo(() => 
    quizzes.reduce((acc, quiz) => {
      const category = quiz.category || 'uncategorized';
      acc[category] = [...(acc[category] || []), quiz];
      return acc;
    }, {}),
    [quizzes]
  );

  // Memoizowana wartość kontekstu
  const contextValue = useMemo(() => ({
    quizzes: sortedQuizzes,
    quizzesByCategory,
    loading,
    error,
    addQuiz,
    updateQuiz,
    deleteQuiz,
    getQuizById,
    filterQuizzes,
    refreshQuizzes: fetchQuizzes
  }), [
    sortedQuizzes,
    quizzesByCategory,
    loading,
    error,
    addQuiz,
    updateQuiz,
    deleteQuiz,
    getQuizById,
    filterQuizzes,
    fetchQuizzes
  ]);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Ładowanie quizów...</p>
      </div>
    );
  }

  return (
    <QuizContext.Provider value={contextValue}>
      {children}
    </QuizContext.Provider>
  );
};

export { QuizContext };