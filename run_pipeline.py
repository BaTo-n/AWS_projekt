import subprocess
import sys
import os

def run_script(script_path):
    print(f"\n==================================================")
    print(f"URUCHAMIANIE: {os.path.basename(script_path)}")
    print(f"==================================================")
    
    result = subprocess.run([sys.executable, script_path], capture_output=False)
    
    if result.returncode != 0:
        print(f"BŁĄD: Skrypt {script_path} zakończył się niepowodzeniem!")
        sys.exit(1)
    else:
        print(f"SUKCES: {os.path.basename(script_path)} zakończony.")

def main():
    print("=== ROZPOCZĘCIE PIPELINE'a ===")
    
    pipeline_steps = [
        "src/get_weather.py",
        "src/process_weather.py",
        "src/detect_events.py",
        "src/generate_report.py"
    ]
    
    for step in pipeline_steps:
        if not os.path.exists(step):
            print(f"Nie znaleziono pliku {step}!")
            sys.exit(1)
        run_script(step)
        
    print("Zapisano raport końcowy w: reports/daily_report.txt")

if __name__ == "__main__":
    main()