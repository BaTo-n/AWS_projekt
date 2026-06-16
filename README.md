# Projekt 9 - Weather Event Timeline and Automatic Daily Report
## Cel projektu
Głównym celem projektu jest wygenerowanie dziennej osi czasu ważnych zdarzeń pogodowych oraz czytelnego podsumowania analitycznego w formie raportu. Zgodnie z założeniami, system pobiera dane ze współdzielonego Weather REST API, a następnie automatycznie je przetwarza, agreguje w oknach godzinowych i wykorzystuje reguły systemu eksperckiego do detekcji anomalii (np. ulewnego deszczu, silnego wiatru czy ryzyka burzy na podstawie spadku ciśnienia). Projekt udowadnia, że komponenty systemów eksperckich wspierają przepływ przetwarzania danych, a nie go zastępują.


## Architektura systemu
System został zaprojektowany zgodnie z założeniami potokowego przetwarzania danych i zachowuje wyraźny podział na warstwy. Opiera się na architekturze rekomendowanej w zadaniu: od kolektora REST API, przez surowy magazyn danych, czyszczenie i transformację, po analitykę opartą na regułach eksperckich i finalny raport.

### Komponenty architektury


* Warstwa Pobierania: Skrypt get_weather.py łączy się ze współdzielonym interfejsem REST API (endpoint /weather/batch dla stacji GDN_01). Pobrane, surowe pomiary są bezwzględnie utrwalane na dysku w formacie JSON w warstwie data/raw/ przed jakimkolwiek czyszczeniem.
* Warstwa Przetwarzania: Skrypt process_weather.py odpowiada za wczytanie surowych plików JSON, transformację zagnieżdżonych struktur oraz normalizację znaczników czasu. Następnie dane są agregowane w oknach 1-godzinnych (średnia temperatura, wilgotność, suma opadów itp.) i zapisywane do formatu CSV w warstwie data/processed/. Użycie Spark SQL zapewnia skalowalność.
* Warstwa Analityczna i Systemu Eksperckiego: Skrypt detect_events.py iteruje po zagregowanych danych i przy użyciu silnika opartego na regułach eksperckich  klasyfikuje i filtruje zdarzenia anomalne (np. wiatr >= 50 km/h, ciśnienie < 1000 hPa). Wyniki trafiają do pliku events.csv.
* Warstwa Prezentacji: Skrypt generate_report.py konsoliduje dane godzinowe z tabelą zdarzeń, wylicza dzienne metryki (np. min/max) i generuje podsumowanie (wykres matplotlib oraz raport.txt).

```text
   [ Pobieranie Danych z API ]
                |
                v
  [ Przetwarzanie i Agregacja  ]
                |
                v
       [ System Ekspercki ]      
                |
                v 
[ Generowanie Raportu Końcowego ]
```
---

Całość zarządzana jest z poziomu narzędzia Docker Compose, które poprzez mapowanie wolumenów dba o zachowanie plików wynikowych w systemie hosta.


### Struktura projektu
```text
root/
├── data/
│   ├── processed/
│   │   ├── hourly_weather/        # Wynikowe pliki CSV z sesji Spark
│   │   └── events.csv             # Oś czasu wykrytych anomalii
│   └── raw/
│       └── weather_*.json         # Surowe zrzuty z REST API
├── reports/
│   ├── daily_report.txt           # Główny raport tekstowy z metrykami
│   └── daily_weather_chart.png    # Wykres
├── src/
│   ├── detect_events.py           # Silnik reguł 
│   ├── generate_report.py         # Moduł wizualizacji i podsumowań
│   ├── get_weather.py             # Moduł pobierania danych z API
│   └── process_weather.py         # Skrypt PySpark
├── docker-compose.yml
├── Dockerfile
├── README.md
└── requirements.txt
```

### Reguły Systemu Eksperckiego

Moduł analityczny bazuje na predefiniowanych progach meteorologicznych identyfikujących zdarzenia krytyczne w rozdzielczości godzinowej:
* **Heavy Rain (Ulewa):** Opad godzinowy wykraczający poza normę bezpieczeństwa ($\ge$ 10.0 mm).
* **Strong Wind (Silny Wiatr):** Maksymalny poryw wiatru stanowiący zagrożenie ($\ge$ 50.0 km/h).
* **Heat Wave (Fala Upałów):** Średnia temperatura godzinowa przekraczająca próg komfortu termicznego ($\ge$ 30.0 °C).
* **Frost Alert (Przymrozek):** Spadek temperatury poniżej lub równej zero ($\le$ 0.0 °C).
* **Low Pressure / Storm Risk (Ryzyko Burzy):** Znaczny spadek ciśnienia atmosferycznego zwiastujący załamanie pogody (< 1000.0 hPa).
* **High Humidity (Wysoka Wilgotność):** Ekstremalne nasycenie powietrza parą wodną obniżające komfort (> 90.0 %).

## Instrukcja Uruchomienia

Projekt został skonteneryzowany, co oznacza, że jego uruchomienie sprowadza się do kilku prostych poleceń. Oczywiście oznacza to, że wymagane jest posiadanie Docker'a.

* Ze względów bezpieczeństwa token do API nie został udostępniony w kodzie. Najpierw należy podmienić token z src/get_weather.py na poprawny.
* Teraz wystarczy z perspektywy katalogu projektu użyć polecenia `docker compose up --build`, zbuduje ono obraz systemu i automatycznie go odpali.
* Jeśli obraz zostanie już zbudowany z każdym kolejnym razem wystarczy użyć `docker compose up`.