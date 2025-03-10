import React, { useState, useEffect, useCallback, memo, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQuiz } from '../context/QuizContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faPlus, faTimes, faArrowLeft, 
  faImage, faSave, faTrash 
} from '@fortawesome/free-solid-svg-icons';
import '../styles/CreateQuiz.css';

// Komponent formularza podstawowych informacji
const BasicInfoForm = memo(({ 
  quizData, 
  onQuizDataChange, 
  previewImage, 
  onImageUpload 
}) => (
  <div className="quiz-basic-info">
    <div className="form-group">
      <label htmlFor="title">Tytuł quizu*</label>
      <input
        type="text"
        id="title"
        name="title"
        value={quizData.title}
        onChange={onQuizDataChange}
        placeholder="Wprowadź tytuł quizu"
        required
      />
    </div>

    <div className="form-group">
      <label htmlFor="description">Opis</label>
      <textarea
        id="description"
        name="description"
        value={quizData.description}
        onChange={onQuizDataChange}
        placeholder="Wprowadź opis quizu"
        rows="3"
      />
    </div>

    <div className="form-row">
      <div className="form-group">
        <label htmlFor="category">Kategoria</label>
        <select
          id="category"
          name="category"
          value={quizData.category}
          onChange={onQuizDataChange}
        >
          <option value="">Wybierz kategorię</option>
          <option value="cybersecurity">Cyberbezpieczeństwo</option>
          <option value="programming">Programowanie</option>
          <option value="networking">Sieci komputerowe</option>
          <option value="other">Inne</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="difficulty">Poziom trudności</label>
        <select
          id="difficulty"
          name="difficulty"
          value={quizData.difficulty}
          onChange={onQuizDataChange}
        >
          <option value="easy">Łatwy</option>
          <option value="medium">Średni</option>
          <option value="hard">Trudny</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="timeLimit">Limit czasu (sekundy)</label>
        <input
          type="number"
          id="timeLimit"
          name="timeLimit"
          value={quizData.timeLimit}
          onChange={onQuizDataChange}
          min="1"
          max="120"
        />
      </div>
    </div>

    <div className="form-group">
      <label htmlFor="coverImage">Zdjęcie okładkowe</label>
      <div className="image-upload-container">
        <input
          type="file"
          id="coverImage"
          accept="image/*"
          onChange={onImageUpload}
          className="hidden-input"
        />
        <label htmlFor="coverImage" className="image-upload-label">
          {previewImage ? (
            <img src={previewImage} alt="Quiz cover" className="image-preview" />
          ) : (
            <>
              <FontAwesomeIcon icon={faImage} />
              <span>Wybierz zdjęcie</span>
            </>
          )}
        </label>
      </div>
    </div>
  </div>
));

// Komponent pojedynczej opcji odpowiedzi
const AnswerOption = memo(({ 
  index, 
  option, 
  isCorrect, 
  onOptionChange, 
  onCorrectAnswerChange 
}) => (
  <div className="option-item">
    <input
      type="text"
      value={option}
      onChange={(e) => onOptionChange(index, e.target.value)}
      placeholder={`Opcja ${index + 1}`}
    />
    <input
      type="radio"
      name="correctAnswer"
      checked={isCorrect}
      onChange={() => onCorrectAnswerChange(index)}
    />
  </div>
));

// Komponent formularza pytania
const QuestionForm = memo(({ 
  currentQuestion, 
  onQuestionChange, 
  onOptionChange, 
  onCorrectAnswerChange, 
  onAddQuestion, 
  isEditing 
}) => (
  <div className="question-form">
    <div className="form-group">
      <label htmlFor="question">Treść pytania*</label>
      <input
        type="text"
        id="question"
        name="question"
        value={currentQuestion.question}
        onChange={onQuestionChange}
        placeholder="Wprowadź treść pytania"
      />
    </div>

    <div className="options-grid">
      {currentQuestion.options.map((option, index) => (
        <AnswerOption
          key={index}
          index={index}
          option={option}
          isCorrect={currentQuestion.correctAnswer === index}
          onOptionChange={onOptionChange}
          onCorrectAnswerChange={onCorrectAnswerChange}
        />
      ))}
    </div>

    <div className="form-group">
      <label htmlFor="explanation">Wyjaśnienie (opcjonalne)</label>
      <textarea
        id="explanation"
        name="explanation"
        value={currentQuestion.explanation}
        onChange={onQuestionChange}
        placeholder="Wprowadź wyjaśnienie odpowiedzi"
        rows="2"
      />
    </div>

    <button 
      type="button" 
      className="add-question-button"
      onClick={onAddQuestion}
    >
      <FontAwesomeIcon icon={faPlus} />
      {isEditing ? 'Zaktualizuj pytanie' : 'Dodaj pytanie'}
    </button>
  </div>
));

// Komponent listy pytań
const QuestionsList = memo(({ 
  questions, 
  onEditQuestion, 
  onDeleteQuestion 
}) => (
  <div className="questions-list">
    {questions.map((question, index) => (
      <div key={index} className="question-item">
        <div className="question-content">
          <span className="question-number">#{index + 1}</span>
          <div className="question-text">
            <p>{question.question}</p>
            <small>{question.options.length} opcji</small>
          </div>
        </div>
        <div className="question-actions">
          <button 
            type="button"
            onClick={() => onEditQuestion(index)}
            className="edit-button"
          >
            Edytuj
          </button>
          <button 
            type="button"
            onClick={() => onDeleteQuestion(index)}
            className="delete-button"
          >
            <FontAwesomeIcon icon={faTrash} />
          </button>
        </div>
      </div>
    ))}
  </div>
));

// Główny komponent
const CreateQuiz = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { addQuiz, updateQuiz } = useQuiz();
  const editingQuiz = location.state?.quiz;

  // Stan komponentu
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [quizData, setQuizData] = useState(editingQuiz || {
    title: '',
    description: '',
    category: '',
    difficulty: 'medium',
    timeLimit: 15,
    coverImage: '',
    questions: []
  });

  const [currentQuestion, setCurrentQuestion] = useState({
    question: '',
    options: ['', '', '', ''],
    correctAnswer: 0,
    explanation: ''
  });

  const [previewImage, setPreviewImage] = useState(editingQuiz?.coverImage || null);
  const [editingQuestionIndex, setEditingQuestionIndex] = useState(null);

  // Callbacki do obsługi zdarzeń
  const handleQuizDataChange = useCallback((e) => {
    const { name, value } = e.target;
    setQuizData(prev => ({
      ...prev,
      [name]: value
    }));
    setHasChanges(true);
  }, []);

  const handleImageUpload = useCallback((e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewImage(reader.result);
        setQuizData(prev => ({
          ...prev,
          coverImage: reader.result
        }));
        setHasChanges(true);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const handleQuestionChange = useCallback((e) => {
    const { name, value } = e.target;
    setCurrentQuestion(prev => ({
      ...prev,
      [name]: value
    }));
    setHasChanges(true);
  }, []);

  const handleOptionChange = useCallback((index, value) => {
    setCurrentQuestion(prev => ({
      ...prev,
      options: prev.options.map((opt, i) => i === index ? value : opt)
    }));
    setHasChanges(true);
  }, []);

  const handleCorrectAnswerChange = useCallback((index) => {
    setCurrentQuestion(prev => ({
      ...prev,
      correctAnswer: index
    }));
    setHasChanges(true);
  }, []);

  const handleNavigateBack = useCallback(() => {
    if (!hasChanges || window.confirm('Masz niezapisane zmiany. Czy na pewno chcesz opuścić stronę?')) {
      navigate('/home');
    }
  }, [hasChanges, navigate]);

  const addQuestion = useCallback(() => {
    if (currentQuestion.question.trim() === '') {
      alert('Pytanie nie może być puste!');
      return;
    }

    if (currentQuestion.options.some(opt => opt.trim() === '')) {
      alert('Wszystkie opcje odpowiedzi muszą być wypełnione!');
      return;
    }

    setQuizData(prev => ({
      ...prev,
      questions: editingQuestionIndex !== null
        ? prev.questions.map((q, i) => i === editingQuestionIndex ? currentQuestion : q)
        : [...prev.questions, currentQuestion]
    }));

    setEditingQuestionIndex(null);
    setCurrentQuestion({
      question: '',
      options: ['', '', '', ''],
      correctAnswer: 0,
      explanation: ''
    });
    setHasChanges(true);
  }, [currentQuestion, editingQuestionIndex]);

  const editQuestion = useCallback((index) => {
    setCurrentQuestion(quizData.questions[index]);
    setEditingQuestionIndex(index);
  }, [quizData.questions]);

  const deleteQuestion = useCallback((index) => {
    setQuizData(prev => ({
      ...prev,
      questions: prev.questions.filter((_, i) => i !== index)
    }));
    setHasChanges(true);
  }, []);

  // Obsługa beforeunload
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (hasChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasChanges]);

  // Memoizacja funkcji do zapisywania quizu
  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();

    if (quizData.title.trim() === '') {
      alert('Tytuł quizu jest wymagany!');
      return;
    }

    if (quizData.questions.length === 0) {
      alert('Quiz musi zawierać przynajmniej jedno pytanie!');
      return;
    }

    setIsSubmitting(true);
    try {
      const quizToSave = {
        ...quizData,
        lastModified: new Date().toISOString()
      };

      if (editingQuiz) {
        await updateQuiz(editingQuiz.id, quizToSave);
        alert('Quiz został pomyślnie zaktualizowany!');
      } else {
        quizToSave.createdAt = new Date().toISOString();
        await addQuiz(quizToSave);
        alert('Quiz został pomyślnie utworzony!');
      }
      navigate('/home');
    } catch (error) {
      alert('Wystąpił błąd podczas ' + (editingQuiz ? 'aktualizacji' : 'tworzenia') + ' quizu: ' + error.message);
    } finally {
      setIsSubmitting(false);
    }
  }, [quizData, editingQuiz, navigate, addQuiz, updateQuiz]);

  return (
    <div className="create-quiz-container">
      <div className="create-quiz-header">
        <button 
          className="back-button"
          onClick={handleNavigateBack}
        >
          <FontAwesomeIcon icon={faArrowLeft} /> Wróć
        </button>
        <h1>{editingQuiz ? 'Edycja quizu' : 'Tworzenie nowego quizu'}</h1>
      </div>

      <form onSubmit={handleSubmit} className="create-quiz-form">
        <BasicInfoForm
          quizData={quizData}
          onQuizDataChange={handleQuizDataChange}
          previewImage={previewImage}
          onImageUpload={handleImageUpload}
        />

        <div className="questions-section">
          <h2>Pytania</h2>
          
          <QuestionForm
            currentQuestion={currentQuestion}
            onQuestionChange={handleQuestionChange}
            onOptionChange={handleOptionChange}
            onCorrectAnswerChange={handleCorrectAnswerChange}
            onAddQuestion={addQuestion}
            isEditing={editingQuestionIndex !== null}
          />

          <QuestionsList
            questions={quizData.questions}
            onEditQuestion={editQuestion}
            onDeleteQuestion={deleteQuestion}
          />
        </div>

        <div className="form-actions">
          <button 
            type="button" 
            className="cancel-button"
            onClick={handleNavigateBack}
          >
            <FontAwesomeIcon icon={faTimes} /> Anuluj
          </button>
          <button 
            type="submit" 
            className="save-button"
            disabled={quizData.questions.length === 0 || isSubmitting}
          >
            {isSubmitting ? (
              <span className="loading-spinner"></span>
            ) : (
              <>
                <FontAwesomeIcon icon={faSave} /> {editingQuiz ? 'Zapisz zmiany' : 'Zapisz quiz'}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateQuiz;