# PSI 2024Z - Funnel

## Zadanie
Celem zadania jest implementacja serwera HTTP, który będzie posiadał następujące funkcjonalności:

- Konfiguracja za pomocą pliku konfiguracyjnego (np. YAML lub TOML).
- Możliwość zamontowania wybranego katalogu pod zadaną ścieżką i nazwą hosta.
- Obsługa nagłówka Host.
- Obsługa nagłówka Authorization (Basic oraz Bearer).
- Obsługa przynajmniej żądań GET, POST oraz DELETE.
- Funkcjonalność widoku indeksu katalogu (GET /katalog powinien zwrócić odnośniki do plików i podkatalogów, poprawnie renderowane w przeglądarce).
- Dla chętnych: obsługa nagłówka Range.
## Założenia funkcjonalne
1. Serwer powinien odczytywać konfigurację z pliku YAML lub TOML, umożliwiającego dostosowanie parametrów takich jak:
    - Host i port serwera.
    - Ścieżki do zamontowanych katalogów.
    - Reguły autoryzacji (Basic i Bearer).
    - Dodatkowe ustawienia opcjonalne (np. obsługa Range).
2. Administrator powinien mieć możliwość przypisania katalogów lokalnych do wybranych ścieżek HTTP oraz nazw hostów za pomocą pliku konfiguracyjnego.
3. Serwer musi poprawnie obsługiwać nagłówek Host, odrzucając żądania z niepoprawnym hostem.
4. Serwer powinien obsługiwać nagłówek Authorization:
    - Basic: Weryfikacja loginu i hasła użytkownika.
    - Bearer: Weryfikacja tokenu dostępowego.
5. Serwer powinien obsługiwać metody HTTP:
    - GET: Odczyt zasobów, w tym możliwość generowania widoku indeksu katalogu.
    - POST: Tworzenie lub przesyłanie zasobów.
    - DELETE: Usuwanie zasobów.
6. Serwer powinien udostępniać widok indeksu katalogu. W przypadku żądania GET /katalog serwer powinien generować widok HTML zawierający listę plików i podkatalogów.
7. Serwer powinien obsługiwać i zwracać odpowiednie kody statusu:
    - 400 Bad Request dla niepoprawnych żądań.
    - 401 Unauthorized dla braku autoryzacji.
    - 403 Forbidden dla niedozwolonych działań.
    - 404 Not Found dla nieistniejących zasobów.
## Założenia niefunkcjonalne

## Przypadki użycia
Podstawowe przypadki użycia:
- Administrator uruchamia serwer podając ścieżkę do pliku konfiguracyjnego, np.:
```
host: "localhost"
port: 8080
mounts:
  - path: "/static"
    directory: "/var/www/static"
    hostname: "example.com"
auth:
  basic:
    users:
      admin: "password123"
  bearer:
    token: "my-secret-token"
```
Serwer uruchamia się zgodnie z podaną konfiguracją
- Użytkownik odwiedza adres podany w konfiguracji np. http://example.com/static w przeglądarce, gdzie serwer udostępnia pliki z katalogu /var/www/static. Przykładowe żądanie:
GET http://example.com/static/file.txt z nagłówkiem Host: example.com.
Serwer zwraca zawartość pliku /var/www/static/file.txt

- Użytkownik próbuje uzyskać dostęp do zasobu chronionego. Przykładowe żądanie GET http://example.com/protected/resource z nagłówkiem:
Authorization: Basic YWRtaW46cGFzc3dvcmQxMjM=
W rezultacie, w przypadku dane logowania są poprawne to serwer zwróci dane, a kiedy niepoprawnie to serwer zwraca 401 Unauthorized.

- Użytkownik korzysta z tokena Bearer, aby uzyskać dostęp do chronionego zasobu.
Przykładowe żądanie: GET http://example.com/api/data
z nagłówkiem Authorization: Bearer my-secret-token
Jeśli token jest poprawny to zwracane są przez serwer dane. W przeciwnym przypadku serwer zwraca kod 403.

- Użytkownik odwiedza /static w przeglądarce, a serwer odpowiada wygenerowaną listą plików i katalogów.
Przykładowe żądanie: GET http://example.com/static/
W rezultacie otrzymujemy kod HTML wygenerowany przez serwer

- Użytkownik przesyła dane do zapisania na serwerze.
Przykładowe żądanie: POST http://example.com/api/upload
Z nagłówkiem Content-Type: application/json
O treści:
```
{
  "filename": "data.txt",
  "content": "Hello, World!"
}
```
Serwer w rezultacie zapisuje plik i zwraca kod 201 Created.

- Użytkownik usuwa zasób z serwera za pomocą DELETE. Np.
Żądanie: DELETE http://example.com/static/file1.txt
Serwer w rezultacie usuwany jest z serwera plik file1.txt

- Użytkownik wysyła żądanie z nieprawidłowym nagłówkiem Host. Na przykład:
Żądanie: GET http://example.com/static/file.txt
Z nagłówkiem: Host: otherhost.com
W rezultacie serwer zwraca kod błędu 400 Bad Request


## Analiza sytuacji błędnych i ich obsługa
1. Brak parametrów niezbędnych do konfiguracji serwera. Obługiawane za pomocą komunikatu zwrotnego na przykład:
```Error: Invalid configuration file. Missing 'port' parameter.```
2. Błędna składnie pliku konfiguracyjnego. Obsługowane za pomocą wiadomości zwrotnej.
3. Błedny/brak nagłówka host w żądaniu. Serwer zwraca kod błędu 400 z wiadomością:
```
{
  "error": "Invalid Host header. The host is not recognized by the server."
}
```
4. Brak nagłówka Authorization w przypadku żądania do zasobu chronionego. Obsłużone za pomocą kodu błędu 401 Unauthorized i przykładowej wiadomości:
```
{
  "error": "Authorization header is missing."
}
```
5. Nieprawidłowy login/hasło w autoryzacji Basic lub nieprawidłowy token w autoryzacji Bearer kiedy żądany jest dostęp do zasobu chronionego . Obsłużone za pomocą kodu błędu 403 Forbidden i przykładowej wiadomości:
```
{
  "error": "Invalid credentials or token."
}
```
6. Użytkownik próbuje uzyskać dostęp do pliku lub katalogu, który nie istnieje. Obsłużone przez zwrócenie kodu 404 Not Found z przykładową treścią
```
{
  "error": "The requested resource was not found."
}
```
7. Użytkownik używa nieobsługiwanej metody np PATCH. Obsłużone przez wysłanie kodu odpowiedzi 405 Method Not Allowed z treścią:
```
{
  "error": "HTTP method not allowed. Allowed methods: GET, POST, DELETE."
}
```

## Środowisko sprzętowo-programowe i narzędziowe

## Architektura rozwiązania

## Sposób testowania

## Podział pracy w zespole

## Przewidywane funkcje do zademonstrowania w ramach odbioru częściowego.

## Plan pracy z podziałem na tygodnie.
