const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3001;

// Middlewares
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Logger middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// Error handler middleware
const asyncHandler = (fn) => (req, res, next) => {
  return Promise.resolve(fn(req, res, next)).catch(next);
};

// Ścieżki do plików JSON
const USERS_FILE_PATH = path.join(__dirname, 'public', 'users.json');
const QUIZ_FILE_PATH = path.join(__dirname, 'public', 'quiz.json');

// Helper functions
const readJsonFile = async (filePath) => {
  try {
    const data = await fs.readFile(filePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error(`Error reading file ${filePath}:`, error);
    throw new Error('Error reading file');
  }
};

const writeJsonFile = async (filePath, data) => {
  try {
    await fs.writeFile(filePath, JSON.stringify(data, null, 2), 'utf8');
  } catch (error) {
    console.error(`Error writing to file ${filePath}:`, error);
    throw new Error('Error writing to file');
  }
};

// ===== User Routes =====

// Pobieranie użytkowników
app.get('/users.json', asyncHandler(async (req, res) => {
  const data = await readJsonFile(USERS_FILE_PATH);
  res.json(data);
}));

// Aktualizacja użytkowników
app.put('/users.json', asyncHandler(async (req, res) => {
  await writeJsonFile(USERS_FILE_PATH, req.body);
  res.json({ success: true });
}));

// ===== Quiz Routes =====

// Pobieranie wszystkich quizów (stara ścieżka dla kompatybilności)
app.get('/quiz.json', asyncHandler(async (req, res) => {
  const data = await readJsonFile(QUIZ_FILE_PATH);
  res.json(data);
}));

// Aktualizacja pliku quiz.json (stara ścieżka dla kompatybilności)
app.put('/quiz.json', asyncHandler(async (req, res) => {
  await writeJsonFile(QUIZ_FILE_PATH, req.body);
  res.json({ success: true });
}));

// Pobieranie wszystkich quizów
app.get('/quiz', asyncHandler(async (req, res) => {
  const data = await readJsonFile(QUIZ_FILE_PATH);
  
  // Dodawanie opcjonalnych filtrów
  const { category, difficulty, search } = req.query;
  
  if (!category && !difficulty && !search) {
    return res.json(data);
  }
  
  let filteredQuizzes = [...data.quizzes];
  
  if (category) {
    filteredQuizzes = filteredQuizzes.filter(q => q.category === category);
  }
  
  if (difficulty) {
    filteredQuizzes = filteredQuizzes.filter(q => q.difficulty === difficulty);
  }
  
  if (search) {
    const searchLower = search.toLowerCase();
    filteredQuizzes = filteredQuizzes.filter(q => 
      q.title.toLowerCase().includes(searchLower) || 
      (q.description && q.description.toLowerCase().includes(searchLower))
    );
  }
  
  res.json({ quizzes: filteredQuizzes });
}));

// Pobieranie konkretnego quizu po ID
app.get('/quiz/:id', asyncHandler(async (req, res) => {
  const data = await readJsonFile(QUIZ_FILE_PATH);
  const quizId = parseInt(req.params.id, 10);
  
  if (isNaN(quizId)) {
    return res.status(400).json({ error: 'ID quizu musi być liczbą' });
  }
  
  const quiz = data.quizzes.find(q => q.id === quizId);
  
  if (!quiz) {
    return res.status(404).json({ error: 'Quiz nie został znaleziony' });
  }
  
  res.json(quiz);
}));

// Dodawanie nowego quizu
app.post('/quiz', asyncHandler(async (req, res) => {
  const data = await readJsonFile(QUIZ_FILE_PATH);
  
  if (!req.body.title || !req.body.questions) {
    return res.status(400).json({ 
      error: 'Brakuje wymaganych pól. Wymagane pola: title, questions' 
    });
  }
  
  // Znajdź najwyższe ID i dodaj 1
  const maxId = data.quizzes.length > 0 
    ? Math.max(...data.quizzes.map(q => q.id)) 
    : 0;
  
  const newQuiz = {
    id: maxId + 1,
    createdAt: new Date().toISOString(),
    ...req.body
  };
  
  data.quizzes.push(newQuiz);
  
  await writeJsonFile(QUIZ_FILE_PATH, data);
  
  res.status(201).json(newQuiz);
}));

// Aktualizacja quizu
app.put('/quiz/:id', asyncHandler(async (req, res) => {
  const data = await readJsonFile(QUIZ_FILE_PATH);
  const quizId = parseInt(req.params.id, 10);
  
  if (isNaN(quizId)) {
    return res.status(400).json({ error: 'ID quizu musi być liczbą' });
  }
  
  const quizIndex = data.quizzes.findIndex(q => q.id === quizId);
  if (quizIndex === -1) {
    return res.status(404).json({ error: 'Quiz nie został znaleziony' });
  }
  
  // Zachowaj dane, które nie powinny być zmieniane
  const createdAt = data.quizzes[quizIndex].createdAt;
  
  data.quizzes[quizIndex] = {
    ...data.quizzes[quizIndex],
    ...req.body,
    id: quizId, // zachowaj oryginalne ID
    createdAt, // zachowaj oryginalną datę utworzenia
    lastModified: new Date().toISOString() // aktualizuj datę modyfikacji
  };
  
  await writeJsonFile(QUIZ_FILE_PATH, data);
  
  res.json(data.quizzes[quizIndex]);
}));

// Usuwanie quizu
app.delete('/quiz/:id', asyncHandler(async (req, res) => {
  const data = await readJsonFile(QUIZ_FILE_PATH);
  const quizId = parseInt(req.params.id, 10);
  
  if (isNaN(quizId)) {
    return res.status(400).json({ error: 'ID quizu musi być liczbą' });
  }
  
  const quizIndex = data.quizzes.findIndex(q => q.id === quizId);
  if (quizIndex === -1) {
    return res.status(404).json({ error: 'Quiz nie został znaleziony' });
  }
  
  data.quizzes.splice(quizIndex, 1);
  
  await writeJsonFile(QUIZ_FILE_PATH, data);
  
  res.json({ success: true, message: 'Quiz został usunięty' });
}));

// Obsługa błędów
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({ 
    error: 'Wystąpił błąd po stronie serwera', 
    details: process.env.NODE_ENV === 'development' ? err.message : undefined 
  });
});

// Obsługa nieistniejących ścieżek
app.use((req, res) => {
  res.status(404).json({ error: 'Nie znaleziono zasobu' });
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});