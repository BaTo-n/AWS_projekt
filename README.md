# System Ekspercki Analizy Pogodowej – Daily Event Timeline
**Projekt nr 9 – Autonomous Expert Systems and Data Exploration**

Automatyczny potok danych (Data Pipeline) oraz System Ekspercki służący do monitorowania, agregowania i wykrywania anomalii pogodowych na podstawie danych z REST API. Projekt realizuje pełną architekturę referencyjną przetwarzania Big Data: od surowej pozyskiwalności, przez okienkową agregację, aż po logikę reguł eksperckich i prezentację wyników.

---

## Architektura Referencyjna i Przepływ Danych (Data Lineage)

Projekt został zaprojektowany zgodnie z zasadą luźnego powiązania komponentów, dzieląc potok przetwarzania na 4 odseparowane warstwy funkcjonalne:

[ Weather REST API ]
          │
          ▼  (Ingestion Layer)
   get_weather.py  ──> Zapis surowego pliku do: [ data/raw/ ]
          │
          ▼  (Processing Layer - Apache Spark)
 process_weather.py ──> Agregacja okienkowa (1h) do: [ data/processed/hourly_weather/ ]
          │
          ▼  (Analytics Layer - System Ekspercki)
  detect_events.py ──> Walidacja progów i anomalii do: [ data/processed/events.csv ]
          │
          ▼  (Presentation Layer)
generate_report.py ──> Generowanie końcowego raportu w: [ reports/daily_report.txt ]

1. Warstwa Ingestii (get_weather.py): Odpytuje zewnętrzne API pogodowe, pobiera zmienne środowiskowe i utrwala niezmieniony stan surowy w formacie JSON.
2. Warstwa Przetwarzania (process_weather.py): Silnik Apache Spark (PySpark SQL) ładuje strukturę na podstawie zdefiniowanego schematu, normalizuje znaczniki czasu oraz wykonuje agregacje godzinowe za pomocą funkcji okien czasowych (F.window).
3. Warstwa Analityczna / System Ekspercki (detect_events.py): Silnik regułowy (Rule-Engine) analizuje ustrukturyzowane dane godzinowe w poszukiwaniu anomalii i ekstremów takich jak silny wiatr, ulewy czy fale upałów.
4. Warstwa Prezentacji (generate_report.py): Agreguje statystyki dobowe i generuje sformatowany, czytelny raport biznesowo-analityczny dla użytkownika końcowego.

---

## Struktura Katalogów Projektu

weather-emr-project/
│
├── run_pipeline.py          # Główny orkiestrator (uruchamia cały potok automatycznie)
├── .gitignore               # Blokada wersjonowania danych lokalnych i śmieci systemowych
├── README.md                # Dokumentacja techniczna projektu
│
├── data/                    # Magazyn danych (lokalny / emulacja AWS S3)
│   ├── raw/                 # Nieprzetworzone pliki wejściowe JSON z API
│   └── processed/           # Dane ustrukturyzowane po procesach Spark i Pandasa
│       ├── hourly_weather/  # Skonsolidowane pliki CSV wygenerowane przez Sparka
│       └── events.csv       # Oś czasu wykrytych zdarzeń przez system ekspercki
│
├── reports/                 # Warstwa wyjściowa
│   └── daily_report.txt     # Gotowy raport analityczny (podsumowanie + alerty)
│
└── src/                     # Kod źródłowy modułów
    ├── get_weather.py       # Pobieranie danych z API (Inżynieria danych)
    ├── process_weather.py   # Agregacje i okna czasowe (Apache Spark)
    ├── detect_events.py     # Detekcja anomalii i reguły (System Ekspercki)
    └── generate_report.py   # Generowanie prezentacji wynikowej (Raport tekstowy)

---

## Kryteria i Reguły Systemu Eksperckiego

Moduł analityczny bazuje na predefiniowanych progach meteorologicznych identyfikujących zdarzenia krytyczne w rozdzielczości godzinowej:
* Heavy Rain (Ulewa): Opad godzinowy wykraczający poza normę bezpieczeństwa.
* Strong Wind (Silny Wiatr): Maksymalny poryw wiatru stanowiący zagrożenie.
* Heat Wave (Fala Upałów): Średnia temperatura godzinowa przekraczająca próg komfortu termicznego.
* Frost Alert (Przymrozek): Spadek temperatury poniżej zera stopni.

---

## Wymagania Środowiskowe i Instalacja

Wymagania Lokalne (Przed migracją na AWS EMR):
1. Python 3.9+
2. Java JDK 11 lub 17 (Wymagana do poprawnego działania silnika Apache Spark lokalnie). Zmienna środowiskowa JAVA_HOME musi wskazywać na katalog instalacyjny JDK.

Instalacja bibliotek:
Wewnątrz swojego środowiska wirtualnego (venv) zainstaluj wymagane pakiety:
pip install pyspark pandas requests

---

## Instrukcja Uruchomienia

Aby uruchomić cały potok przetwarzania danych automatycznie (od pobrania danych po końcowy raport), użyj przygotowanego skryptu orkiestracji znajdującego się w folderze głównym:

python run_pipeline.py

Ręczne uruchamianie krok po kroku:
Jeżeli chcesz debugować poszczególne warstwy niezależnie, zachowaj poniższą kolejność:
python src/get_weather.py
python src/process_weather.py
python src/detect_events.py
python src/generate_report.py

---

## Założenia, Ograniczenia i Rozwój (AWS EMR/S3 Context)

* Architektura chmurowa: Kody źródłowe zostały przygotowane w sposób umożliwiający bezpośrednią migrację na platformę chmurową AWS. W środowisku docelowym ścieżki lokalne data/raw/ oraz data/processed/ zostaną zamienione na adresy zasobów w AWS S3 (np. s3://bucket-pogodowy/raw/).
* Skalowanie: Wykorzystanie czystego PySpark SQL w process_weather.py gwarantuje, że skrypt uruchomiony na klastrze maszyn AWS EMR (np. na bezpiecznych pod kątem kompatybilności instancjach opartych na architekturze Intel/AMD, takich jak r6i.xlarge lub r5.xlarge) bez żadnych modyfikacji kodu obsłuży duże wolumeny danych historycznych dla wielu stacji jednocześnie.
* Ograniczenia: Obecna wersja systemu eksperckiego działa w oparciu o statyczne progi regułowe. Przyszłym krokiem rozwoju jest wdrożenie zaawansowanych modeli uczenia maszynowego (np. z biblioteki SparkML) w celu dynamicznego wyznaczania anomalii relatywnie do trendów długoterminowych.