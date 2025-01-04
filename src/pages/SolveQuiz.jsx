import { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { QuizContext } from '../context/QuizContext';
import '../styles/SolveQuiz.css';

const SolveQuiz = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { getQuizById } = useContext(QuizContext);
  const [quiz, setQuiz] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);

  const [error, setError] = useState(null);

  useEffect(() => {
    const loadQuiz = async () => {
      try {
        const quizData = await getQuizById(id);
        setQuiz(quizData);
        setTimeLeft(quizData.timePerQuestion);
        setError(null);
      } catch (err) {
        setError(err.message);
        setQuiz(null);
      }
    };
    loadQuiz();
  }, [id, getQuizById]);

  useEffect(() => {
    if (!quiz || showResult) return;

    const timer = setInterval(() => {
      setTimeLeft((prevTime) => {
      if (prevTime <= 1) {
        const currentQuestion = quiz.questions[currentQuestionIndex];
        if (selectedAnswer && selectedAnswer.index === currentQuestion.correctAnswer) {
        setScore(prevScore => prevScore + 1);
        }
        handleNextQuestion();
        return quiz.timePerQuestion;
      }
      return prevTime - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [quiz, currentQuestionIndex, showResult, selectedAnswer]);

  const handleAnswerSelect = (answer, index) => {
    setSelectedAnswer({ answer, index });
  };

  useEffect(() => {
    console.log('Current Question Index:', currentQuestionIndex);
    console.log('Selected Answer:', selectedAnswer);
    console.log('Time Left:', timeLeft);
  }, [currentQuestionIndex, selectedAnswer, timeLeft]);

  const handleNextQuestion = () => {
    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(prevIndex => prevIndex + 1);
      setSelectedAnswer(null);
      setTimeLeft(quiz.timePerQuestion);
    } else {
      setShowResult(true);
    }
  };

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

  if (!currentQuestion) return <div className="solve-quiz-container">Loading question...</div>;

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
    </div>
  );
};

export default SolveQuiz;