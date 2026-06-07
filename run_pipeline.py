import subprocess
import sys
import os

def run_script(script_path):
    """Uruchamia skrypt Pythona jako osobny proces i sprawdza czy nie ma błędów."""
    print(f"\n==================================================")
    print(f"URUCHAMIANIE: {os.path.basename(script_path)}")
    print(f"==================================================")
    
    # Wywołujemy plik przy użyciu aktualnego interpretera (np. Waszego venv)
    result = subprocess.run([sys.executable, script_path], capture_output=False)
    
    if result.returncode != 0:
        print(f"BŁĄD: Skrypt {script_path} zakończył się niepowodzeniem!")
        sys.exit(1) # Przerywamy cały proces, jeśli któryś krok wybuchnie
    else:
        print(f"SUKCES: {os.path.basename(script_path)} zakończony.")

def main():
    print("=== ROZPOCZĘCIE AUTOMATYCZNEJ POTOKU DANYCH (WEATHER PIPELINE) ===")
    
    # Definiujemy kolejność wykonywania zadań (Workflow / Lineage)
    pipeline_steps = [
        "src/get_weather.py",
        "src/process_weather.py",
        "src/detect_events.py",
        "src/generate_report.py"
    ]
    
    # Uruchamiamy krok po kroku
    for step in pipeline_steps:
        if not os.path.exists(step):
            print(f"Błąd krytyczny: Nie znaleziono pliku {step}!")
            sys.exit(1)
        run_script(step)
        
    print("\n==================================================")
    print("BRAWO! CAŁY POTOK DANYCH WYKONANY AUTOMATYCZNIE!")
    print("Wyszukaj raport końcowy w: reports/daily_report.txt")
    print("==================================================")

if __name__ == "__main__":
    main()