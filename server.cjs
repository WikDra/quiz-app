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
app.get('/quiz.json', async (req, res) => {
  try {
    const data = await fs.readFile(path.join(__dirname, 'public', 'users.json'), 'utf8');
    res.json(JSON.parse(data));
  } catch (error) {
    res.status(500).json({ error: 'Błąd podczas odczytu pliku' });
  }
});

// Endpoint do aktualizacji użytkowników
app.put('/quiz.json', async (req, res) => {
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
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});