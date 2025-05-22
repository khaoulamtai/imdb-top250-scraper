import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Set up the Selenium WebDriver with options
service = ChromeService(executable_path=ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode
options.add_argument('--disable-blink-features=AutomationControlled')  # Avoid detection

# Add a user-agent string to mimic a real browser
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(service=service, options=options)

# Define the URL of the IMDb Top 250 Movies page
base_url = 'https://www.imdb.com/chart/top'

try:
    # Fetch the main page
    driver.get(base_url)

    # Wait for the movie containers to be visible
    try:
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.ipc-title__text')))
    except TimeoutException:
        print("Timeout occurred while waiting for the page to load.")
        raise

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Find the movie containers
    movies = soup.select('.ipc-metadata-list-summary-item__tc')
    if not movies:
        print("No movie containers found. Check the selector.")
        raise Exception("No movie containers found.")

    # Extract movie details
    movies_data = []
    for movie in movies:
        title = movie.select_one('.ipc-title__text').text.strip()
        href = "https://www.imdb.com" + movie.select_one('.ipc-title__text').find_parent('a')['href']
        year = movie.select('.cli-title-metadata-item')[0].text.strip()
        length = movie.select('.cli-title-metadata-item')[1].text.strip()
        rating = movie.select_one('.ipc-rating-star--rating').text.strip()

        try:
            time.sleep(random.uniform(1, 3))  
            driver.set_page_load_timeout(30)  # 30 seconds
            driver.get(href)
        except TimeoutException:
            print(f"Timeout while loading {href}. Skipping...")
            continue


        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-testid="plot-xl"], span[data-testid="plot-xs_to_m"]')))
        detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Introduction
        intro_tag = detail_soup.select_one('span[data-testid="plot-xl"]') or detail_soup.select_one('span[data-testid="plot-xs_to_m"]')
        introduction = intro_tag.text.strip() if intro_tag else 'N/A'

        # Genres
        genre_tags = detail_soup.select('div.ipc-chip-list__scroller a.ipc-chip--on-baseAlt span.ipc-chip__text')
        genres = [g.text.strip() for g in genre_tags] if genre_tags else []

        # Directors
        director = []
        director_block = detail_soup.select_one('li[data-testid="title-pc-principal-credit"]:has(span:contains("Director"))')
        if director_block:
            director = [a.text.strip() for a in director_block.select('a')]

        # Stars
        stars_block = detail_soup.select_one('li[data-testid="title-pc-principal-credit"]:has(span:contains("Stars"))')
        if stars_block:
            stars = [a.text.strip() for a in stars_block.select('a')]
        else:
            stars = [a.text.strip() for a in detail_soup.select('a[data-testid="title-cast-item__actor"]')[:3]]

        # Append the data to the list
        movies_data.append([title, href, year, rating, length, genres, introduction, director, stars])

        print(f"Scraping: {title}")

    # Define the columns for the DataFrame
    columns = ['Title','Href', 'Year', 'Rating', 'Length', 'Genres', 'Introduction', 'Director', 'Stars']

    # Create a DataFrame from the list of movies data
    df = pd.DataFrame(movies_data, columns=columns)

    # Save the DataFrame to a CSV file
    df.to_csv('imdb_top_250_movies_advanced.csv', index=False)
    print("Data has been saved to imdb_top_250_movies_advanced.csv")

finally:
    # Close the WebDriver
    driver.quit()