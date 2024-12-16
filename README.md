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

## Środowisko sprzętowo-programowe i narzędziowe

## Architektura rozwiązania

## Sposób testowania

## Podział pracy w zespole

## Przewidywane funkcje do zademonstrowania w ramach odbioru częściowego.

## Plan pracy z podziałem na tygodnie.
