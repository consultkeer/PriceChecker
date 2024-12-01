import requests
import smtplib
import csv
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Fetch Google Sheet data
def fetch_google_sheet(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    response = requests.get(url)
    if response.status_code == 200:
        decoded_content = response.content.decode('utf-8')
        reader = csv.reader(decoded_content.splitlines())
        return [row for row in reader]
    else:
        print(f"Failed to fetch data from Sheet GID {gid}. Status code: {response.status_code}")
        return []

# Scrape prices
def fetch_price_amazon(url):
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        price = soup.find('span', {'class': 'a-price-whole'})
        if price:
            return float(price.get_text().replace(',', ''))
    print(f"Failed to fetch price for {url}")
    return None

def fetch_price_flipkart(url):
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        price = soup.find('div', {'class': '_30jeq3'})
        if price:
            return float(price.get_text().replace('₹', '').replace(',', ''))
    print(f"Failed to fetch price for {url}")
    return None

# Process price data
def check_price_changes(data):
    changes = []
    for row in data[1:]:  # Skip header row
        url, prev_price = row[0], float(row[1])
        if "amazon" in url:
            current_price = fetch_price_amazon(url)
        elif "flipkart" in url:
            current_price = fetch_price_flipkart(url)
        else:
            continue
        
        if current_price is not None and current_price != prev_price:
            changes.append([url, prev_price, current_price])
    return changes

# Send email
def send_email(to_email, changes):
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
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

# Main function
def main():
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

    # Check price changes
    changes = check_price_changes(url_data)

    # Notify users
    if changes:
        emails = [row[0] for row in email_data[1:]]  # Skip header row
        for email in emails:
            send_email(email, changes)
    else:
        print("No price changes detected.")

if __name__ == "__main__":
    main()
