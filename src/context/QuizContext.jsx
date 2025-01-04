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

  const [quizzes, setQuizzes] = useState(() => {
    const savedQuizzes = localStorage.getItem('quizzes');
    return savedQuizzes ? [...JSON.parse(savedQuizzes)] : [];
  });

  function addQuiz(quiz) {
    setQuizzes(prev => [...prev, { ...quiz, id: `user-${Date.now()}` }]);
  }

  const updateQuiz = (id, updatedQuiz) => {
    setQuizzes(prev => prev.map(quiz => 
      quiz.id === id ? { ...updatedQuiz, id } : quiz
    ));
  };

  const deleteQuiz = (id) => {
    setQuizzes(prev => prev.filter(quiz => quiz.id !== id));
  };

  const getQuiz = (id) => {
    return quizzes.find(quiz => quiz.id === id);
  };

  useEffect(() => {
    localStorage.setItem('quizzes', JSON.stringify(quizzes));
  }, [quizzes]);

  const getQuizById = async (id) => {
    const quiz = quizzes.find(quiz => quiz.id === id);
    if (!quiz) {
      throw new Error('Quiz not found');
    }
    return {
      ...quiz,
      timePerQuestion: quiz.timeLimit || 30
    };
  };

  const value = {
    quizzes,
    addQuiz,
    updateQuiz,
    deleteQuiz,
    getQuiz,
    getQuizById
  };

  return (
    <QuizContext.Provider value={value}>
      {children}
    </QuizContext.Provider>
  );
};