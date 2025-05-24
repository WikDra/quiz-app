# Stripe Integration Setup Guide

This guide will help you set up Stripe payment processing for the Quiz App premium subscription feature. The core implementation is already in place, but you need to configure your Stripe account and environment variables correctly.

## Prerequisites

1. A Stripe account - sign up at [stripe.com](https://stripe.com) if you don't have one.
2. Access to the Stripe Dashboard to obtain API keys and set up webhooks.

## Setup Steps

### 1. Obtain API Keys from Stripe

1. Log in to your [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to Developers > API keys
3. Make note of your **Publishable Key** and **Secret Key**

### 2. Create a Product and Price in Stripe

1. In your Stripe Dashboard, go to Products > Add Product
2. Create a product for your premium subscription:
   - Name: "Quiz App Premium Subscription"
   - Price: Set your desired price (e.g., $9.99 per month)
   - Billing: Set to recurring (monthly or annual)
3. After creating the product, Stripe will generate a **Price ID** (starts with `price_`). Save this ID.

### 3. Set Up Webhook Endpoints

#### Option A: Using Stripe CLI (Recommended for Development)

1. Download and install [Stripe CLI](https://stripe.com/docs/stripe-cli)

2. Log in to your Stripe account through CLI:
   ```bash
   stripe login
   ```

3. Start forwarding events to your local server:
   ```bash
   stripe listen --forward-to localhost:5000/api/stripe/webhook
   ```
   This will provide you with a webhook signing secret. Save this secret in your `.env` file.

4. In a separate terminal, you can trigger test events:
   ```bash
   stripe trigger payment_intent.succeeded
   stripe trigger checkout.session.completed
   stripe trigger customer.subscription.deleted
   ```

#### Option B: Using ngrok (Alternative Method)

1. In Stripe Dashboard, go to Developers > Webhooks
2. Click "Add Endpoint"
3. Use [ngrok](https://ngrok.com/) to expose your local server:
   ```bash
   ngrok http 5000
   ```
4. Use the generated ngrok URL as your webhook endpoint: `https://your-ngrok-url/api/stripe/webhook`
5. Select events to listen for:
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `customer.subscription.deleted`
6. After creating the webhook, Stripe will provide a **Webhook Secret**. Save this value.

### 4. Configure Environment Variables

Update your `.env` file with the following values:

```
# Stripe Configuration
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
VITE_STRIPE_PREMIUM_PLAN_ID=price_your_price_id
```

> **IMPORTANT**: Replace the placeholder values with your actual Stripe keys and IDs.

### 5. Run the Configuration Setup

Execute the security setup script to ensure all variables are properly configured:

```bash
cd backend
python -m utils.setup_security
```

### 6. Testing the Integration

#### Local Development Testing with Stripe CLI

1. **Setup Testing Environment**
   ```bash
   # Install Stripe CLI (if not already installed)
   # Using Chocolatey on Windows
   choco install stripe-cli
   
   # Login to your Stripe account
   stripe login
   ```

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