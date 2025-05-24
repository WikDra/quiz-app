# 💳 Stripe Integration Setup Guide (KOMPLETNA IMPLEMENTACJA)

Ten przewodnik opisuje pełną integrację płatności Stripe w Quiz App, która **już została zaimplementowana** z zaawansowanymi funkcjami obsługi płatności.

## ✅ **ZAIMPLEMENTOWANE FUNKCJE**

### **🏆 Core Stripe Features:**
- ✅ **Checkout Sessions:** Bezpieczne sesje płatności
- ✅ **Webhooks:** `customer.subscription.created/updated/deleted`  
- ✅ **Failed Payments:** Obsługa `invoice.payment_failed`, `payment_intent.payment_failed`
- ✅ **Retry Logic:** 3 próby z automatyczną dezaktywacją premium
- ✅ **Admin Dashboard:** Monitoring failed payments
- ✅ **Database Tracking:** Model `StripeSubscription` z `failed_payment_count`

### **🔧 Advanced Features:**
- ✅ **Webhook Security:** Signature verification
- ✅ **Idempotency:** Duplicate event protection
- ✅ **Error Handling:** Comprehensive logging i error responses
- ✅ **CORS Support:** Frontend integration

---

## 🚀 Setup Steps

### **1. Utwórz konto Stripe**

1. Zarejestruj się na [stripe.com](https://stripe.com)
2. Potwierdź email i zaloguj się do Dashboard

### **2. Pobierz API Keys**

1. W [Stripe Dashboard](https://dashboard.stripe.com/) → **Developers > API keys**
2. Skopiuj:
   - **Publishable Key** (`pk_test_...`)
   - **Secret Key** (`sk_test_...`)

### **3. Utwórz Produkt i Cenę**

1. **Products** → **Add Product**
2. Konfiguracja:
   - **Name:** "Quiz App Premium Subscription"
   - **Price:** $9.99 (lub inna kwota)
   - **Billing:** Recurring - Monthly
3. **Zapisz Price ID** (format: `price_xxxxx`)

### **4. Skonfiguruj Webhooks**

#### **Opcja A: Stripe CLI (Development)**

1. **Zainstaluj Stripe CLI:** [stripe.com/docs/stripe-cli](https://stripe.com/docs/stripe-cli)

2. **Zaloguj się:**
   ```bash
   stripe login
   ```

3. **Uruchom listener dla webhook'ów:**
   ```bash
   stripe listen --forward-to localhost:5000/stripe/webhook
   ```
   **Skopiuj webhook signing secret** z output'u

4. **Testuj eventy:**
   ```bash
   stripe trigger checkout.session.completed
   stripe trigger invoice.payment_failed
   stripe trigger customer.subscription.deleted
   ```

#### **Opcja B: Dashboard Webhook (Production)**

1. **Developers** → **Webhooks** → **Add endpoint**
2. **URL:** `https://yourdomain.com/stripe/webhook`
3. **Events to send:**
   - `customer.subscription.created`
   - `customer.subscription.updated` 
   - `customer.subscription.deleted`
   - `invoice.payment_failed` ⚠️ **WAŻNE dla failed payments**
   - `payment_intent.payment_failed`
4. **Skopiuj Webhook Secret**

---

## 🔧 **Environment Variables**

Zaktualizuj plik `.env`:

```env
# Stripe Keys (Test Mode)
STRIPE_SECRET_KEY=sk_test_51xxxxx...
STRIPE_PUBLISHABLE_KEY=pk_test_51xxxxx...
STRIPE_WEBHOOK_SECRET=whsec_xxxxx...

# Product Configuration
STRIPE_PREMIUM_PLAN_ID=price_xxxxx  # ID z kroku 3

# Frontend Keys (w .env.local dla frontendu)
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_51xxxxx...
VITE_STRIPE_PREMIUM_PLAN_ID=price_xxxxx
```

---

## 🧪 **Testing Integration**

### **1. Development Testing**

2. **Start the Event Listener**
   ```bash
   # Start forwarding events to your local server
   stripe listen --forward-to localhost:5000/api/stripe/webhook
   ```

3. **Test Different Webhook Events**
   ```bash
   # Test successful checkout completion
   stripe trigger checkout.session.completed \
     --add checkout_session:client_reference_id=123 \
     --add checkout_session:customer=cus_xxx

   # Test subscription deletion
   stripe trigger customer.subscription.deleted \
     --add subscription:customer=cus_xxx

   # Test failed payment
   stripe trigger invoice.payment_failed \
     --add invoice:customer=cus_xxx
   ```

4. **Monitor Event Processing**
   - Watch the terminal running `stripe listen` for forwarded events
   - Check your application logs for webhook processing
   - Verify database updates in the user table

#### Manual Testing with the Test Interface

1. Navigate to `/test-premium` in your browser
2. Use the test interface to:
   - Trigger test purchases
   - Toggle premium status
   - View subscription details

#### Troubleshooting Testing Issues

1. **Webhook Errors**
   - Verify webhook secret in `.env` matches the one from Stripe CLI
   - Check application logs for detailed error messages
   - Ensure your local server is running and accessible

2. **Database Updates**
   - Use the SQL console to verify user premium status:
     ```sql
     SELECT id, email, has_premium_access, premium_since 
     FROM users 
     WHERE has_premium_access = 1;
     ```

3. **Event Processing**
   - Set logging level to DEBUG in your Flask app
   - Monitor the Stripe CLI output for request/response details
   - Use the Stripe Dashboard Events section to verify event delivery

### 7. Production Deployment

When deploying to production:

1. Replace test API keys with production keys
2. Update webhook endpoint URL to your production server
3. Configure proper webhook signing secret
4. Test the complete flow in production environment using real cards

> **Note**: Always use test API keys and test card numbers for development. Never use real card data in development environment.

## Troubleshooting

### Common Issues

1. **Webhook not working**:
   - Check if `STRIPE_WEBHOOK_SECRET` is correct in your `.env` file
   - Use Stripe CLI to debug webhook issues:
     ```bash
     # Start webhook forwarding in verbose mode
     stripe listen --forward-to localhost:5000/api/stripe/webhook --log-level debug
     
     # In another terminal, trigger test events
     stripe trigger checkout.session.completed
     ```
   - Check logs for webhook verification errors
   - If using ngrok, verify your webhook URL is accessible from the internet
   - Check the Stripe Dashboard for webhook delivery attempts and failures

2. **Payment successful but premium not activated**:
   - Check application logs for errors in the webhook handler
   - Verify that `client_reference_id` is being properly passed to Stripe during checkout

3. **Stripe configuration not loaded**:
   - Make sure you've run the setup script and restarted your servers

### Debugging

The application includes several debugging tools:

- `AuthStateLogger` component logs authentication state changes, including premium status
- The `/test-premium` route allows manual toggling of premium status for testing
- Check your browser console and server logs for any error messages

#### Debug Methods:

1. **Using Stripe CLI**:
   ```bash
   # Terminal 1: Start webhook forwarding
   stripe listen --forward-to localhost:5000/stripe/webhook
   
   # Terminal 2: Trigger specific events
   stripe trigger checkout.session.completed
   stripe trigger customer.subscription.deleted
   ```

2. **Using Test Premium Page**:
   - Navigate to `/test-premium` in your browser
   - Use the toggle button to manually switch premium status
   - Check the activation date display
   - Test webhook simulation buttons

3. **Check Server Logs**:
   - Watch the Flask server output for webhook events
   - Look for "Processing webhook event type" messages
   - Verify premium status changes in the database

## Production Deployment

When deploying to production:

1. Update the webhook endpoint URL in Stripe to your production URL
2. Get new webhook secrets for your production environment
3. Ensure all Stripe environment variables are properly set in your production environment
4. Consider using Stripe's live mode keys instead of test mode keys

## Additional Resources

- [Stripe API Documentation](https://stripe.com/docs/api)
- [Handling Webhook Events](https://stripe.com/docs/webhooks)
- [Testing Stripe Payments](https://stripe.com/docs/testing)