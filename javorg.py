import os
import re
import requests
from bs4 import BeautifulSoup
import shutil

# Get the current working directory where the script is running
folder_path = os.getcwd()

# Regex pattern to match any word followed by a hyphen and digits (code format)
pattern = re.compile(r'[a-zA-Z]+-\d+')

# Characters that are not allowed in Windows filenames
INVALID_CHARACTERS = r'[<>:"/\\|?*]'

# Function to clean up the title and remove invalid characters
def clean_title(title):
    # Remove invalid characters
    clean_title = re.sub(INVALID_CHARACTERS, '', title)
    
    # Optionally, truncate the title if it exceeds a certain length (e.g., 150 characters)
    max_length = 150
    if len(clean_title) > max_length:
        clean_title = clean_title[:max_length] + "..."
    
    return clean_title

# Function to scrape the data from the website
def scrape_data(code):
    url = f"https://www.javdatabase.com/movies/{code}/"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        header = soup.find('header', class_='entry-header')
        if header:
            title = header.find('h1').text.strip()
        else:
            title = None
        
        # Extract cover image from the specific <div> containing it
        cover_image_h2 = soup.find('h2', class_='subhead', string=re.compile(f"{code} Cover"))
        if cover_image_h2:
            cover_image = cover_image_h2.find_next('div').find('img')
            if cover_image:
                # Get the image URL from either src or data-src
                cover_image_url = cover_image.get('data-src', cover_image.get('src'))
            else:
                cover_image_url = None
        else:
            cover_image_url = None
        
        # Extract all screenshots (from <a> tags)
        screenshot_urls = []
        for a_tag in soup.find_all('a', href=True):
            if '.jpg' in a_tag['href']:
                screenshot_urls.append(a_tag['href'])
        
        return title, cover_image_url, screenshot_urls
    
    return None, None, None

# Function to download an image from a URL
def download_image(url, folder_path, image_name):
    image_path = os.path.join(folder_path, image_name)
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(image_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Downloaded: {image_name}")
    else:
        print(f"Failed to download: {url}")

# Function to rename, move the file, and download images
def process_file(filename, title, code, cover_image_url, screenshot_urls):
    # Clean the title to make it safe for Windows filenames
    clean_title_str = clean_title(title)
    
    # Create the new folder for the code
    new_folder_path = os.path.join(folder_path, code)
    os.makedirs(new_folder_path, exist_ok=True)
    
    # New file name with clean title
    new_filename = os.path.join(new_folder_path, f"{clean_title_str}{os.path.splitext(filename)[1]}")
    
    old_file_path = os.path.join(folder_path, filename)
    
    try:
        # Rename and move the file
        shutil.move(old_file_path, new_filename)
        print(f"Moved and renamed file to: {new_filename}")
    except OSError as e:
        print(f"Error renaming file: {e}")
    
    # Download cover image as 'a_cover.webp'
    if cover_image_url:
        download_image(cover_image_url, new_folder_path, f"a_cover.webp")
    
    # Download screenshots
    for i, screenshot_url in enumerate(screenshot_urls, 1):
        download_image(screenshot_url, new_folder_path, f"{code}_screenshot_{i}.jpg")

# Loop through the files in the current directory
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)
    
    # Check if it's a file (skip directories)
    if os.path.isfile(file_path):
        # Search for the code pattern within the filename
        match = pattern.search(filename)
        
        if match:
            code = match.group()  # Extract the matched code
            print(f"Processing file: {filename} with code: {code}")
            
            # Scrape the title, cover image, and screenshots from the webpage
            title, cover_image_url, screenshot_urls = scrape_data(code)
            
            if title:
                # Process the file: rename, move, and download images
                process_file(filename, title, code, cover_image_url, screenshot_urls)
            else:
                print(f"Could not retrieve title for {code}")
        else:
            print(f"Skipping file: {filename} (no matching code pattern)")
    else:
        print(f"Skipping directory: {filename}")
