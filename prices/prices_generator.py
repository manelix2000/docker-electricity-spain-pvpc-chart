import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import matplotlib.pyplot as plt
import random
import os
import requests
from datetime import datetime

def generate_chart(values):
    timestamp = datetime.now().strftime('%Y%m%d%H')
    output_filename = f'{timestamp}_prices.png'
    output_path = os.path.join('images', output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)  # Ensure folder exists

    if not os.path.exists(output_path):
        print(f"[INFO] Creating initial {output_path}...")
    else:
        print(f"[INFO] Overwriting {output_path}...")

    # Extract hours and prices, sorted by hour
    sorted_values = sorted(values, key=lambda v: v['hour'])
    hours = [v['hour'] for v in sorted_values]
    prices = [v['price'] for v in sorted_values]

    # Find current hour and price
    current_hour = datetime.now().hour
    current_value = next((v for v in sorted_values if v['hour'] == current_hour), None)

    # Plot chart
    plt.figure(figsize=(8, 4))
    plt.plot(hours, prices, marker='o', label="Electricity Price (€/kWh)")
    plt.xticks(range(0, 24))
    plt.xlabel("Hour")
    plt.ylabel("€/kWh")
    plt.title("Spain PVPC Electricity Prices")
    plt.grid(True)

    # Add annotation for current price
    if current_value:
        x = current_value['hour']
        y = current_value['price']
        plt.annotate(
            f"Now: {y:.3f} €/kWh",
            xy=(x, y),
            xytext=(x + 0.5, y + 0.01),
            arrowprops=dict(arrowstyle="->", color="red"),
            color="red",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", lw=0.5)
        )

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def get_prices():
    print('---------------------------------------------')
    print('Getting prices... ESIOS_API_TOKEN='+os.getenv('ESIOS_API_TOKEN', ''))
    url = 'https://api.esios.ree.es/indicators/1001'
    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v1+json',
        'Content-Type': 'application/json',
        'x-api-key': os.getenv('ESIOS_API_TOKEN', '')
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        body = response.json()

        values = [
            {
                **e,
                'price': e['value'] / 1000,
                'hour': datetime.fromisoformat(e['datetime']).hour
            }
            for e in body['indicator']['values']
            if e['geo_id'] == 8741
        ]

        max_price = max(v['price'] for v in values)
        min_price = min(v['price'] for v in values)

        sum_weighted = sum(v['price'] * (1 / v['price']) for v in values)
        weight_sum = sum(1 / v['price'] for v in values)
        weighted_avg = sum_weighted / weight_sum if weight_sum else 0

        sum_avg = sum(v['price'] for v in values)
        avg_price = sum_avg / len(values) if values else 0

        current_hour = datetime.now().hour
        current_price_info = next((v for v in values if v['hour'] == current_hour), None)
        current_price = current_price_info['price'] if current_price_info else 0

        price_percentage = 100 - (((current_price - min_price) / (max_price - min_price)) * 100) if max_price != min_price else 0

        print('---------------------------------------------')
        if current_price_info:
            dt = datetime.fromisoformat(current_price_info['datetime'])
            print(f"Current Hour {str(dt.hour).zfill(2)}-{str(dt.hour + 1).zfill(2)}")

        print(f"Weighted Price {weighted_avg:.2f} vs Average Price {avg_price:.2f}")
        print(f"Current Price {current_price} percentage {price_percentage}")
        generate_chart(values)
    except Exception as e:
        print(f"Failed to update light price: {e}")