import React, { memo, useMemo } from 'react';
import { Link } from 'react-router-dom';
import '../styles/LandingPage.css';

// Hero section component
const HeroSection = memo(() => (
  <section className="hero-section">
    <h1>Odkryj Świat Quizów z CyberQuiz</h1>
    <div className="hero-image">
      <img 
        src="https://images.unsplash.com/photo-1550439062-609e1531270e?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
        alt="CyberQuiz Platform"
        loading="eager" // Priorytetowe ładowanie głównego obrazu
      />
    </div>
    <div className="hero-buttons">
      <Link to="/login" className="btn btn-primary">Zaloguj się</Link>
      <Link to="/register" className="btn btn-secondary">Zarejestruj się</Link>
    </div>
  </section>
));

// Feature card component
const FeatureCard = memo(({ image, title, description, reverse }) => (
  <div className={`feature-card ${reverse ? 'reverse' : ''}`}>
    {!reverse && (
      <img 
        src={image}
        alt={title}
        loading="lazy" // Leniwe ładowanie obrazów sekcji Features
      />
    )}
    <div className="feature-content">
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
    {reverse && (
      <img 
        src={image}
        alt={title}
        loading="lazy"
      />
    )}
  </div>
));

// Features section component
const FeaturesSection = memo(() => (
  <section className="features-section">
    <FeatureCard
      image="https://images.unsplash.com/photo-1522199755839-a2bacb67c546?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80"
      title="Dostępne na Wszystkich Urządzeniach"
      description="CyberQuiz działa płynnie na każdym urządzeniu, od komputerów po smartfony. Ucz się w sposób, który najbardziej Ci odpowiada!"
    />
    <FeatureCard
      image="https://images.unsplash.com/photo-1531498860502-7c67cf02f657?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80"
      title="Dołącz do Społeczności"
      description="Zarejestruj się już dziś i dołącz do tysięcy innych użytkowników, którzy rozwijają się razem!"
      reverse
    />
  </section>
));

// Testimonial card component
const TestimonialCard = memo(({ text, author }) => (
  <div className="testimonial-card">
    <p>"{text}"</p>
    <span className="author">- {author}</span>
  </div>
));

// Testimonials section component
const TestimonialsSection = memo(() => {
  const testimonials = useMemo(() => [
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
  ], []);

  return (
    <section className="testimonials-section">
      <h2>Co Mówią Nasi Użytkownicy</h2>
      <div className="testimonials-grid">
        {testimonials.map(testimonial => (
          <TestimonialCard
            key={testimonial.id}
            text={testimonial.text}
            author={testimonial.author}
          />
        ))}
      </div>
    </section>
  );
});

// CTA section component
const CTASection = memo(() => (
  <section className="cta-section">
    <h2>Gotowy na Wyjątkowe Quizy?</h2>
    <p>Dołącz do nas już teraz i zacznij swoją cyfrową przygodę!</p>
    <Link to="/register" className="btn btn-primary">Zarejestruj się</Link>
  </section>
));

// Footer component
const Footer = memo(() => (
  <footer className="landing-footer">
    <p>© {new Date().getFullYear()} CyberQuiz. All rights reserved.</p>
  </footer>
));

// Main component
const LandingPage = () => {
  return (
    <div className="landing-container">
      <HeroSection />
      <FeaturesSection />
      <TestimonialsSection />
      <CTASection />
      <Footer />
    </div>
  );
};

export default LandingPage;