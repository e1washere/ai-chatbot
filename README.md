# AI Dokumenty - Inteligentny Asystent Dokumentów

![License](https://img.shields.io/github/license/e1washere/ai-chatbot)
![Last Commit](https://img.shields.io/github/last-commit/e1washere/ai-chatbot)
![Python](https://img.shields.io/badge/Built%20with-Python-blue)
![GitHub issues](https://img.shields.io/github/issues/e1washere/ai-chatbot)
![GitHub Repo stars](https://img.shields.io/github/stars/e1washere/ai-chatbot?style=social)
![GitHub forks](https://img.shields.io/github/forks/e1washere/ai-chatbot?style=social)

Zaawansowane narzędzie AI do analizy dokumentów PDF z wykorzystaniem sztucznej inteligencji. Wspiera języki polski, angielski, ukraiński i rosyjski.

## 🚀 Funkcje

- 📄 Analiza wielu plików PDF jednocześnie
- 🔍 Inteligentne wyszukiwanie w dokumentach
- 🌐 Wsparcie dla wielu języków (PL, EN, UKR, RU)
- 📱 Responsywny interfejs
- 💳 System subskrypcji (darmowa/premium)
- 📊 Źródła odpowiedzi z numerami stron

## 🎯 Główne zastosowania B2B

1. **Kancelarie prawne**
   - Analiza umów i dokumentów prawnych
   - Szybkie wyszukiwanie klauzul i zapisów

2. **Działy HR**
   - Analiza dokumentów pracowniczych
   - Wyszukiwanie w regulaminach i procedurach

3. **Firmy ubezpieczeniowe**
   - Analiza polis i dokumentów ubezpieczeniowych
   - Szybkie wyszukiwanie warunków i wyłączeń

4. **Firmy budowlane**
   - Analiza dokumentacji technicznej
   - Wyszukiwanie w specyfikacjach i normach

5. **Firmy konsultingowe**
   - Analiza raportów i dokumentacji
   - Wyszukiwanie w bazach wiedzy

## 📦 Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/yourusername/ai-dokumenty.git
cd ai-dokumenty
```

2. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

3. Utwórz plik `.streamlit/secrets.toml`:
```toml
# OpenAI API Key (required)
OPENAI_API_KEY = "your-openai-api-key"

# OCR.Space API Key (required for scanned PDFs)
OCR_SPACE_API_KEY = "your-ocr-space-api-key"

# Stripe Configuration (required for payments)
STRIPE_SECRET_KEY = "your-stripe-secret-key"
STRIPE_PAYMENT_LINK = "your-stripe-payment-link"

# App Configuration
MAX_FREE_PDFS = 1
ENVIRONMENT = "production"
```

4. Uruchom aplikację:
```bash
streamlit run app.py
```

## 🔧 Rozwiązywanie problemów

### Błąd podczas instalacji zależności

Jeśli pojawi się błąd z `faiss-cpu`, spróbuj:
1. Usuń linię `faiss-cpu==1.7.4` z `requirements.txt`
2. Uruchom ponownie deployment

### Błąd OCR

Jeśli OCR nie działa:
1. Sprawdź czy klucz OCR.Space API jest poprawny
2. Upewnij się, że PDF nie jest zabezpieczony

### Błąd OPENAI API

Jeśli pojawia się błąd OpenAI:
1. Sprawdź czy klucz API jest aktualny
2. Upewnij się, że masz wystarczające środki na koncie

### Błąd Stripe

Jeśli płatności nie działają:
1. Sprawdź czy klucze Stripe są prawidłowe
2. Upewnij się, że link do płatności jest aktualny

## 📱 Deployment

### Streamlit Cloud

1. Połącz z GitHub
2. Dodaj wszystkie sekrety w ustawieniach
3. Zdeployuj aplikację

### Landing Page

1. Zdeployuj folder `landing/` na Netlify/Vercel
2. Dodaj własną domenę
3. Skonfiguruj Google Analytics

## 📞 Wsparcie

W razie problemów:
- Email: support@aidokumenty.pl
- GitHub Issues
- Dokumentacja: [link do dokumentacji]

## 🔒 Bezpieczeństwo

- Wszystkie dokumenty są przetwarzane lokalnie
- Nie przechowujemy zawartości dokumentów
- Zgodność z RODO/GDPR

## 📄 Licencja

MIT License - zobacz plik LICENSE

## 💰 Model cenowy

- **Wersja darmowa**
  - 1 plik PDF
  - Podstawowe funkcje

- **Wersja premium**
  - Nielimitowana liczba plików
  - Wszystkie funkcje
  - Priorytetowe wsparcie

## 📝 Tekst marketingowy

"AI Dokumenty to rewolucyjne narzędzie, które zmienia sposób, w jaki firmy pracują z dokumentami. Dzięki zaawansowanej technologii AI, możesz w kilka sekund znaleźć odpowiedzi na pytania dotyczące Twoich dokumentów, bez konieczności ręcznego przeszukiwania setek stron.

Nasze rozwiązanie jest szczególnie przydatne dla:
- Kancelarii prawnych analizujących umowy
- Działów HR zarządzających dokumentacją pracowniczą
- Firm ubezpieczeniowych przetwarzających polisy
- Firm budowlanych pracujących z dokumentacją techniczną
- Firm konsultingowych analizujących raporty

Wspieramy dokumenty w językach polskim, angielskim, ukraińskim i rosyjskim, a nasz system OCR pozwala na pracę zarówno z dokumentami cyfrowymi, jak i zeskanowanymi.

Rozpocznij za darmo i przekonaj się, jak AI Dokumenty może zoptymalizować pracę Twojej firmy!"

---
*Ostatnia aktualizacja: 2025-06-07*
