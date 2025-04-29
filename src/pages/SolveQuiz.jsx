import React, { useState, useEffect, useContext, useCallback, useMemo, memo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { QuizContext } from '../context/QuizContext';
import '../styles/SolveQuiz.css';
import { useAuth } from '../context/AuthContext';

// Zoptymalizowany komponent tabeli wyników
const ScoreTable = memo(({ currentScore, playerName }) => {
  return (
    <div className="score-table">
      <h3>Twój wynik</h3>
      <div className="score-table-content">
        <div className="score-row">
          <span className="score-details">{playerName}</span>
          <span className="score-value">{currentScore} pkt</span>
        </div>
      </div>
    </div>
  );
});

// Zoptymalizowany komponent odpowiedzi
const AnswerButton = memo(({ 
  answer, 
  index, 
  letter,
  selectedAnswer, 
  correctAnswerIndex, 
  timeExpired, 
  onSelect, 
  disabled 
}) => {
  let buttonClass = "answer-button";
  
  // Zawsze konwertujemy correctAnswerIndex na liczbę
  const correctIndex = typeof correctAnswerIndex === 'string' 
    ? parseInt(correctAnswerIndex, 10) 
    : correctAnswerIndex;
  
  if (selectedAnswer && selectedAnswer.answer === answer) {
    buttonClass += " selected";
  }
  
  if (timeExpired) {
    if (index === correctIndex) {
      buttonClass += " correct";
    } else if (selectedAnswer && selectedAnswer.index === index) {
      buttonClass += " incorrect";
    }
  }
  
  return (
    <button
      onClick={() => onSelect(answer, index)}
      className={buttonClass}
      data-letter={letter}
      disabled={disabled}
    >
      {answer}
    </button>
  );
});

const SolveQuiz = () => {
  const { user } = useAuth();
  const { id } = useParams();
  const navigate = useNavigate();
  const { getQuizById } = useContext(QuizContext);
  
  // Stan komponentu
  const [quiz, setQuiz] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [correctAnswers, setCorrectAnswers] = useState(0);
  const [showScores, setShowScores] = useState(false);
  const [error, setError] = useState(null);
  const [timerActive, setTimerActive] = useState(true); // Nowy stan do kontrolowania timera

  // Powrót do strony głównej
  const handleBackToHome = useCallback(() => {
    navigate('/home');
  }, [navigate]);

  // Przejście do następnego pytania
  const handleNextQuestion = useCallback(() => {
    if (!quiz) return;
    
    const isLastQuestion = currentQuestionIndex >= quiz.questions.length - 1;
    
    if (isLastQuestion) {
      setShowScores(false);
      setShowResult(true);
      setTimerActive(false); // Zatrzymaj timer na ostatniej stronie
    } else {
      const nextIndex = currentQuestionIndex + 1;
      setCurrentQuestionIndex(nextIndex);
      setSelectedAnswer(null);
      // Resetujemy czas dla nowego pytania
      setTimeLeft(quiz.timeLimit || 30);
      setShowScores(false);
      setTimerActive(true); // Aktywuj timer dla nowego pytania
    }
  }, [quiz, currentQuestionIndex]);
  
  // Obsługa wyboru odpowiedzi
  const handleAnswerSelect = useCallback((answer, index) => {
    if (!selectedAnswer && quiz) {  
      const currentQuestion = quiz.questions[currentQuestionIndex];
      setSelectedAnswer({ answer, index });
      setTimerActive(false); // Zatrzymaj timer po wyborze odpowiedzi
      
      // Zapewniamy, że correctAnswer jest liczbą
      const correctAnswerIndex = typeof currentQuestion.correctAnswer === 'string'
        ? parseInt(currentQuestion.correctAnswer, 10)
        : currentQuestion.correctAnswer;
      
      console.log("Correct answer index:", correctAnswerIndex, "Selected index:", index, "Type of correctAnswer:", typeof currentQuestion.correctAnswer);
      
      if (index === correctAnswerIndex) {
        // Zwiększamy licznik poprawnych odpowiedzi
        setCorrectAnswers(prev => prev + 1);
        // Punktacja zależy od czasu odpowiedzi
        const maxTimeForQuestion = quiz.timeLimit || 30;
        const timeBonus = Math.floor((timeLeft / maxTimeForQuestion) * 100);
        const questionPoints = 100 + timeBonus;
        setScore(prevScore => prevScore + questionPoints);
      }
      
      // Dodajemy opóźnienie przed pokazaniem wyników
      setTimeout(() => {
        setShowScores(true);
      }, 2000); // 2 sekundy na zobaczenie poprawnej/niepoprawnej odpowiedzi

      // Przejście do następnego pytania po dodatkowych 3 sekundach (łącznie 5 sekund)
      setTimeout(() => {
        handleNextQuestion();
      }, 5000);
    }
  }, [quiz, currentQuestionIndex, selectedAnswer, timeLeft, handleNextQuestion]);

  // Załaduj dane quizu
  const loadQuiz = useCallback(async () => {
    let timeoutId;
    
    try {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      await new Promise(resolve => {
        timeoutId = setTimeout(resolve, 300);
      });

      const quizData = await getQuizById(id);
      if (!quizData) return;

      // Upewnij się, że correctAnswer jest zawsze liczbą
      if (quizData.questions && Array.isArray(quizData.questions)) {
        quizData.questions = quizData.questions.map(question => ({
          ...question,
          correctAnswer: typeof question.correctAnswer === 'string'
            ? parseInt(question.correctAnswer, 10)
            : question.correctAnswer
        }));
      }

      setQuiz({
        ...quizData,
        timePerQuestion: quizData.timeLimit || 30
      });
      setTimeLeft(quizData.timeLimit || 30);
      setTimerActive(true); // Aktywuj timer po załadowaniu quizu
      setError(null);
    } catch (err) {
      setError(err.message);
      setQuiz(null);
    }

    // Zawsze zwracamy funkcję czyszczącą
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [id, getQuizById]);

  useEffect(() => {
    let cleanup;
    const init = async () => {
      setScore(0);
      setCorrectAnswers(0);
      cleanup = await loadQuiz();
    };
    
    init();
    
    return () => {
      if (typeof cleanup === 'function') {
        cleanup();
      }
    };
  }, [loadQuiz]);
  
  // Efekt dla timera
  useEffect(() => {
    if (!quiz || showResult || selectedAnswer || !timerActive) return;

    const timer = setInterval(() => {
      setTimeLeft(prevTime => {
        if (prevTime <= 1) {
          console.log("Czas minął dla pytania:", currentQuestionIndex);
          setSelectedAnswer({ answer: '', index: -1 });
          setTimerActive(false); // Zatrzymaj timer gdy czas się skończył
          
          // Dodajemy opóźnienie przed pokazaniem wyników gdy skończy się czas
          setTimeout(() => {
            setShowScores(true);
          }, 2000);
          
          setTimeout(() => {
            handleNextQuestion();
          }, 5000);
          
          return 0; // Zatrzymaj na 0, aby uniknąć problemów z ponownym uruchomieniem timera
        }
        return prevTime - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [quiz, showResult, selectedAnswer, handleNextQuestion, currentQuestionIndex, timerActive]);

  // Memoizacja bieżącego pytania
  const currentQuestion = useMemo(() => 
    quiz?.questions?.[currentQuestionIndex] || null,
    [quiz, currentQuestionIndex]
  );

  // Memoizacja procentu ukończenia quizu
  const progressPercentage = useMemo(() => 
    quiz?.questions ? ((currentQuestionIndex + 1) / quiz.questions.length) * 100 : 0,
    [quiz, currentQuestionIndex]
  );

  // Memoizacja procentu poprawnych odpowiedzi - teraz bazuje na rzeczywistej liczbie poprawnych odpowiedzi
  const resultPercentage = useMemo(() => {
    if (!quiz?.questions?.length) return 0;
    return Math.round((correctAnswers / quiz.questions.length) * 100);
  }, [quiz, correctAnswers]);

  // Wyświetl komunikat błędu
  if (error) {
    return (
      <div className="solve-quiz-container">
        <div className="quiz-error">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={handleBackToHome}>Back to Home</button>
        </div>
      </div>
    );
  }

  // Wyświetl ładowanie
  if (!quiz) return <div className="solve-quiz-container">Loading...</div>;

  // Wyświetl wyniki
  if (showResult) {
    return (
      <div className="solve-quiz-container">
        <div className="quiz-result">
          <h2>Quiz ukończony!</h2>
          <div className="score-circle">
            <div className="score-number">{resultPercentage}%</div>
            <div className="score-text">poprawnych odpowiedzi</div>
          </div>
          <p>Zdobyłeś {score} punktów (maksymalnie możliwe: {quiz.questions.length * 200})</p>
          <button onClick={handleBackToHome}>Wróć do strony głównej</button>
        </div>
      </div>
    );
  }

  // Sprawdź czy pytanie jest dostępne
  if (!currentQuestion) {
    return <div className="solve-quiz-container">Loading question...</div>;
  }

  const letters = ['A', 'B', 'C', 'D'];
  // Dodatkowe sprawdzenia bezpieczeństwa
  const hasValidOptions = currentQuestion && currentQuestion.options && Array.isArray(currentQuestion.options);
  
  return (
    <div className="solve-quiz-container">
      <div className="quiz-header">
        <div className="points">
          <img src="/points-icon.svg" alt="Points" className="points-icon" />
          {score}
        </div>
        <h1 className="quiz-title">{quiz.title}</h1>
        <button className="close-button" onClick={handleBackToHome}>×</button>
      </div>
      
      <div className="question-container">
        <h2 className="question-text">{currentQuestion ? currentQuestion.question : "Ładowanie pytania..."}</h2>
        <div className="answers-container">
          {hasValidOptions && currentQuestion.options.map((answer, index) => (
            <AnswerButton
              key={index}
              answer={answer}
              index={index}
              letter={letters[index]}
              selectedAnswer={selectedAnswer}
              correctAnswerIndex={currentQuestion.correctAnswer}
              timeExpired={timeLeft <= 0}
              onSelect={handleAnswerSelect}
              disabled={!!selectedAnswer || timeLeft <= 0}
            />
          ))}

        </div>
        {selectedAnswer && currentQuestion && currentQuestion.explanation && (
          <div className="explanation">
            <p>{currentQuestion.explanation}</p>
          </div>
        )}
      </div>

      <div className="quiz-progress">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
        <div className="timer">{timeLeft}</div>
      </div>

      {showScores && (
        <div className="scores-overlay">
          <ScoreTable 
            currentScore={score}
            playerName={user.name}
          />
        </div>
      )}
    </div>
  );
};

export default SolveQuiz;