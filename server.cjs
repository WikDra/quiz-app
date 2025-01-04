const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Endpoint do pobierania użytkowników
app.get('/users.json', async (req, res) => {
  try {
    const data = await fs.readFile(path.join(__dirname, 'public', 'users.json'), 'utf8');
    res.json(JSON.parse(data));
  } catch (error) {
    res.status(500).json({ error: 'Błąd podczas odczytu pliku' });
  }
});

// Endpoint do aktualizacji użytkowników
app.put('/users.json', async (req, res) => {
  try {
    await fs.writeFile(
      path.join(__dirname, 'public', 'users.json'),
      JSON.stringify(req.body, null, 2)
    );
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Błąd podczas zapisu pliku' });
  }
});
// Endpoint do pobierania quizów
app.get('/quiz.json', async (req, res) => {
  try {
    const data = await fs.readFile(path.join(__dirname, 'public', 'quiz.json'), 'utf8');
    res.json(JSON.parse(data));
  } catch (error) {
    res.status(500).json({ error: 'Błąd podczas odczytu pliku quizów' });
  }
});

// Endpoint do aktualizacji quizów
app.put('/quiz.json', async (req, res) => {
  try {
    await fs.writeFile(
      path.join(__dirname, 'public', 'quiz.json'),
      JSON.stringify(req.body, null, 2)
    );
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Błąd podczas zapisu pliku quizów' });
  }
});
// Endpoint do pobierania wszystkich quizów
app.get('/quiz', async (req, res) => {
  try {
    const data = await fs.readFile(path.join(__dirname, 'public', 'quiz.json'), 'utf8');
    res.json(JSON.parse(data));
  } catch (error) {
    res.status(500).json({ error: 'Błąd podczas odczytu pliku quizów' });
  }
});

// Endpoint do pobierania konkretnego quizu po ID
app.get('/quiz/:id', async (req, res) => {
  try {
    const data = await fs.readFile(path.join(__dirname, 'public', 'quiz.json'), 'utf8');
    const quizzes = JSON.parse(data).quizzes;
    const quiz = quizzes.find(q => q.id === parseInt(req.params.id));
    
    if (!quiz) {
      return res.status(404).json({ error: 'Quiz nie został znaleziony' });
    }
    
    res.json(quiz);
  } catch (error) {
    res.status(500).json({ error: 'Błąd podczas odczytu pliku quizów' });
  }
});

// Endpoint do dodawania nowego quizu
app.post('/quiz', async (req, res) => {
  try {
    const data = await fs.readFile(path.join(__dirname, 'public', 'quiz.json'), 'utf8');
    const quizData = JSON.parse(data);
    
    // Znajdź najwyższe ID i dodaj 1
    const maxId = Math.max(...quizData.quizzes.map(q => q.id), 0);
    const newQuiz = {
      id: maxId + 1,
      ...req.body
    };
    
    quizData.quizzes.push(newQuiz);
    
    await fs.writeFile(
      path.join(__dirname, 'public', 'quiz.json'),
      JSON.stringify(quizData, null, 2)
    );
    
    res.status(201).json(newQuiz);
  } catch (error) {
    res.status(500).json({ error: 'Błąd podczas dodawania quizu' });
  }
});

// Endpoint do aktualizacji quizu
app.put('/quiz/:id', async (req, res) => {
  try {
    const data = await fs.readFile(path.join(__dirname, 'public', 'quiz.json'), 'utf8');
    const quizData = JSON.parse(data);
    const quizId = parseInt(req.params.id);
    
    const quizIndex = quizData.quizzes.findIndex(q => q.id === quizId);
    if (quizIndex === -1) {
      return res.status(404).json({ error: 'Quiz nie został znaleziony' });
    }
    
    quizData.quizzes[quizIndex] = {
      ...quizData.quizzes[quizIndex],
      ...req.body,
      id: quizId // zachowaj oryginalne ID
    };
    
    await fs.writeFile(
      path.join(__dirname, 'public', 'quiz.json'),
      JSON.stringify(quizData, null, 2)
    );
    
    res.json(quizData.quizzes[quizIndex]);
  } catch (error) {
    res.status(500).json({ error: 'Błąd podczas aktualizacji quizu' });
  }
});

// Endpoint do usuwania quizu
app.delete('/quiz/:id', async (req, res) => {
  try {
    const data = await fs.readFile(path.join(__dirname, 'public', 'quiz.json'), 'utf8');
    const quizData = JSON.parse(data);
    const quizId = parseInt(req.params.id);
    
    const quizIndex = quizData.quizzes.findIndex(q => q.id === quizId);
    if (quizIndex === -1) {
      return res.status(404).json({ error: 'Quiz nie został znaleziony' });
    }
    
    quizData.quizzes.splice(quizIndex, 1);
    
    await fs.writeFile(
      path.join(__dirname, 'public', 'quiz.json'),
      JSON.stringify(quizData, null, 2)
    );
    
    res.json({ success: true, message: 'Quiz został usunięty' });
  } catch (error) {
    res.status(500).json({ error: 'Błąd podczas usuwania quizu' });
  }
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});