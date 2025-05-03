
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime, timezone
import csv
import boto3
import tempfile
from dotenv import load_dotenv
import os

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--headless")
options.add_argument("--disable-gpu")

user_data_dir = tempfile.mkdtemp()
options.add_argument(f"--user-data-dir={user_data_dir}")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
print(driver.title)

URL = "https://justjoin.it/job-offers/all-locations/ai"
# URL = "https://justjoin.it/job-offers/all-locations/javascript"  # Podmień na właściwy adres strony
driver.get(URL)
wait = WebDriverWait(driver, 10)
all_links = set()
SCROLL_PAUSE_TIME = 4
SCROLL_LIMIT = 30  

for i in range(SCROLL_LIMIT):
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.MuiBox-root.css-1jbajow")))
    except:
        print("No links with sections. Ending...")
        break

    new_links = set()
    for elem in driver.find_elements(By.CSS_SELECTOR, "div.MuiBox-root.css-1jbajow a"):
        try:
            href = elem.get_attribute("href")
            if href:
                new_links.add(href)
        except:
            continue

    all_links.update(new_links)

    print(f"Found links: {len(all_links)}")

    driver.execute_script("window.scrollBy(0, window.innerHeight);")
    time.sleep(SCROLL_PAUSE_TIME)


job_offers = []  
relation_table = []

for index, link in enumerate(all_links):
    print(f"➡️ ({index+1}/{len(all_links)}) Processing: {link}")
    driver.get(link) 
    time.sleep(3)

    try:
        title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()  # Pobierz tytuł
    except:
        title = "Brak tytułu"

    try:
        company = driver.find_element(By.CSS_SELECTOR, "h2").text.strip()  # Pobierz nazwę firmy
    except:
        company = "Brak informacji o firmie"

    try:
        location = driver.find_element(By.CSS_SELECTOR, "span.css-1o4wo1x").text.strip()  # Pobierz lokalizację
    except:
        location = "Brak lokalizacji"

    try:
        type_of_work = driver.find_elements(By.CSS_SELECTOR, "div.css-ktfb40")[0].text.strip()  # Pobierz lokalizację
    except:
        type_of_work = "Brak typu pracy"

    try:
        experience = driver.find_elements(By.CSS_SELECTOR, "div.css-ktfb40")[1].text.strip()  # Pobierz lokalizację
    except:
        experience = "Brak doświadczenia"

    try:
        employment_type = driver.find_elements(By.CSS_SELECTOR, "div.css-ktfb40")[2].text.strip()  # Pobierz lokalizację
    except:
        employment_type = "Brak typu umowy"

    try:
        operating_mode = driver.find_elements(By.CSS_SELECTOR, "div.css-ktfb40")[3].text.strip()  # Pobierz lokalizację
    except:
        operating_mode = "Brak info o zdalnej pracy"

    try:
        salary = driver.find_element(By.CSS_SELECTOR, "span.css-1pavfqb").text.strip().replace("<span>", "")  # Pobierz lokalizację
    except:
        salary = "Missing salary"

    skill_names = []

    try:
        skill_h4 = driver.find_elements(By.CSS_SELECTOR, "div.css-qsaw8 h4")  
        for el in skill_h4:
            skill_names.append(el.text.strip())
    except:
        skill_names = "Brak nazw skilli"

    skills_need_or_nice_to_have = []

    try:
        skills_span = driver.find_elements(By.CSS_SELECTOR, "div.css-qsaw8 span")  
        for el in skills_span:
            skills_need_or_nice_to_have.append(el.text.strip())
    except:
        skills_need_or_nice_to_have = "Brak info o zdalnej pracy"

    skill_levels = []

    try:
        skill_div_elements = driver.find_elements(By.CSS_SELECTOR, "div.css-qsaw8")
        for div in skill_div_elements:
            try:
                ul_element = div.find_element(By.CSS_SELECTOR, "ul.css-1qii1b7")
                skill_levels.append(len(ul_element.find_elements(By.CSS_SELECTOR, "li.css-j1kr6i")))  
            except:
                skill_levels.append("Nan") 

    except:
        skill_levels = "Brak wartości skilla!"

    job_offers.append({
        "offer_id": index,
        "title": title,
        "company": company,
        "location": location,
        "salary": salary,
        "link": link,
        "type_of_work": type_of_work,
        "experience": experience,
        "employment_type": employment_type,
        "operating_mode": operating_mode,
        "skill_names": skill_names,
        "skills_need_or_nice_to_have": skills_need_or_nice_to_have,
        "skill_levels": skill_levels,
        "scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    })

    print(f"✅ Offer: offer_id={index} {datetime.now(timezone.utc)} | {type_of_work} | {experience} | {salary} | {employment_type} | {operating_mode} | {title} | {company} | {location}")
    print(f"{skill_names} | {skills_need_or_nice_to_have} {skill_levels}")
    print("=========================================================")
    driver.back()  
    time.sleep(2)

print("\n📌 Found job offers:")
for offer in job_offers:
    print(f"{offer['title']} | {offer['company']} | {offer['location']} | {offer['link']}")
    print("====================================================================================")

all_skills = set()
for offer in job_offers:
    all_skills.update(offer["skill_names"]) 

all_skills = sorted(all_skills)  
processed_offers = []

for index, offer in enumerate(job_offers):
    row = {
        "offer_id": index,
        "title": offer["title"],
        "company": offer["company"],
        "location": offer["location"],
        "salary": offer["salary"],
        "link": offer["link"],
        "type_of_work": offer["type_of_work"],
        "experience": offer["experience"],
        "employment_type": offer["employment_type"],
        "operating_mode": offer["operating_mode"],
        "scraped_at": offer["scraped_at"]
    }
    
    for skill in all_skills:
        row[skill] = 1 if skill in offer["skill_names"] else 0
    
    processed_offers.append(row)

now = datetime.now()
formatted_date = now.strftime("%d_%m_%y")
csv_filename_general = f"{formatted_date}oferty_one_hot_ai_ml.csv"

with open(csv_filename_general, "w", newline="", encoding="utf-8") as file:
    fieldnames = list(processed_offers[0].keys()) 
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    
    writer.writeheader() 
    writer.writerows(processed_offers)  

print(f"Data saved in {csv_filename_general} 🎉")
print( "All skills:", all_skills)
print("Length of array of all skills:", len(all_skills))

for index, offer in enumerate(job_offers):
    for j, skill in enumerate(offer["skill_names"]):
        row = {
            "offer_id": index,
            "skill_name": skill,
            "skill_level": offer["skill_levels"][j],
            "skill_level_name": offer["skills_need_or_nice_to_have"][j]
        }
        relation_table.append(row)

csv_filename_skills_scores = f"{formatted_date}tabela_relacyjna_ai_ml.csv"

with open(csv_filename_skills_scores, "w", newline="", encoding="utf-8") as file:
    fieldnames = list(relation_table[0].keys())  
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()  
    writer.writerows(relation_table) 

load_dotenv() 

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION')

print("Inicialize boto3 client")

s3_client = boto3.client(
    service_name="s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

response = s3_client.upload_file(csv_filename_general, AWS_S3_BUCKET_NAME, csv_filename_general)
response = s3_client.upload_file(csv_filename_skills_scores, AWS_S3_BUCKET_NAME, csv_filename_skills_scores)

driver.quit()
