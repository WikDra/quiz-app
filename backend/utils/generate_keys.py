"""
Skrypt do generowania kluczy bezpieczeństwa dla aplikacji
"""
import os
import secrets
import base64

def generate_key(bytes_length=32):
    """Generuje bezpieczny klucz o podanej długości"""
    return base64.urlsafe_b64encode(secrets.token_bytes(bytes_length)).decode('utf-8')

if __name__ == "__main__":
    print("\nGenerowanie kluczy bezpieczeństwa dla aplikacji Quiz App\n")
    
    # Generowanie kluczy
    secret_key = generate_key()
    jwt_secret_key = generate_key()
    
    print("SECRET_KEY=" + secret_key)
    print("JWT_SECRET_KEY=" + jwt_secret_key)
    
    print("\nDodaj te klucze do twojego pliku .env lub bezpośrednio do zmiennych środowiskowych.")
    
    # Sprawdź czy plik .env już istnieje i czy zawiera te klucze
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    
    if os.path.exists(env_path):
        print("\nPlik .env już istnieje. Możesz dodać powyższe klucze ręcznie do tego pliku.")
    else:
        create_env = input("\nCzy chcesz utworzyć plik .env z tymi kluczami? (t/n): ")
        if create_env.lower() == 't':
            with open(env_path, 'w') as env_file:
                env_file.write(f"SECRET_KEY={secret_key}\n")
                env_file.write(f"JWT_SECRET_KEY={jwt_secret_key}\n")
            print(f"Plik .env został utworzony w: {env_path}")
        else:
            print("Nie utworzono pliku .env. Pamiętaj, aby dodać klucze do środowiska.")
