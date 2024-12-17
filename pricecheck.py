import requests
import smtplib
import csv
import os
import subprocess  # For Git commands
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load previous prices from CSV
def load_previous_prices(file_path):
    if not os.path.exists(file_path):
        print("Previous prices file not found. Creating a new one.")
        return {}
    
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        previous_prices = {row[0]: float(row[1]) for row in reader if len(row) == 2}
    print(f"Loaded previous prices: {previous_prices}")
    return previous_prices

# Fetch Google Sheet data
def fetch_google_sheet(sheet_id, gid):
    print(f"Fetching data from Google Sheet: Sheet ID {sheet_id}, GID {gid}")
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    response = requests.get(url)
    if response.status_code == 200:
        print("Successfully fetched Google Sheet data.")
        decoded_content = response.content.decode('utf-8')
        reader = csv.reader(decoded_content.splitlines())
        data = [row for row in reader]
        print(f"Fetched {len(data)} rows from the sheet.")
        return data
    else:
        print(f"Failed to fetch data from Sheet GID {gid}. Status code: {response.status_code}")
        return []

# Unified price-fetching function
def fetch_price(url):
    """
    Unified function to fetch product prices from supported websites:
    Amazon, Flipkart, Agaro Lifestyle, Lifelong India Online.
    """
    print(f"Fetching price for URL: {url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        # Amazon Price
        if "amazon" in url:
            price_whole = soup.find('span', {'class': 'a-price-whole'})
            price_fraction = soup.find('span', {'class': 'a-price-fraction'})
            if price_whole:
                price = price_whole.get_text().replace(',', '').strip()
                if price_fraction:
                    price += price_fraction.get_text().strip()
                return float(price)

        # Flipkart Price
        elif "flipkart" in url:
            price_element = soup.find('div', {'class': 'Nx9bqj'}) or soup.find('div', {'class': '_30jeq3'})
            if price_element:
                return float(price_element.get_text().replace('₹', '').replace(',', '').strip())

        # Agaro Lifestyle Price
        elif "agarolifestyle" in url:
            price_elements = soup.select('span.price.price--sale span')
            if price_elements:
                return float(price_elements[-1].get_text().replace('Rs.', '').replace(',', '').strip())

        # Lifelong India Online Price
        elif "lifelongindiaonline" in url:
            price_element = soup.find('h5', {'class': 'hind-semi-bold'})
            if price_element:
                return float(price_element.get_text().replace('Rs.', '').replace(',', '').strip())

        else:
            print(f"Unsupported website for URL: {url}")
            return None

    except Exception as e:
        print(f"Error fetching price for {url}: {e}")
        return None

# Process price data
def check_price_changes(data, price_file):
    print("Checking for price changes...")
    previous_prices = load_previous_prices(price_file)
    changes = []
    updated_prices = {}

    for i, row in enumerate(data, start=1):
        print(f"Processing row {i}: {row}")
        try:
            url = row[0].strip()
            prev_price = previous_prices.get(url, None)
            print(f"URL: {url}, Previous Price: ₹{prev_price if prev_price else 'N/A'}")

            current_price = fetch_price(url)
            if current_price is not None:
                updated_prices[url] = current_price
                print(f"Current Price for {url}: ₹{current_price}")

                if prev_price is not None and current_price != prev_price:
                    print(f"Price change detected: Previous: ₹{prev_price}, Current: ₹{current_price}")
                    changes.append([url, prev_price, current_price])
                elif prev_price is None:
                    print(f"New product added: {url}")
            else:
                print(f"Could not fetch price for {url}.")
        except Exception as e:
            print(f"Error processing row {i}: {row}. Error: {e}")

    # Save updated prices back to the CSV file
    save_current_prices(price_file, updated_prices)
    return changes

# Save current prices to CSV
def save_current_prices(file_path, updated_prices):
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        for url, price in updated_prices.items():
            writer.writerow([url, price])
    print(f"Saved updated prices to {file_path}")

# Send email
def send_email(to_email, changes):
    print(f"Preparing to send email to {to_email}...")
    from_email = "consultkeerthan@gmail.com"
    from_password = "nevz gfbi ocqc sduh"  # Replace with your App Password
    subject = "Price Change Notification"

    body = "The following items have price changes:\n\n"
    body += "<html><body><ul>"

    for change in changes:
        url, prev_price, current_price = change
        product_name = url.split("/")[-1].replace("-", " ").replace("%20", " ")  # Extract and clean product name
        product_name = product_name[:60]  # Optional: Truncate to 60 characters for neatness
        hyperlink = f"<a href='{url}'>{product_name}</a>"
        body += f"<li>{hyperlink}: Previous Price: ₹{prev_price}, Current Price: ₹{current_price}</li>"

    body += "</ul></body></html>"

    # Email content setup
    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html'))  # Note: Set content type as HTML

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(message)
        server.quit()
        print(f"Email successfully sent to {to_email}.")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

# Main function
def main():
    print("Starting the Price Checker script...")
    # Google Sheet IDs
    sheet_id = "1rEWuNwnxkJ8nWyz__lqJbNvykOp5jjtm1iSIADdskQI"
    url_gid = "1012817683"
    email_gid = "1112713903"
    price_file = "previous_prices.csv"  # Local file to store prices

    # Fetch data
    url_data = fetch_google_sheet(sheet_id, url_gid)
    email_data = fetch_google_sheet(sheet_id, email_gid)

    if not url_data or not email_data:
        print("Failed to retrieve data from Google Sheets.")
        return

    # Parse email addresses
    emails = [email.strip() for email in email_data[0][0].split(',')]
    print(f"Parsed Emails: {emails}")

    # Check price changes
    changes = check_price_changes(url_data, price_file)

    # Notify users
    if changes:
        print("Detected price changes. Sending notifications...")
        for email in emails:
            send_email(email, changes)
    else:
        print("No price changes detected.")

    print("Price Checker script finished.")

if __name__ == "__main__":
    main()
