import asyncio
from pyppeteer import launch
from bs4 import BeautifulSoup
import csv

chromium_path = r"C:\Users\gmedh\OneDrive\Documents\chrome-win\chrome-win\chrome.exe"

async def scrape_page(url):
    browser = await launch(
        executablePath=chromium_path,
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    page = await browser.newPage()
    await page.goto(url, {"waitUntil": "networkidle2"})
    
    # Get the full page content after rendering
    content = await page.content()
    await browser.close()
    return content

def parse_cars(html):
    soup = BeautifulSoup(html, 'html.parser')
    cars_container = soup.find('div', {'id': 'listCar-container'})
    if not cars_container:
        return []
    
    car_divs = cars_container.find_all('div', class_='newCarListUnit_contain')
    
    cars_data = []
    for car in car_divs:
        # Extract car details
        header = car.find('div', class_='newCarListUnit_header')
        if not header:
            continue
        
        # Car title
        title_a = header.find('a')
        car_title = title_a.text.strip() if title_a else ''
        
        meta_tags = car.find('div', class_='newCarListUnit_metaTags')
        brand = ''
        model = ''
        color = ''
        km = ''
        city = ''
        
        if meta_tags:
            meta_links = meta_tags.find_all('span', class_='newCarListUnit_metaLink')
            if len(meta_links) > 0:
                brand = meta_links[0].get_text(strip=True)
            if len(meta_links) > 1:
                model = meta_links[1].get_text(strip=True)
            
            meta_color = meta_tags.find('span', class_='mob_hidden')
            if meta_color:
                color = meta_color.get_text(strip=True)
            
            meta_spans = meta_tags.find_all('span', class_='newCarListUnit_metaTag')
            for mspan in meta_spans:
                text = mspan.get_text(strip=True)
                if 'كم' in text:
                    km = text
            # City might be the last meta_link after brand/model:
            if len(meta_links) > 2:
                city = meta_links[-1].get_text(strip=True)

        # Extract date and features
        other_data = car.find('div', class_='otherData_tags')
        date_posted = ''
        transmission = ''
        ac = ''
        power = ''
        remote = ''
        
        if other_data:
            date_div = other_data.find('div', class_='otherData_Date')
            if date_div and date_div.find('span'):
                date_posted = date_div.find('span').get_text(strip=True)
            
            feature_divs = other_data.find_all('div', class_='carTypeIcon_wrap')
            for fdiv in feature_divs:
                icon = fdiv.find('i', class_='tooltipDef')
                if icon and icon.has_attr('data-original-title'):
                    feature = icon['data-original-title'].strip()
                    if 'اوتوماتيك' in feature:
                        transmission = 'اوتوماتيك'
                    elif 'تكيف' in feature:
                        ac = 'تكيف'
                    elif 'باور' in feature:
                        power = 'باور'
                    elif 'ريموت كونترول' in feature:
                        remote = 'ريموت كونترول'
        
        # Price
        footer = car.find('div', class_='newCarListUnit_footer')
        price = ''
        if footer:
            price_div = footer.find('div', class_='main_price')
            if price_div and price_div.find('a'):
                price = price_div.find('a').get_text(strip=True)
        
        cars_data.append({
            'title': car_title,
            'brand': brand,
            'model': model,
            'color': color,
            'km': km,
            'city': city,
            'date_posted': date_posted,
            'transmission': transmission,
            'ac': ac,
            'power': power,
            'remote': remote,
            'price': price
        })
    
    return cars_data

async def main():
    base_url = "https://eg.hatla2ee.com/ar/car/page/"
    all_cars = []
    
    for page_num in range(1, 769):
        url = f"{base_url}{page_num}"
        html = await scrape_page(url)
        cars = parse_cars(html)
        
        if not cars:
            # If no cars found on this page, assume we've reached the end
            print(f"No cars found on page {page_num}. Ending scrape.")
            break
        
        print(f"Page {page_num}: Found {len(cars)} cars.")
        all_cars.extend(cars)
    
    # Save to CSV
    with open('cars_data.csv', 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            'title', 'brand', 'model', 'color', 'km', 'city', 
            'date_posted', 'transmission', 'ac', 'power', 'remote', 'price'
        ])
        writer.writeheader()
        for car in all_cars:
            writer.writerow(car)

asyncio.get_event_loop().run_until_complete(main())
