import React, { useState } from 'react';
import StripeCheckout from '../components/StripeCheckout';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../utils/constants';
import '../styles/PremiumPage.css';

const PremiumPage = () => {
  const { user } = useAuth();
  const [showOfflinePaymentForm, setShowOfflinePaymentForm] = useState(false);
  const [offlinePaymentData, setOfflinePaymentData] = useState({
    amount: '29.99',
    paymentMethod: '',
    referenceNumber: '',
    description: 'Premium subscription payment'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState('');

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

  const handleOfflinePaymentChange = (e) => {
    const { name, value } = e.target;
    setOfflinePaymentData({
      ...offlinePaymentData,
      [name]: value
    });
  };

  const handleOfflinePaymentSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setMessage('');

    try {
      const response = await fetch(`${API_BASE_URL}/users/offline-payment-request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(offlinePaymentData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Network response was not ok');
      }

      const responseData = await response.json();
      setMessage(`Prośba o płatność offline została wysłana pomyślnie. ID żądania: ${responseData.request_id}`);
      setShowOfflinePaymentForm(false);
      setOfflinePaymentData({
        amount: '29.99',
        paymentMethod: '',
        referenceNumber: '',
        description: 'Premium subscription payment'
      });
    } catch (error) {
      setMessage(`Wystąpił błąd podczas wysyłania prośby: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

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

        <div className="offline-payment-section">
          <h2>Lub poproś o płatność offline</h2>
          <p>Jeśli wolisz płacić przelewem lub gotówką, wyślij prośbę do administratora.</p>
          
          <button 
            className="btn-secondary"
            onClick={() => setShowOfflinePaymentForm(!showOfflinePaymentForm)}
          >
            {showOfflinePaymentForm ? 'Anuluj' : 'Poproś o płatność offline'}
          </button>

          {showOfflinePaymentForm && (
            <form onSubmit={handleOfflinePaymentSubmit} className="offline-payment-form">
              <div className="form-group">
                <label htmlFor="amount">Kwota (PLN):</label>
                <input
                  type="number"
                  id="amount"
                  name="amount"
                  step="0.01"
                  min="0"
                  placeholder="29.99"
                  value={offlinePaymentData.amount}
                  onChange={handleOfflinePaymentChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="paymentMethod">Metoda płatności:</label>
                <select
                  id="paymentMethod"
                  name="paymentMethod"
                  value={offlinePaymentData.paymentMethod}
                  onChange={handleOfflinePaymentChange}
                  required
                >
                  <option value="">Wybierz metodę</option>
                  <option value="bank_transfer">Przelew bankowy</option>
                  <option value="cash">Gotówka</option>
                  <option value="blik">BLIK</option>
                  <option value="other">Inna</option>
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="referenceNumber">Numer referencyjny (opcjonalnie):</label>
                <input
                  type="text"
                  id="referenceNumber"
                  name="referenceNumber"
                  placeholder="np. numer przelewu"
                  value={offlinePaymentData.referenceNumber}
                  onChange={handleOfflinePaymentChange}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="description">Opis:</label>
                <textarea
                  id="description"
                  name="description"
                  placeholder="Dodatkowe informacje o płatności"
                  value={offlinePaymentData.description}
                  onChange={handleOfflinePaymentChange}
                  required
                ></textarea>
              </div>
              
              <button type="submit" className="btn-primary" disabled={isSubmitting}>
                {isSubmitting ? 'Wysyłanie...' : 'Wyślij prośbę o płatność'}
              </button>
            </form>
          )}

          {message && (
            <div className={`payment-message ${message.includes('błąd') ? 'error' : 'success'}`}>
              {message}
            </div>
          )}
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
