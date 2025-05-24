import React from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import axios from '../utils/axiosConfig'; // Assuming you have an axios instance configured

// Make sure to call `loadStripe` outside of a component’s render to avoid
// recreating the `Stripe` object on every render.
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || 'YOUR_FALLBACK_STRIPE_PUBLISHABLE_KEY');

const CheckoutForm = ({ priceId, onSuccess, onError }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    if (!stripe || !elements) {
      // Stripe.js has not yet loaded.
      setError('Stripe.js has not loaded yet.');
      setLoading(false);
      return;
    }

    // const cardElement = elements.getElement(CardElement); // Not needed if redirecting immediately

    try {
      // Create a checkout session on your server
      const response = await axios.post('/stripe/create-checkout-session', { priceId });
      const session = response.data;

      // When the customer clicks on the button, redirect them to Checkout.
      const result = await stripe.redirectToCheckout({
        sessionId: session.sessionId,
      });

      if (result.error) {
        // If `redirectToCheckout` fails due to a browser or network
        // error, display the localized error message to your customer
        // using `result.error.message`.
        console.error('Stripe redirectToCheckout error:', result.error.message);
        setError(result.error.message);
        if (onError) onError(result.error.message);
      } else {
        // This part is unlikely to be reached if redirectToCheckout is successful,
        // as the browser will navigate away.
        if (onSuccess) onSuccess(session);
      }
    } catch (err) {
      console.error('Error creating checkout session or redirecting:', err);
      const errorMessage = err.response?.data?.error || err.message || 'An unexpected error occurred.';
      setError(errorMessage);
      if (onError) onError(errorMessage);
    }

    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '400px', margin: '20px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      <h4>Unlock Premium Features</h4>
      <p>Complete your payment to get access to all premium quizzes and features.</p>
      {/* 
        If you wanted to collect card details directly on your page before creating the session 
        (e.g., for a more integrated single-page app feel for certain payment methods),
        you would include <CardElement /> here. However, for redirectToCheckout with Stripe Checkout's hosted page,
        this is not strictly necessary as Stripe handles the card form securely on their page.
      */}
      {/* <div style={{ margin: '20px 0' }}>
        <CardElement options={{
          style: {
            base: {
              fontSize: '16px',
              color: '#424770',
              '::placeholder': {
                color: '#aab7c4',
              },
            },
            invalid: {
              color: '#9e2146',
            },
          },
        }} />
      </div> */}
      {error && <div style={{ color: 'red', marginTop: '15px', padding: '10px', border: '1px solid red', borderRadius: '4px' }}>{error}</div>}
      <button 
        type="submit" 
        disabled={!stripe || loading} 
        style={{
          marginTop: '20px', 
          padding: '12px 20px', 
          backgroundColor: loading ? '#ccc' : '#007bff', 
          color: 'white', 
          border: 'none', 
          borderRadius: '4px', 
          cursor: loading ? 'not-allowed' : 'pointer', 
          width: '100%',
          fontSize: '16px'
        }}
      >
        {loading ? 'Processing...' : 'Proceed to Payment'}
      </button>
    </form>
  );
};

const StripeCheckout = ({ priceId }) => {
  if (!import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY) {
    console.error("Stripe publishable key is not set. Ensure VITE_STRIPE_PUBLISHABLE_KEY is in your .env file.");
    return <p style={{color: 'red'}}>Payment system configuration error. Please contact support.</p>;
  }

  if (!priceId) {
    console.error("StripeCheckout component requires a priceId prop.");
    return <p style={{color: 'red'}}>Error: Payment Price ID not configured for this item.</p>;
  }

  const handleSuccess = (session) => {
    console.log('Stripe checkout session creation initiated:', session);
    // Redirection to Stripe's page is handled by redirectToCheckout.
    // Actual payment success confirmation is typically handled via webhooks on the backend
    // and then communicated to the frontend (e.g., by updating user state or redirecting to a success page).
  };

  const handleError = (error) => {
    console.error('Stripe checkout error:', error);
    // Consider displaying a user-friendly message here, e.g., using a toast notification system.
  };

  return (
    <Elements stripe={stripePromise}>
      <CheckoutForm priceId={priceId} onSuccess={handleSuccess} onError={handleError} />
    </Elements>
  );
};

export default StripeCheckout;
