#!/usr/bin/env python
"""
Script to update the Stripe webhook secret in .env file
"""
import os
import re
from dotenv import load_dotenv, set_key

def update_webhook_secret():
    """Update the Stripe webhook secret in .env file"""
    # Get the path to the .env file
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if not os.path.exists(dotenv_path):
        print(f"Error: .env file not found at {dotenv_path}")
        return
    
    # Load current environment variables
    load_dotenv(dotenv_path)
    
    current_webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    
    # Show current value
    print("\nCurrent Stripe Webhook Secret Configuration:")
    print(f"STRIPE_WEBHOOK_SECRET={current_webhook_secret}")
    
    if current_webhook_secret.startswith('whsec_'):
        print("\nCurrent webhook secret appears to be valid (starts with 'whsec_').")
        proceed = input("Do you want to replace it anyway? (y/N): ").lower() == 'y'
        if not proceed:
            print("No changes made to webhook secret.")
            return
    else:
        print("\nCurrent webhook secret is NOT valid. Webhook secrets must start with 'whsec_'.")
        print("You need to get the webhook secret from your Stripe dashboard:")
        print("1. Go to https://dashboard.stripe.com/webhooks")
        print("2. Select your webhook endpoint")
        print("3. Click 'Reveal secret' to get your webhook signing secret")
    
    # Get new webhook secret
    new_webhook_secret = input("\nEnter your Stripe webhook secret (starts with 'whsec_'): ")
    
    if not new_webhook_secret.startswith('whsec_'):
        print("Error: Invalid webhook secret. Webhook secrets should start with 'whsec_'.")
        retry = input("Try again? (y/N): ").lower() == 'y'
        if not retry:
            print("No changes made to webhook secret.")
            return
        else:
            new_webhook_secret = input("Enter your Stripe webhook secret (starts with 'whsec_'): ")
            if not new_webhook_secret.startswith('whsec_'):
                print("Error: Invalid webhook secret. No changes made.")
                return
    
    # Update the .env file
    set_key(dotenv_path, 'STRIPE_WEBHOOK_SECRET', new_webhook_secret)
    print(f"\nWebhook secret updated successfully in {dotenv_path}")
    print("\nYou need to restart your application for the changes to take effect.")

if __name__ == "__main__":
    update_webhook_secret()