import { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { QuizContext } from '../context/QuizContext';
import '../styles/SolveQuiz.css';
import { useAuth } from '../context/AuthContext';

const ScoreTable = ({ currentScore, playerName }) => {
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
};

const SolveQuiz = () => {
  const { user, logout } = useAuth();
  const { id } = useParams();
  const navigate = useNavigate();
  const { getQuizById } = useContext(QuizContext);
  const [quiz, setQuiz] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [showScores, setShowScores] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadQuiz = async () => {
      try {
        const quizData = await getQuizById(id);
        console.log('Loaded quiz data:', quizData);
        setQuiz({
          ...quizData,
          timePerQuestion: quizData.timeLimit || 30
        });
        setTimeLeft(quizData.timeLimit || 30);
        setError(null);
      } catch (err) {
        console.error('Error loading quiz:', err);
        setError(err.message);
        setQuiz(null);
      }
    };
    loadQuiz();
  }, [id, getQuizById]);

  // Efekt do monitorowania zmian w quizie
  useEffect(() => {
    if (quiz) {
      console.log('Quiz updated:', {
        quiz,
        currentQuestionIndex,
        totalQuestions: quiz.questions.length,
        currentQuestion: quiz.questions[currentQuestionIndex]
      });
    }
  }, [quiz, currentQuestionIndex]);

  useEffect(() => {
    if (!quiz || showResult) return;

    const timer = setInterval(() => {
      setTimeLeft((prevTime) => {
        if (prevTime <= 1) {
          setShowScores(true);
          setTimeout(() => {
            handleNextQuestion();
          }, 2000);
          return quiz.timePerQuestion;
        }
        return prevTime - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [quiz, currentQuestionIndex, showResult]);

  const handleAnswerSelect = (answer, index) => {
    if (!selectedAnswer) {  // Sprawdzamy tylko przy pierwszym wyborze
      const currentQuestion = quiz.questions[currentQuestionIndex];
      if (index === currentQuestion.correctAnswer) {
        setScore(prevScore => prevScore + 1);
      }
      setSelectedAnswer({ answer, index });
      setShowScores(true);
      setTimeout(() => {
        handleNextQuestion();
      }, 2000);
    }
  };

  useEffect(() => {
    console.log('Current Question Index:', currentQuestionIndex);
    console.log('Selected Answer:', selectedAnswer);
    console.log('Time Left:', timeLeft);
  }, [currentQuestionIndex, selectedAnswer, timeLeft]);

  const handleNextQuestion = () => {
    const isLastQuestion = currentQuestionIndex >= quiz.questions.length - 1;
    
    if (isLastQuestion) {
      setShowScores(false);
      setShowResult(true);
    } else {
      const nextIndex = currentQuestionIndex + 1;
      setCurrentQuestionIndex(nextIndex);
      setSelectedAnswer(null);
      setTimeLeft(quiz.timePerQuestion);
      setShowScores(false);
    }
  };

  // Dodajemy efekt do debugowania
  useEffect(() => {
    console.log('Quiz state:', {
      currentQuestionIndex,
      questionsLength: quiz?.questions?.length,
      currentQuestion: quiz?.questions?.[currentQuestionIndex],
      timeLeft,
      showScores,
      showResult
    });
  }, [quiz, currentQuestionIndex, timeLeft, showScores, showResult]);

  if (error) {
    return (
      <div className="solve-quiz-container">
        <div className="quiz-error">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/home')}>Back to Home</button>
        </div>
      </div>
    );
  }

  if (!quiz) return <div className="solve-quiz-container">Loading...</div>;

  if (showResult) {
    const percentage = Math.round((score / quiz.questions.length) * 100);
    return (
      <div className="solve-quiz-container">
        <div className="quiz-result">
          <h2>Quiz ukończony!</h2>
          <div className="score-circle">
            <div className="score-number">{percentage}%</div>
            <div className="score-text">poprawnych odpowiedzi</div>
          </div>
          <p>Zdobyłeś {score} z {quiz.questions.length} punktów</p>
          <button onClick={() => navigate('/home')}>Wróć do strony głównej</button>
        </div>
      </div>
    );
  }

  const currentQuestion = quiz.questions[currentQuestionIndex];

  if (!quiz || !quiz.questions || !quiz.questions[currentQuestionIndex]) {
    console.log('Loading state:', {
      quiz: !!quiz,
      questions: !!quiz?.questions,
      currentQuestion: !!quiz?.questions?.[currentQuestionIndex],
      currentQuestionIndex
    });
    return <div className="solve-quiz-container">Loading question...</div>;
  }

  const letters = ['A', 'B', 'C', 'D'];
  const progressPercentage = ((currentQuestionIndex + 1) / quiz.questions.length) * 100;

  return (
    <div className="solve-quiz-container">
      <div className="quiz-header">
        <div className="points">
          <img src="/points-icon.svg" alt="Points" className="points-icon" />
          200
        </div>
        <h1 className="quiz-title">{quiz.title}</h1>
        <button className="close-button" onClick={() => navigate('/home')}>×</button>
      </div>
      
      <div className="question-container">
        <h2 className="question-text">{currentQuestion.question}</h2>
        <div className="answers-container">
          {currentQuestion.options.map((answer, index) => (
            <button
              key={index}
              onClick={() => handleAnswerSelect(answer, index)}
              className={`answer-button ${
                selectedAnswer && selectedAnswer.answer === answer
                  ? 'selected'
                  : ''
              } ${
                timeLeft <= 1 && index === currentQuestion.correctAnswer
                  ? 'correct'
                  : timeLeft <= 1 && selectedAnswer && selectedAnswer.index === index
                  ? 'incorrect'
                  : ''
              }`}
              data-letter={letters[index]}
              disabled={timeLeft <= 1}
            >
              {answer}
            </button>
          ))}
        </div>
        {selectedAnswer && currentQuestion.explanation && (
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