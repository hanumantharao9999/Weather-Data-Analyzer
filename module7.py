import tkinter as tk
from tkinter import messagebox, Toplevel, scrolledtext
import requests
import csv
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# --- CONFIG ---
API_KEY = "bd5e378503939ddaee76f12ad7a97608"  # Your OpenWeatherMap API key
CSV_FILE = "weather_data.csv"

# --- Fetch current weather ---
def fetch_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("cod") != 200:
            raise Exception(data.get("message", "Error fetching weather"))
        return data
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None

# --- Fetch 5-day/3-hour forecast ---
def fetch_forecast(city):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("cod") != "200":
            raise Exception(data.get("message", "Error fetching forecast"))
        return data
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None

# --- Update weather info on GUI ---
def update_weather():
    city = city_entry.get().strip()
    if not city:
        messagebox.showwarning("Input Error", "Please enter a city name.")
        return

    data = fetch_weather(city)
    if data:
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["description"].title()

        result_label.config(
            text=f"City: {city}\nTemperature: {temp} °C\nHumidity: {humidity}%\nCondition: {condition}"
        )
        save_to_csv(city, temp, humidity, condition)

# --- Save weather data to CSV ---
def save_to_csv(city, temp, humidity, condition):
    file_exists = False
    try:
        with open(CSV_FILE, "r"):
            file_exists = True
            print("file exist")
    except FileNotFoundError:
        pass
    
    with open(CSV_FILE, "a", newline="") as file:
        writer = csv.writer(file)  
        if not file_exists:
            print("file not exist")
            writer.writerow(["datetime", "city", "temp", "humidity", "condition"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), city, temp, humidity, condition])
        print(city)

# --- Show temperature chart from saved data ---
def show_chart():
    temps = []
    times = []

    try:
        with open(CSV_FILE, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["city"].lower() == city_entry.get().strip().lower():
                    temps.append(float(row["temp"]))
                    times.append(row["datetime"])
    except FileNotFoundError:
        messagebox.showerror("File Error", "No weather history found.")
        return

    if not temps:
        messagebox.showinfo("No Data", "No records for this city.")
        return

    plt.figure(figsize=(8, 4))
    plt.plot(times, temps, marker="o", linestyle='-', color='blue')
    plt.xticks(rotation=45)
    plt.xlabel("Date & Time")
    plt.ylabel("Temperature (°C)")
    plt.title(f"Temperature Trend - {city_entry.get().title()}")
    plt.tight_layout()
    plt.grid(True)
    plt.show()

# --- Show 5-day forecast in a popup window ---
def show_forecast():
    city = city_entry.get().strip()
    if not city:
        messagebox.showwarning("Input Error", "Enter a city name.")
        return

    forecast_data = fetch_forecast(city)
    if not forecast_data:
        return

    # Aggregate data by date
    daily_data = {}
    for item in forecast_data["list"]:
        date_str = item["dt_txt"].split(" ")[0]  # YYYY-MM-DD
        temp = item["main"]["temp"]
        desc = item["weather"][0]["description"].title()

        if date_str not in daily_data:
            daily_data[date_str] = {"temps": [], "descs": []}
        daily_data[date_str]["temps"].append(temp)
        daily_data[date_str]["descs"].append(desc)

    # Prepare forecast text with average temps and most common description per day
    forecast_text = ""
    for date_str in sorted(daily_data.keys())[:5]:
        temps = daily_data[date_str]["temps"]
        descs = daily_data[date_str]["descs"]
        avg_temp = sum(temps) / len(temps)
        # Most common description
        most_common_desc = max(set(descs), key=descs.count)
        forecast_text += f"{date_str}: Avg Temp: {avg_temp:.1f} °C, Condition: {most_common_desc}\n"

    # Show in popup window
    top = Toplevel(root)
    top.title(f"5-Day Forecast - {city}")
    top.geometry("400x300")

    txt = scrolledtext.ScrolledText(top, width=50, height=15, font=("Arial", 10))
    txt.pack(padx=10, pady=10)
    txt.insert(tk.END, forecast_text)
    txt.config(state=tk.DISABLED)

# --- Export CSV to Excel ---
def export_to_excel():
    try:
        df = pd.read_csv(CSV_FILE)
        export_file = "weather_data_export.xlsx"
        df.to_excel(export_file, index=False)
        messagebox.showinfo("Export Complete", f"Data exported to {export_file}")
    except Exception as e:
        messagebox.showerror("Export Failed", str(e))

# --- GUI Setup ---
root = tk.Tk()
root.title("Weather Data Analyzer")
root.geometry("400x400")

tk.Label(root, text="Enter City Name:").pack(pady=5)
city_entry = tk.Entry(root, width=30)
city_entry.pack(pady=5)

tk.Button(root, text="Get Weather", command=update_weather).pack(pady=10)
tk.Button(root, text="Show Temperature Chart", command=show_chart).pack(pady=5)
tk.Button(root, text="Show 5-Day Forecast", command=show_forecast).pack(pady=5)
tk.Button(root, text="Export to Excel", command=export_to_excel).pack(pady=5)

result_label = tk.Label(root, text="", font=("Arial", 12), justify="left")
result_label.pack(pady=20)

root.mainloop()
