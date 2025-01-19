# **PSI 2024Z - Funnel**

---

## **Zadanie**
Celem zadania jest implementacja serwera HTTP, który będzie posiadał następujące funkcjonalności:

- Konfiguracja za pomocą pliku konfiguracyjnego (np. YAML lub TOML).
- Możliwość zamontowania wybranego katalogu pod zadaną ścieżką i nazwą hosta.
- Obsługa nagłówka Host.
- Obsługa nagłówka Authorization (Basic oraz Bearer).
- Obsługa przynajmniej żądań GET, POST oraz DELETE.
- Funkcjonalność widoku indeksu katalogu (GET /katalog powinien zwrócić odnośniki do plików i podkatalogów, poprawnie renderowane w przeglądarce).
- Dla chętnych: obsługa nagłówka Range.

---

## **Założenia funkcjonalne**

1. **Konfiguracja serwera**
   - Serwer odczytuje konfigurację z pliku **YAML** lub **TOML**.
   - Plik konfiguracyjny zawiera:
     - Host i port serwera,
     - Mapowanie ścieżek HTTP na katalogi lokalne,
     - Reguły autoryzacji dla zasobów (**Basic** i **Bearer**).

2. **Routing i montowanie katalogów**
   - Serwer obsługuje mapowanie katalogów lokalnych na zadane ścieżki HTTP.
   - Bezpieczeństwo montowanych katalogów:
     - Serwer blokuje dostęp do zasobów poza zamontowanymi katalogami.

3. **Obsługa metod HTTP**
   - Serwer obsługuje metody:
     - **GET**: Pobieranie zasobów i generowanie widoku katalogu.
     - **POST**: Odbieranie danych JSON i zapisywanie plików na serwerze.
     - **DELETE**: Usuwanie zasobów z zamontowanego katalogu.

4. **Widok indeksu katalogu**
   - Żądanie **GET** dla katalogu (np. `/static/`) generuje dynamiczną listę plików i podkatalogów w formacie HTML.

5. **Obsługa autoryzacji**
   - Możliwość zabezpieczenia wybranych ścieżek za pomocą:
     - **Basic Authorization**: Weryfikacja loginu i hasła.
     - **Bearer Authorization**: Weryfikacja tokena dostępowego.
   - Nieautoryzowane żądania zwracają **401 Unauthorized**.

6. **Obsługa nagłówka Host**
   - Serwer weryfikuje poprawność nagłówka **Host** i akceptuje żądania tylko dla dozwolonych wartości.
   - Niepoprawny nagłówek skutkuje odpowiedzią **400 Bad Request**.

7. **Obsługa kodów odpowiedzi HTTP**
   - Serwer zwraca standardowe kody statusu HTTP:
     - **200 OK**: Poprawna odpowiedź,
     - **201 Created**: Utworzono nowy zasób (POST),
     - **400 Bad Request**: Niepoprawne żądanie,
     - **401 Unauthorized**: Brak autoryzacji,
     - **403 Forbidden**: Błędne dane autoryzacyjne,
     - **404 Not Found**: Zasób nie istnieje,
     - **405 Method Not Allowed**: Nieobsługiwana metoda HTTP,
     - **500 Internal Server Error**: Wewnętrzny błąd serwera.

8. **Dynamiczna obsługa żądań POST**
   - Żądania **POST** z danymi JSON umożliwiają:
     - Tworzenie nowych plików w określonym katalogu,
     - Zwracanie odpowiedzi **201 Created** po udanym zapisie.

9. **Logowanie żądań**
   - Serwer loguje informacje o żądaniach, w tym:
     - Adres IP klienta,
     - Metodę HTTP,
     - Ścieżkę URL,
     - Kod odpowiedzi HTTP,
     - Czas odpowiedzi serwera.

10. **Obsługa nagłówka Range (opcjonalnie)**
    - Możliwość pobierania części pliku przy użyciu nagłówka **Range** (np. dla strumieniowania).


---

## **Założenia niefunkcjonalne**

1. **Wydajność**
   - Serwer obsługuje do **10 jednoczesnych połączeń** w środowisku lokalnym.
   - W celu realizacji obsługi wielu klientów serwer wykorzystuje **wielowątkowość** za pomocą modułu `threading`. Każde połączenie jest obsługiwane w osobnym wątku.
   - Czas odpowiedzi dla podstawowych żądań (GET) nie przekracza **1 sekundy**.

2. **Przenośność**
   - Serwer działa na systemach operacyjnych: **Linux**, **Windows** i **macOS**.
   - Wykorzystuje standardowe biblioteki Pythona (wersja **3.13**).

3. **Bezpieczeństwo**
   - Serwer blokuje dostęp do katalogów poza zdefiniowanymi ścieżkami.
   - Obsługa autoryzacji **Basic** i **Bearer** dla chronionych zasobów.

4. **Konfiguracja**
   - Wszystkie ustawienia serwera (host, port, mapowanie katalogów, autoryzacja) są definiowane w pliku **YAML** lub **TOML**.

5. **Testowalność**
   - **Testy jednostkowe**: Sprawdzają poprawność kluczowych funkcji serwera (routing, autoryzacja, obsługa plików).
   - **Testy integracyjne**: Obowiązkowe dla weryfikacji współdziałania wszystkich komponentów serwera.

6. **Niezawodność**
   - Serwer obsługuje sytuacje błędne (np. brak zasobu, błędna autoryzacja) i zwraca odpowiednie kody HTTP.
   - Błędy są logowane w pliku **logs/**.

7. **Utrzymywalność**
   - Kod jest zgodny ze standardami **PEP8** i zawiera dokumentację użytkową.

---

## **Przypadki użycia**

1. **Uruchomienie serwera HTTP z konfiguracją**
   - **Scenariusz**: Administrator uruchamia serwer, podając ścieżkę do pliku konfiguracyjnego YAML/TOML.
   - **Opis działania**:
     - Biblioteka odczytuje konfigurację zawierającą host, port, mapowanie katalogów i reguły autoryzacji.
     - Serwer startuje na zdefiniowanym hoście i porcie.
   - **Rezultat**: Serwer jest gotowy do obsługi żądań.

---

2. **Dostęp do statycznych plików**
   - **Scenariusz**: Użytkownik wysyła żądanie **GET** na ścieżkę `/static/file.txt`.
   - **Opis działania**:
     - Serwer sprawdza konfigurację i mapuje ścieżkę HTTP `/static` na lokalny katalog (np. `/var/www/static`).
     - Serwer odszukuje plik `file.txt` i zwraca go klientowi z kodem **200 OK**.
   - **Rezultat**: Plik jest poprawnie zwracany klientowi.

---

3. **Widok indeksu katalogu**
   - **Scenariusz**: Użytkownik wysyła żądanie **GET** na ścieżkę katalogu `/static/`.
   - **Opis działania**:
     - Serwer generuje dynamiczny widok HTML zawierający listę plików i podkatalogów.
     - Każdy plik jest wyświetlany jako odnośnik.
   - **Rezultat**: Klient otrzymuje stronę HTML z widokiem katalogu.

---

4. **Dostęp do zasobów chronionych (autoryzacja Basic)**
   - **Scenariusz**: Użytkownik próbuje uzyskać dostęp do zasobu chronionego (np. `/protected/data`).
   - **Opis działania**:
     - Serwer sprawdza nagłówek **Authorization**:
       - Jeśli dane (login i hasło) są poprawne → odpowiedź **200 OK**.
       - Jeśli dane są niepoprawne → odpowiedź **401 Unauthorized**.
       - Jeśli brak nagłówka **Authorization** → odpowiedź **400 Bad Request**.
   - **Rezultat**: Użytkownik otrzymuje zasób lub komunikat o błędzie.

---

5. **Dostęp do zasobów chronionych (autoryzacja Bearer)**
   - **Scenariusz**: Użytkownik próbuje uzyskać dostęp do zasobu chronionego tokenem Bearer (np. `/api/data`).
   - **Opis działania**:
     - Serwer weryfikuje token Bearer w nagłówku **Authorization**.
       - Jeśli token jest poprawny → odpowiedź **200 OK**.
       - Jeśli token jest błędny → odpowiedź **401 Unauthorized**.
       - Jeśli brak tokena → odpowiedź **400 Bad Request**.
   - **Rezultat**: Użytkownik otrzymuje zasób lub komunikat o błędzie.

---

6. **Przesyłanie danych na serwer (POST)**
   - **Scenariusz**: Użytkownik wysyła żądanie **POST** na ścieżkę `/upload` z danymi JSON.
   - **Opis działania**:
     - Serwer odbiera dane, weryfikuje ich poprawność i zapisuje je jako plik na serwerze.
     - Serwer zwraca odpowiedź **201 Created**.
   - **Rezultat**: Dane są zapisane na serwerze, a użytkownik otrzymuje potwierdzenie.

---

7. **Usuwanie zasobów z serwera (DELETE)**
   - **Scenariusz**: Użytkownik wysyła żądanie **DELETE** na ścieżkę `/static/file.txt`.
   - **Opis działania**:
     - Serwer sprawdza, czy plik istnieje w zamontowanym katalogu.
     - Jeśli plik istnieje → serwer usuwa plik i zwraca **200 OK**.
     - Jeśli plik nie istnieje → serwer zwraca **404 Not Found**.
   - **Rezultat**: Plik jest usunięty lub klient otrzymuje komunikat o błędzie.

---

8. **Błąd nagłówka Host**
   - **Scenariusz**: Użytkownik wysyła żądanie z niepoprawnym nagłówkiem **Host**.
   - **Opis działania**:
     - Serwer sprawdza nagłówek **Host** zgodnie z konfiguracją.
     - Jeśli nagłówek nie jest zgodny → serwer zwraca **400 Bad Request**.
   - **Rezultat**: Żądanie jest odrzucone.

---

9. **Obsługa nieznanej metody HTTP**
   - **Scenariusz**: Użytkownik wysyła żądanie z nieobsługiwaną metodą HTTP (np. **PATCH**).
   - **Opis działania**:
     - Serwer sprawdza metodę HTTP.
     - W przypadku nieobsługiwanej metody zwraca **405 Method Not Allowed**.
   - **Rezultat**: Klient otrzymuje komunikat o błędnej metodzie.

---

## **Analiza i obsługa błędnych sytuacji**

1. **Brak lub niepoprawna konfiguracja serwera**
   - **Sytuacja błędna**: Plik konfiguracyjny YAML/TOML jest nieprawidłowy lub brakuje wymaganych parametrów (np. host, port, ścieżki).
   - **Obsługa**:
     - Serwer wyświetla komunikat błędu i przerywa działanie.
     - Przykładowa wiadomość:
       ```
       Error: Invalid configuration file. Missing required parameter: 'port'.
       ```

---

2. **Żądanie zasobu, który nie istnieje**
   - **Sytuacja błędna**: Użytkownik wysyła żądanie **GET** lub **DELETE** dla pliku lub katalogu, który nie istnieje.
   - **Obsługa**:
     - Serwer zwraca odpowiedź **404 Not Found** z komunikatem:
       ```json
       {
         "error": "The requested resource was not found."
       }
       ```

---

3. **Niepoprawny nagłówek Host**
   - **Sytuacja błędna**: Użytkownik wysyła żądanie z niepoprawnym nagłówkiem **Host**.
   - **Obsługa**:
     - Serwer weryfikuje nagłówek **Host** i zwraca **400 Bad Request**:
       ```json
       {
         "error": "Invalid Host header. The host is not recognized by the server."
       }
       ```

---

4. **Brak autoryzacji dla zasobu chronionego**
   - **Sytuacja błędna**: Użytkownik próbuje uzyskać dostęp do zasobu chronionego bez nagłówka **Authorization**.
   - **Obsługa**:
     - Serwer zwraca odpowiedź **400 Bad Request** z komunikatem:
       ```json
       {
         "error": "Authorization header is missing."
       }
       ```

---

5. **Niepoprawne dane autoryzacyjne**
   - **Sytuacja błędna**: Użytkownik podaje błędny login/hasło (Basic) lub token (Bearer).
   - **Obsługa**:
     - Serwer zwraca odpowiedź **401 Unauthorized** z komunikatem:
       ```json
       {
         "error": "Invalid credentials or token."
       }
       ```

---

6. **Próba dostępu do zasobu spoza zamontowanego katalogu**
   - **Sytuacja błędna**: Użytkownik próbuje uzyskać dostęp do zasobów spoza zamontowanego katalogu (np. przez `../` w ścieżce URL).
   - **Obsługa**:
     - Serwer blokuje dostęp i zwraca **403 Forbidden**:
       ```json
       {
         "error": "Access to the requested resource is forbidden."
       }
       ```

---

7. **Nieobsługiwana metoda HTTP**
   - **Sytuacja błędna**: Użytkownik wysyła żądanie z metodą HTTP, która nie jest obsługiwana przez serwer (np. **PATCH**).
   - **Obsługa**:
     - Serwer zwraca odpowiedź **405 Method Not Allowed** z listą dozwolonych metod:
       ```json
       {
         "error": "HTTP method not allowed. Allowed methods: GET, POST, DELETE."
       }
       ```

---

8. **Błędny format danych w żądaniu POST**
   - **Sytuacja błędna**: Użytkownik wysyła żądanie **POST** z niepoprawnym lub niekompletnym formatem danych (np. błędny JSON).
   - **Obsługa**:
     - Serwer zwraca **400 Bad Request** z komunikatem:
       ```json
       {
         "error": "Invalid request payload. Please check the data format."
       }
       ```

---

9. **Błąd serwera (500)**
   - **Sytuacja błędna**: Wewnętrzny błąd serwera spowodowany np. wyjątkiem w kodzie.
   - **Obsługa**:
     - Serwer loguje szczegóły błędu do pliku logów.
     - Użytkownik otrzymuje odpowiedź **500 Internal Server Error**:
       ```json
       {
         "error": "An internal server error occurred. Please try again later."
       }
       ```

---

10. **Przekroczenie liczby jednoczesnych połączeń**
   - **Sytuacja błędna**: Liczba jednoczesnych połączeń przekracza limit (10).
   - **Obsługa**:
     - Nowe żądanie jest odrzucane z odpowiedzią **503 Service Unavailable**:
       ```json
       {
         "error": "The server is currently overloaded. Please try again later."
       }
       ```

---

## **Instrukcja uruchomienia**

Projekt znajduję się na repozytorium https://gitlab-stud.elka.pw.edu.pl/npieczko/funnel.git. Jest instalowalny za pomocą managera pakietów *uv*.

```
$ git clone https://gitlab-stud.elka.pw.edu.pl/npieczko/funnel.git
$ cd funnel
$ uv sync
$ uv pip install -e .
```

Nasza biblioteka umożliwia dodawanie ścieżek (route) przez dektorator. Aby uruchomić przykładowy serwer HTTP należy wywołać komendę:

```
$ python3 examples/main.py
```

---

## **Opis interfejsu użytkownika**

Zaimplementowany został dekorator *route*, który umożliwia dodanie ścieżki do serwera.

Struktura:
```python
@server.route(<path>, <methods>, <host>)
```

**path** - adres ściezki

**methods** - lista metod obsługiwanych pod daną ściezką

**host** - opcjonalny argument oznaczający adres hosta. W przypadku gdy host jest zdefiniowany, żądzanie musi zawierać dokładną nazwę hosta, aby zostało odbrane. Jezeli host nie zostanie podany żądania będą obsługiwane nieżaleznie od wartości nagłówka Host.

Przykład użycia:

```python
server = HTTPServer("./config/server_config.yaml")

@server.route("/", methods=["GET", "POST"], host="example.com")
def home_example(request):
    return Response.html(
        200, "OK", "<h1>Welcome to the Home Page of example.com host!</h1>"
    )
```
---

## **Środowisko sprzętowo-programowe i narzędziowe**

### **1. Systemy operacyjne**
   - **Linux** i **macOS** – system testowy i deweloperski.

---

### **2. Biblioteki programistyczne**
   - **Python 3.13** – język programowania do implementacji biblioteki i serwera.
   - **Standardowa biblioteka Pythona**:
     - `socket` - do implementacji niskopoziomowej komunikacji sieciowej dla protokołu HTTP,
     - `threading` – do obsługi wielowątkowości i równoczesnych połączeń,
     - `os` i `pathlib` – zarządzanie ścieżkami plików i katalogów,
     - `logging` – logowanie zdarzeń i błędów serwera,
     - `json` – przetwarzanie danych wejściowych w formacie JSON.

---

### **3. Narzędzia programistyczne**
   - **Edytor kodu**:
     - **Visual Studio Code** (VS Code) – główny edytor z rozszerzeniami dla Pythona.
   - **Kontrola wersji**:
     - **Git** – system kontroli wersji.
     - **GitLab** – repozytorium kodu źródłowego.
   - **Debugowanie**:
     - **PDB** – wbudowany debugger Pythona,
     - **VS Code Debugger** – graficzne narzędzie do debugowania.

---

### **4. Narzędzia do testowania**
   - **Testy jednostkowe**:
     - **pytest** – narzędzie do testów automatycznych.
   - **Testy integracyjne**:
     - **requests** – biblioteka do wysyłania żądań HTTP podczas testów.
   - **Manualne testowanie**:
     - **Postman** – narzędzie do ręcznego testowania żądań HTTP.
     - **curl** – wiersz poleceń do wysyłania żądań HTTP.

---

## **Architektura rozwiązania**

System składa się z **dwóch głównych części**:

1. **Biblioteka serwera HTTP**
   - Tworzy podstawową funkcjonalność umożliwiającą obsługę serwera HTTP.
   - Główne elementy biblioteki:
     - **Komunikacja sieciowa**: Odpowiada za tworzenie gniazd (`socket`) i obsługę połączeń od klientów.
     - **Routing**: Mapuje ścieżki HTTP na funkcje obsługi żądań.
     - **Obsługa żądań i odpowiedzi**: Przetwarza przychodzące żądania i generuje odpowiedzi HTTP z odpowiednimi kodami statusu.
     - **Autoryzacja**: Weryfikuje poprawność nagłówków autoryzacyjnych (**Basic** i **Bearer Authorization**).
     - **Logowanie**: Rejestruje informacje o żądaniach i błędach serwera do logów.

2. **Aplikacja serwera HTTP**
   - Korzysta z opracowanej biblioteki do implementacji działającego serwera HTTP.
   - Wykorzystuje możliwości biblioteki do:
     - Montowania lokalnych katalogów pod zdefiniowanymi ścieżkami HTTP,
     - Konfiguracji serwera (host, port, autoryzacja) z pliku **YAML/TOML**,
     - Definiowania reguł autoryzacji i tras (routingu),
     - Testowania i uruchomienia serwera w środowisku lokalnym.

---

## **Sposób testowania**

### **1. Testy jednostkowe**
Testy jednostkowe sprawdzają poprawność działania poszczególnych komponentów biblioteki.
- **Zakres testów**:
   - Weryfikacja poprawnego przetwarzania żądań HTTP (GET, POST, DELETE).
   - Sprawdzenie działania routingu i mapowania ścieżek.
   - Testowanie mechanizmów autoryzacji (**Basic** i **Bearer Authorization**).
   - Generowanie odpowiedzi HTTP z poprawnymi nagłówkami i statusami.
   - Obsługa błędów (np. brak zasobu, nieprawidłowe żądanie).
   - Obsługa nagłówka Range

- **Narzędzie**:
   - **pytest** – główne narzędzie do automatyzacji testów jednostkowych.

---

### **2. Testy integracyjne**
Testy integracyjne sprawdzają współdziałanie głównych komponentów systemu.
- **Zakres testów**:
   - Poprawne działanie serwera w odpowiedzi na żądania HTTP.
   - Testowanie pełnego przepływu żądania: od odbioru przez gniazdo sieciowe po wygenerowanie odpowiedzi.
   - Weryfikacja autoryzacji w przypadku chronionych zasobów.
   - Sprawdzenie montowania lokalnych katalogów i udostępniania plików.
   - Obsługa błędów przy niepoprawnych lub nieobsługiwanych żądaniach.

- **Narzędzia**:
   - **requests** – biblioteka do wysyłania żądań HTTP w testach.
   - **pytest** – automatyzacja integracyjnych przypadków testowych.

---

### **3. Testy manualne**
Testy manualne pozwolą zweryfikować serwer z perspektywy użytkownika.
- **Zakres testów**:
   - Wysłanie żądań HTTP przy użyciu narzędza **curl**.
   - Sprawdzenie udostępniania zasobów statycznych (pliki i katalogi).
   - Testowanie chronionych zasobów: poprawne i niepoprawne dane autoryzacyjne.
   - Weryfikacja obsługi sytuacji błędnych (404, 403, 500).

- **Narzędzia**:
   - **curl** – narzędzie wiersza poleceń do wysyłania żądań HTTP.

---

### Wyniki testowania

Napisane testy jednostkowe zapewniły porycie linii kodu na poziomie 100%. 


## **Podział pracy w zespole**

### **Daniel Machniak: Komunikacja sieciowa i konfiguracja**
- Implementacja mechanizmu **routingu**:
   - Mapowanie ścieżek HTTP na funkcje obsługi.
- Implementacja mechanizmu **niskopoziomowej komunikacji** przy użyciu `socket`:
   - Tworzenie gniazd, nasłuchiwanie połączeń, akceptowanie klientów.
- Dodanie obsługi wielowątkowości z wykorzystaniem **threading**.
- Obsługa podstawowych metod HTTP (**GET**)
- Implementacjia funkcjonalności montowania katalogów.
- Przygotowanie **testów jednostkowych** i **testów integracyjnych** dla poszczególnych komponentów.

---

### **Krzysztof Gólcz: Routing i obsługa żądań**
- Wczytywanie konfiguracji serwera (host, port, ścieżki) z pliku **YAML/TOML**.
- Obsługa podstawowych metod HTTP (**DELETE**)
- Implementacjia funkcjonalności montowania katalogów.
- Przygotowanie **testów jednostkowych** i **testów integracyjnych** dla poszczególnych komponentów.

---

### **Natalia Pieczko: Autoryzacja, logowanie i testowanie**
- Implementacja mechanizmów autoryzacji (**Basic Authorization**, **Bearer Authorization**).
- Ulepszenie mechanizmu **niskopoziomowej komunikacji** umożliwiając przesyłanie większych porcji danych.
- Obsługa podstawowych metod HTTP (**POST**)
- Implementacja **logowania** żądań (adres IP, metoda, ścieżka, status odpowiedzi) i zapisu do pliku logów.
- Dodanie mechnizmu obsługi nagłówka **Range**
- Przygotowanie **testów jednostkowych** i **testów integracyjnych** dla poszczególnych komponentów.


---

### **Wspólne zadania**
- **Integracja** wszystkich modułów w jeden spójny system.
- Stworzenie przykładowej aplikacji serwera HTTP z wykorzystaniem biblioteki.
- Testowanie całości rozwiązania pod kątem wydajności i poprawności.
- Przygotowanie dokumentacji końcowej.

---

## **Przewidywane  funkcje do zademonstrowania**

1. **Uruchomienie serwera**

2. **Routing i obsługa ścieżek**
   - Mapowanie ścieżek HTTP na funkcje obsługi.
   - Przykłady:
     - **GET** `/hello` – zwrócenie komunikatu tekstowego,
     - **POST** `/echo` – odbiór danych JSON i ich zwrócenie w odpowiedzi.

3. **Autoryzacja**
   - Weryfikacja dostępu do chronionych zasobów za pomocą:
     - **Basic Authorization**,
     - **Bearer Authorization**.

4. **Montowanie katalogów**
   - Udostępnienie plików lokalnych przez HTTP (np. `/static`).

5. **Obsługa błędów**
   - Przykłady sytuacji błędnych:
     - **404 Not Found** – brak zasobu,
     - **401 Unauthorized** – brak autoryzacji,
     - **405 Method Not Allowed** – metoda nieobsługiwana.

6. **Logowanie żądań**
   - Rejestrowanie podstawowych informacji o żądaniach: metoda, ścieżka, status odpowiedzi.
   - Zapis logów do pliku tekstowego.

---

## **Harmonogram pracy**

### **Tydzień 1: Przygotowanie środowiska i implementacja podstaw serwera**

 - Przygotowanie struktury projektu i pliku konfiguracyjnego **YAML/TOML**.
 - Implementacja komunikacji sieciowej z użyciem `socket`:
   - Tworzenie gniazda, nasłuchiwanie połączeń i akceptowanie klientów.
 - Implementacja podstawowego routingu:
   - Obsługa prostych ścieżek **GET**.
 - Stworzenie mechanizmu logowania żądań.

**Wynik tygodnia**: Serwer przyjmuje połączenia, obsługuje proste żądanie **GET**, loguje żądania.

---

### **Tydzień 2: Rozbudowa funkcjonalności serwera**

 - Dodanie obsługi wielowątkowości przy użyciu **threading**.
 - Rozbudowa routingu o obsługę metod: **POST** i **DELETE**.
 - Implementacja **Basic Authorization**.

**Wynik tygodnia**: Serwer obsługuje metody **GET, POST, DELETE**, wspiera wielowątkowość i autoryzację **Basic**.

---

### **Tydzień 3: Finalizacja kluczowych funkcji (odbiór częściowy)**

 - Dodanie montowania katalogów lokalnych pod ścieżki HTTP (np. `/static`).
 - Weryfikacja obsługi błędów:
   - **404 Not Found**, **405 Method Not Allowed**.
 - Rozszerzenie autoryzacji o **Bearer Authorization**.


**Odbiór częściowy**:
- Uruchomienie serwera z podstawowymi funkcjami: komunikacja sieciowa, routing, autoryzacja, montowanie katalogów i obsługa błędów.
- Demonstracja testów jednostkowych i manualnych.

---

### **Tydzień 4: Testowanie i optymalizacja**

   - Optymalizacja obsługi wielowątkowości i logiki serwera.
   - Przygotowanie testów integracyjnych i manualnych.
   - Dokumentacja przypadków testowych i wyników.

**Wynik tygodnia**: Serwer jest w pełni przetestowany pod kątem jednostkowym, integracyjnym i manualnym.

---

### **Tydzień 5: Finalizacja i odbiór projektu**

  - Integracja wszystkich modułów i ostateczne testowanie całości.
  - Przygotowanie logów serwera i raportu z wyników testów.
  - Dokumentacja techniczna i użytkowa projektu (README).
  - Prezentacja funkcji serwera:
    - Uruchomienie serwera,
    - Obsługa żądań (GET, POST, DELETE),
    - Autoryzacja,
    - Logowanie i obsługa błędów.

**Wynik tygodnia**: Gotowy, przetestowany serwer HTTP z dokumentacją i funkcjami do demonstracji.

---

## **Opis najważniejszych rozwiązań funkcjonalnych**


---

## **Postać plików konfiguracyjnych oraz logów**

---

## **Podsumowanie**

---