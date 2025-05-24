import stripe
from flask import request, jsonify, current_app
from flask_restful import Resource
from flask import current_app
from .models import Payment, db  

class CreatePaymentIntent(Resource):
    def post(self):
        data = request.json
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(data['amount']) * 100,  # Kwota w centach
                currency=data.get('currency', 'usd'),
                payment_method_types=["card"],
            )
            return {
                'client_secret': intent['client_secret'],
                'payment_intent_id': intent['id']
            }, 200
        except Exception as e:
            return {'error': str(e)}, 400

class StripeWebhook(Resource):
    def post(self):
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except ValueError:
            return {'message': 'Invalid payload'}, 400
        except stripe.error.SignatureVerificationError:
            return {'message': 'Invalid signature'}, 400

        if event['type'] == 'payment_intent.succeeded':
            intent = event['data']['object']
            amount = intent['amount'] / 100

            # Zapis płatności do bazy danych
            payment = Payment(
                stripe_payment_intent_id=intent['id'],
                amount=amount,
                status='succeeded'
            )
            db.session.add(payment)
            db.session.commit()
            print(f"Zapisano płatność: {intent['id']}")

        return {'status': 'success'}, 200
class create_payment(Resource):
    def post(self):
        data = request.json

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": data.get("currency", "usd"),
                        "product_data": {
                            "name": data.get("description", "Transaction"),
                        },
                        "unit_amount": int(float(data["amount"]) * 100),  # w centach
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
        )

            return {"checkout_url": session.url,"session_id": session.id}, 200

        except Exception as e:
            return {"error": str(e)}, 400