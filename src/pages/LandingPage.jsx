import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/LandingPage.css';

const LandingPage = () => {
  const testimonials = [
    {
      id: 1,
      text: "Aplikacja to niesamowite narzędzie do nauki i rozwoju w branży cyberowej.",
      author: "Michał Kowalski"
    },
    {
      id: 2,
      text: "Świat CyberQuiz może wydać się nowemu osoby trudny, ale to przyjemna nauka!",
      author: "Anna Nowak"
    },
    {
      id: 3,
      text: "Świetna społeczność i ciekawe quizy. Zawsze jest coś nowego!",
      author: "Piotr Wiśniewski"
    }
  ];

  return (
    <div className="landing-container">
      {/* Hero Section */}
      <section className="hero-section">
        <h1>Odkryj Świat Quizów z CyberQuiz</h1>
        <div className="hero-image">
          <img 
            src="https://images.unsplash.com/photo-1550439062-609e1531270e?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
            alt="CyberQuiz Platform"
          />
        </div>
        <div className="hero-buttons">
          <Link to="/login" className="btn btn-primary">Zaloguj się</Link>
          <Link to="/register" className="btn btn-secondary">Zarejestruj się</Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="feature-card">
          <img 
            src="https://images.unsplash.com/photo-1522199755839-a2bacb67c546?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80"
            alt="Dostępność"
          />
          <div className="feature-content">
            <h2>Dostępne na Wszystkich Urządzeniach</h2>
            <p>CyberQuiz działa płynnie na każdym urządzeniu, od komputerów po smartfony. Ucz się w sposób, który najbardziej Ci odpowiada!</p>
          </div>
        </div>

        <div className="feature-card reverse">
          <div className="feature-content">
            <h2>Dołącz do Społeczności</h2>
            <p>Zarejestruj się już dziś i dołącz do tysięcy innych użytkowników, którzy rozwijają się razem!</p>
          </div>
          <img 
            src="https://images.unsplash.com/photo-1531498860502-7c67cf02f657?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80"
            alt="Społeczność"
          />
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="testimonials-section">
        <h2>Co Mówią Nasi Użytkownicy</h2>
        <div className="testimonials-grid">
          {testimonials.map(testimonial => (
            <div key={testimonial.id} className="testimonial-card">
              <p>"{testimonial.text}"</p>
              <span className="author">- {testimonial.author}</span>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <h2>Gotowy na Wyjątkowe Quizy?</h2>
        <p>Dołącz do nas już teraz i zacznij swoją cyfrową przygodę!</p>
        <Link to="/register" className="btn btn-primary">Zarejestruj się</Link>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>© 2024 CyberQuiz. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default LandingPage;