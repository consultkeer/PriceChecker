import requests
import smtplib
import csv
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Fetch Google Sheet data
def fetch_google_sheet(sheet_id, gid):
    print(f"Fetching data from Google Sheet: Sheet ID {sheet_id}, GID {gid}")
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    response = requests.get(url)
    if response.status_code == 200:
        print("Successfully fetched Google Sheet data.")
        decoded_content = response.content.decode('utf-8')
        print(f"Raw fetched data:\n{decoded_content}")  # Debug raw data
        reader = csv.reader(decoded_content.splitlines())
        data = [row for row in reader]
        print(f"Parsed data: {data}")  # Debug parsed data
        print(f"Fetched {len(data)} rows from the sheet.")
        return data
    else:
        print(f"Failed to fetch data from Sheet GID {gid}. Status code: {response.status_code}")
        return []

# Scrape prices from Amazon
def fetch_price_amazon(url):
    print(f"Fetching price for Amazon URL: {url}")
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        # Locate the price element based on the provided structure
        price_whole = soup.find('span', {'class': 'a-price-whole'})
        price_fraction = soup.find('span', {'class': 'a-price-fraction'})  # Handle fractional parts if present
        if price_whole:
            # Combine the whole and fractional parts (if present)
            price_str = price_whole.get_text().replace(',', '').strip()
            if price_fraction:
                price_str += price_fraction.get_text().strip()
            current_price = float(price_str)
            print(f"Fetched Amazon price: ₹{current_price}")
            return current_price
        else:
            print("Price element not found on the page.")
    else:
        print(f"Failed to fetch the page for Amazon URL. Status code: {response.status_code}")
    return None

# Scrape prices from Flipkart
def fetch_price_flipkart(url):
    print(f"Fetching price for Flipkart URL: {url}")
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        price = soup.find('div', {'class': '_30jeq3'})
        if price:
            current_price = float(price.get_text().replace('₹', '').replace(',', ''))
            print(f"Fetched Flipkart price: ₹{current_price}")
            return current_price
    print(f"Failed to fetch price for Flipkart URL: {url}")
    return None

# Process price data
def check_price_changes(data):
    print("Checking for price changes...")
    changes = []
    for i, row in enumerate(data, start=1):  # No skipping, start index from 1
        print(f"Processing row {i}: {row}")
        try:
            url, prev_price = row[0].strip(), float(row[1].strip())
            print(f"URL: {url}, Previous Price: ₹{prev_price}")
            
            if "amazon" in url:
                current_price = fetch_price_amazon(url)
            elif "flipkart" in url:
                current_price = fetch_price_flipkart(url)
            else:
                print(f"Skipping unknown URL format: {url}")
                continue
            
            if current_price is not None:
                print(f"Current Price for {url}: ₹{current_price}")
                if current_price != prev_price:
                    print(f"Price change detected for {url}: Previous: ₹{prev_price}, Current: ₹{current_price}")
                    changes.append([url, prev_price, current_price])
                else:
                    print(f"No price change for {url}.")
        except Exception as e:
            print(f"Error processing row {i}: {
