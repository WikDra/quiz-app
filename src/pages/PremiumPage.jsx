import React from 'react';
import StripeCheckout from '../components/StripeCheckout';
import { useAuth } from '../context/AuthContext';
import '../styles/PremiumPage.css';

const PremiumPage = () => {
  const { user } = useAuth();

  // Ensure VITE_STRIPE_PREMIUM_PLAN_ID is set in your .env file
  const premiumPriceId = import.meta.env.VITE_STRIPE_PREMIUM_PLAN_ID;

  if (!premiumPriceId) {
    console.error("Stripe Premium Plan ID is not configured. Please set VITE_STRIPE_PREMIUM_PLAN_ID in your .env file.");
    // Optionally, render a message to the user or redirect
    return (
      <div className="premium-page-container">
        <div className="premium-content">
          <h1>Przejdź na Premium</h1>
          <p className="error-message">
            Przepraszamy, konfiguracja płatności jest obecnie niedostępna. 
            Prosimy spróbować później lub skontaktować się z pomocą techniczną.
          </p>
        </div>
      </div>
    );
  }

  if (user?.has_premium_access) {
    return (
      <div className="premium-page-container">
        <div className="premium-content">
          <h1>Jesteś już użytkownikiem Premium!</h1>
          <p>Dziękujemy za wsparcie. Ciesz się wszystkimi korzyściami płynącymi z subskrypcji.</p>
          {/* Możesz tutaj dodać link do strony głównej lub specjalnej strony dla użytkowników premium */}
        </div>
      </div>
    );
  }

  return (
    <div className="premium-page-container">
      <div className="premium-content">
        <h1>Przejdź na Premium</h1>
        <p>Odblokuj wszystkie funkcje i ciesz się pełnią możliwości CyberQuiz!</p>
        
        <div className="premium-features">
          <h2>Co zyskujesz?</h2>
          <ul>
            <li>✅ Dostęp do wszystkich quizów, w tym ekskluzywnych.</li>
            <li>✅ Brak reklam.</li>
            <li>✅ Zaawansowane statystyki i analizy Twoich postępów.</li>
            <li>✅ Specjalne odznaki i wyróżnienia profilu.</li>
            <li>✅ Priorytetowe wsparcie techniczne.</li>
          </ul>
        </div>

        <div className="checkout-section">
          <h2>Wybierz plan i zacznij już dziś!</h2>
          <StripeCheckout priceId={premiumPriceId} />
        </div>

        <p className="terms-info">
          Klikając przycisk płatności, akceptujesz nasze Warunki Świadczenia Usług oraz Politykę Prywatności. 
          Subskrypcja odnawia się automatycznie, chyba że zostanie anulowana.
        </p>
      </div>
    </div>
  );
};

export default PremiumPage;
