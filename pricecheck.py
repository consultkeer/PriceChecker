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
            print(f"Error processing row {i}: {row}. Error: {e}")  # Corrected line
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

    # Parse email addresses
    emails = [email.strip() for email in email_data[0][0].split(',')]
    print(f"Parsed Emails: {emails}")

    # Check price changes
    changes = check_price_changes(url_data)

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
