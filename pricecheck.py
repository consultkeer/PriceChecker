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
        reader = csv.reader(decoded_content.splitlines())
        data = [row for row in reader]
        print(f"Fetched {len(data)} rows from the sheet.")
        return data
    else:
        print(f"Failed to fetch data from Sheet GID {gid}. Status code: {response.status_code}")
        return []

# Scrape prices
def fetch_price_amazon(url):
    print(f"Fetching price for Amazon URL: {url}")
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        price = soup.find('span', {'class': 'a-price-whole'})
        if price:
            current_price = float(price.get_text().replace(',', ''))
            print(f"Fetched Amazon price: ₹{current_price}")
            return current_price
    print(f"Failed to fetch price for Amazon URL: {url}")
    return None

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
    for row in data[1:]:  # Skip header row
        url, prev_price = row[0], float(row[1])
        print(f"Processing URL: {url} with Previous Price: ₹{prev_price}")
        
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
    return changes

# Send email
def send_email(to_email, changes):
    print(f"Preparing to send email to {to_email}...")
    from_email = "consultkeerthan@gmail.com"
    from_password = "nevz gfbi ocqc sduh"
    subject = "Price Change Notification"
    body = "The following items have price changes:\n\n"
    for change in changes:
        body += f"URL: {change[0]}\nPrevious Price: ₹{change[1]}\nCurrent Price: ₹{change[2]}\n\n"

    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

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

    # Fetch data
    url_data = fetch_google_sheet(sheet_id, url_gid)
    email_data = fetch_google_sheet(sheet_id, email_gid)

    if not url_data or not email_data:
        print("Failed to retrieve data from Google Sheets.")
        return

    print(f"URL Data: {url_data}")
    print(f"Email Data: {email_data}")

    # Check price changes
    changes = check_price_changes(url_data)

    # Notify users
    if changes:
        print("Detected price changes. Sending notifications...")
        emails = [row[0] for row in email_data[1:]]  # Skip header row
        for email in emails:
            send_email(email, changes)
    else:
        print("No price changes detected.")

    print("Price Checker script finished.")

if __name__ == "__main__":
    main()
