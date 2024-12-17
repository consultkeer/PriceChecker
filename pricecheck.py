import requests
import smtplib
import csv
import os
import subprocess  # For Git automation
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Fetch Google Sheet data
def fetch_google_sheet(sheet_id, gid):
    """
    Fetch data from a Google Sheet (CSV format) using the Sheet ID and GID.
    """
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

# Load previous prices from CSV
def load_previous_prices(file_path):
    if not os.path.exists(file_path):
        print(f"{file_path} not found. Creating a new one.")
        # Create an empty file
        with open(file_path, 'w') as file:
            pass
        return {}
    
    # Load the prices if the file exists
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        previous_prices = {row[0]: float(row[1]) for row in reader if len(row) == 2}
    print(f"Loaded previous prices: {previous_prices}")
    return previous_prices


# Save current prices to CSV
def save_current_prices(file_path, updated_prices):
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        for url, price in updated_prices.items():
            writer.writerow([url, price])
    print(f"Saved updated prices to {file_path}")


# Fetch product prices from supported websites
def fetch_price(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page for URL: {url}. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    try:
        # Amazon
        if "amazon" in url:
            price_whole = soup.find('span', {'class': 'a-price-whole'})
            price_fraction = soup.find('span', {'class': 'a-price-fraction'})
            if price_whole:
                price = price_whole.get_text().replace(',', '').strip()
                if price_fraction:
                    price += price_fraction.get_text().strip()
                return float(price)

        # Flipkart
        elif "flipkart" in url:
            price_element = soup.find('div', {'class': 'Nx9bqj'}) or soup.find('div', {'class': '_30jeq3'})
            if price_element:
                return float(price_element.get_text().replace('₹', '').replace(',', '').strip())

        # Agaro Lifestyle
        elif "agarolifestyle" in url:
            price_elements = soup.select('span.price.price--sale span')
            if price_elements:
                return float(price_elements[-1].get_text().replace('Rs.', '').replace(',', '').strip())

        # Lifelong India Online
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


# Check price changes
def check_price_changes(url_data, price_file):
    print("Checking for price changes...")
    previous_prices = load_previous_prices(price_file)
    changes = []
    updated_prices = {}

    for i, row in enumerate(url_data, start=1):
        url = row[0].strip()
        print(f"Processing URL {i}: {url}")
        prev_price = previous_prices.get(url, None)

        current_price = fetch_price(url)
        if current_price is not None:
            updated_prices[url] = current_price
            print(f"Fetched Price: ₹{current_price} for URL: {url}")

            # Compare prices
            if prev_price is not None and current_price != prev_price:
                print(f"Price change detected for {url}: Previous: ₹{prev_price}, Current: ₹{current_price}")
                changes.append([url, prev_price, current_price])
            elif prev_price is None:
                print(f"New product added: {url}")
        else:
            print(f"Could not fetch price for {url}")

    # Save updated prices
    save_current_prices(price_file, updated_prices)
    return changes


# Send email notifications
def send_email(to_email, changes):
    from_email = "consultkeerthan@gmail.com"
    from_password = "nevz gfbi ocqc sduh"
    subject = "Price Change Notification"
    body = "<html><body><ul>"

    for change in changes:
        url, prev_price, current_price = change
        product_name = url.split("/")[-1].replace("-", " ").replace("%20", " ")
        hyperlink = f"<a href='{url}'>{product_name}</a>"
        body += f"<li>{hyperlink}: Previous Price: ₹{prev_price}, Current Price: ₹{current_price}</li>"

    body += "</ul></body></html>"

    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(message)
        server.quit()
        print(f"Email successfully sent to {to_email}.")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")


# Commit and push updates to Git
def commit_and_push_to_git(file_path, commit_message="Update prices"):
    try:
        subprocess.run(["git", "add", file_path], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Successfully committed and pushed to Git.")
    except Exception as e:
        print(f"Failed to commit or push to Git: {e}")


# Main function
import os  # Required for file path handling

def main():
    print("Starting the Price Checker script...")
    # Google Sheet IDs
    sheet_id = "1rEWuNwnxkJ8nWyz__lqJbNvykOp5jjtm1iSIADdskQI"
    url_gid = "1012817683"
    email_gid = "1112713903"
    price_file = "prev_prices.csv"  # File to store prices locally

    # Print the absolute file path for debugging
    print(f"File will be saved to: {os.path.abspath(price_file)}")

    # Fetch product URLs and email addresses
    url_data = fetch_google_sheet(sheet_id, url_gid)
    email_data = fetch_google_sheet(sheet_id, email_gid)

    if not url_data or not email_data:
        print("Failed to retrieve data from Google Sheets.")
        return

    # Parse email addresses
    emails = [email.strip() for email in email_data[0][0].split(',')]
    print(f"Parsed Emails: {emails}")

    # Check price changes and save to prev_prices.csv
    changes = check_price_changes(url_data, price_file)

    # Notify users if changes detected
    if changes:
        print("Price changes detected. Sending notifications...")
        for email in emails:
            send_email(email, changes)
        commit_and_push_to_git(price_file, "Update product prices after script run")
    else:
        print("No price changes detected.")

    print("Price Checker script finished.")


if __name__ == "__main__":
    main()
