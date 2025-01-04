import React, { createContext, useContext, useState, useEffect } from 'react';

export const QuizContext = createContext();

export const useQuiz = () => {
  const context = useContext(QuizContext);
  if (!context) {
    throw new Error('useQuiz must be used within a QuizProvider');
  }
  return context;
};

export const QuizProvider = ({ children }) => {
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Pobieranie wszystkich quizów
  const fetchQuizzes = async () => {
    try {
      const response = await fetch('http://localhost:3001/quiz');
      if (!response.ok) throw new Error('Failed to fetch quizzes');
      const data = await response.json();
      setQuizzes(data.quizzes || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Pobieranie pojedynczego quizu
  const getQuizById = async (id) => {
    try {
      const response = await fetch(`http://localhost:3001/quiz/${id}`);
      if (!response.ok) throw new Error('Quiz not found');
      const quiz = await response.json();
      return {
        ...quiz,
        timePerQuestion: quiz.timeLimit || 30
      };
    } catch (err) {
      throw new Error(err.message);
    }
  };

  // Dodawanie nowego quizu
  const addQuiz = async (quiz) => {
    try {
      const response = await fetch('http://localhost:3001/quiz', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(quiz),
      });
      if (!response.ok) throw new Error('Failed to add quiz');
      const newQuiz = await response.json();
      setQuizzes(prev => [...prev, newQuiz]);
      return newQuiz;
    } catch (err) {
      throw new Error(err.message);
    }
  };

  // Aktualizacja quizu
  const updateQuiz = async (id, updatedQuiz) => {
    try {
      const response = await fetch(`http://localhost:3001/quiz/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedQuiz),
      });
      if (!response.ok) throw new Error('Failed to update quiz');
      const quiz = await response.json();
      setQuizzes(prev => prev.map(q => q.id === id ? quiz : q));
      return quiz;
    } catch (err) {
      throw new Error(err.message);
    }
  };

  // Usuwanie quizu
  const deleteQuiz = async (id) => {
    try {
      const response = await fetch(`http://localhost:3001/quiz/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete quiz');
      setQuizzes(prev => prev.filter(quiz => quiz.id !== id));
    } catch (err) {
      throw new Error(err.message);
    }
  };

  // Pobranie quizów przy pierwszym renderowaniu
  useEffect(() => {
    fetchQuizzes();
  }, []);

  const value = {
    quizzes,
    loading,
    error,
    addQuiz,
    updateQuiz,
    deleteQuiz,
    getQuizById,
    refreshQuizzes: fetchQuizzes
  };

  return (
    <QuizContext.Provider value={value}>
      {children}
    </QuizContext.Provider>
  );
};