# Instrukcje Bezpieczeństwa dla Quiz App

## Konfiguracja bezpiecznych kluczy

Aby zapewnić bezpieczeństwo aplikacji, należy skonfigurować bezpieczne klucze kryptograficzne. Kroki:

1. Uruchom skrypt konfiguracyjny bezpieczeństwa:

```bash
# Z katalogu głównego projektu
python backend/utils/setup_security.py

# LUB z katalogu backend
cd backend
python utils/setup_security.py
```

2. Skrypt przeprowadzi Cię przez proces:
   - Wygeneruje bezpieczne klucze dla `SECRET_KEY` i `JWT_SECRET_KEY`
   - Utworzy lub zaktualizuje plik `.env` z nowymi kluczami
   - Zachowa inne ustawienia w pliku `.env` (jeśli istnieją)
   - Pomoże skonfigurować Google OAuth (opcjonalnie)

## Konfiguracja Google OAuth (opcjonalnie)

Aby skonfigurować logowanie przez Google OAuth:

1. Przejdź do [Google Cloud Console](https://console.cloud.google.com/)
2. Utwórz nowy projekt lub wybierz istniejący
3. Włącz "Google Sign-In API" dla projektu
4. W sekcji "Credentials", utwórz nowe klucze OAuth Client ID:
   - Typ aplikacji: Web Application
   - Nazwij swoją aplikację (np. "Quiz App")
   - Dodaj autoryzowane URI przekierowań: `http://localhost:5000/api/auth/google/callback`
5. Zapisz wygenerowany `Client ID` oraz `Client Secret`
6. Uruchom skrypt konfiguracyjny i wprowadź te dane:
   ```bash
   python backend/utils/setup_security.py
   ```

## Uwagi dotyczące bezpieczeństwa

- **Plik `.env`** powinien być uwzględniony w `.gitignore` i nigdy nie powinien być przesłany do repozytorium
- W środowisku produkcyjnym, nie używaj lokalnego pliku `.env`, zamiast tego:
  - Skonfiguruj zmienne środowiskowe na poziomie systemu
  - Lub użyj bezpiecznego systemu zarządzania sekretami
- Regularnie rotuj klucze bezpieczeństwa (np. co 90 dni) uruchamiając skrypt ponownie

## Zabezpieczenia, które zostały zaimplementowane

1. Bezpieczne generowanie kluczy kryptograficznych używając `secrets` (entropia kryptograficzna)
2. Odpowiednia konfiguracja CORS dla bezpieczeństwa między domenowego (cross-origin)
3. Bezpieczna implementacja JWT z odpowiednimi czasami wygaśnięcia
4. Ograniczenie prób zapytań (rate limiting) dla ochrony przed atakami brute force

## Przyszłe ulepszenia bezpieczeństwa

- Dodanie ochrony CSRF
- Implementacja Multi-Factor Authentication (MFA)
- Implementacja rotacji tokenów JWT
- Dodanie filtrowania danych wejściowych i wyjściowych
