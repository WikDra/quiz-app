import React, { useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './../styles/PaymentSuccessPage.css';
import { useAuth } from '../context/AuthContext';

function PaymentSuccessPage() {
  const location = useLocation();
  const { refreshUserState } = useAuth();

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    if (queryParams.get('subscription') === 'true') {
      // Refresh user data to get updated premium status
      if (refreshUserState) {
        console.log('Refreshing user state after successful payment');
        refreshUserState();
      }
    }
  }, [location, refreshUserState]);

  return (
    <div className="payment-success-container">
      <h1>Płatność zakończona sukcesem!</h1>
      <p>Dziękujemy za subskrypcję wersji premium.</p>
      <p>Twoje konto zostało zaktualizowane.</p>
      <Link to="/user-settings" className="btn-primary">
        Przejdź do ustawień konta
      </Link>
      <br />
      <Link to="/" className="btn-secondary">
        Powrót na stronę główną
      </Link>
    </div>
  );
}

export default PaymentSuccessPage;