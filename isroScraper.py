import time
from bs4 import BeautifulSoup
import requests
import shutil
import random
import csv
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Mission:
    pass

def RemoveNewLineAndTrim(inp):
    inp=inp.replace('\n','')
    return inp.strip()

def SaveToCSV(missions):
    with open('ISROData.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        for mission in missions:
            writer.writerow([mission.title, mission.date, mission.vehicle, mission.orbit, 
            mission.payload, mission.remarks, mission.pageLink, 
            mission.galleryLink, mission.imageFileName,mission.OriginalImageLinks,mission.TwitterImageLinks])

def GetMissionPageData(missions,url):

    options = Options()
    options.headless = True
    driver = webdriver.Chrome()
    driver.get(url)

    
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Calculate the total number of pages
    pagination_element = soup.find("ul", {"class": "pagination test"})
    page_count = len(pagination_element.find_all("li"))

    for current_page in range(1, page_count + 1):
        rows = soup.find_all('table')[0].find("tbody").find_all("tr")

        for row in rows:
            mission = Mission()
            cells = row.find_all("td")
            mission.id = RemoveNewLineAndTrim(cells[0].get_text())
            mission.title = RemoveNewLineAndTrim(cells[1].get_text())
            mission.date = RemoveNewLineAndTrim(cells[2].get_text())
            mission.vehicle = RemoveNewLineAndTrim(cells[3].get_text())
            mission.payload = RemoveNewLineAndTrim(cells[4].get_text())
            mission.remarks = RemoveNewLineAndTrim(cells[5].get_text())

            mission.pageLink ='https://www.isro.gov.in/'+ cells[1].find_all('a', href=True)[0]['href']
            mission.galleryLink=''
            mission.imageFileName=''
            mission.OriginalImageLinks=[]
            mission.TwitterImageLinks=[]
            missions.append(mission)
            print('Scraped Data for : '+mission.title+', Id: '+mission.id)

        # Find the next page link
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        next_page_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//ul[@class='pagination test']/li/a[@data-i='{current_page + 1}']")))
        #next_page_link = driver.find_element("xpath",f"//ul[@class='pagination test']/li/a[@data-i='{current_page + 1}']")

        #next_page_link.click()
        driver.execute_script("arguments[0].click();", next_page_link)

        # Update the HTML source for the next iteration
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

    driver.quit()

    print('Main Page Scraped, proceeding to Scrape GalleryLinks')
    return missions

def GetGalleryLinks(missions):
    for mission in missions:
        page = requests.get(mission.pageLink)
        soup = BeautifulSoup(page.text, 'html.parser')
        if len(soup.select("a[href*=gallery]"))>0:
            mission.galleryLink = 'https://www.isro.gov.in/'+ soup.select("a[href*=gallery]")[0]['href']
        elif len(soup.select("a[href*=Gallery]"))>0:
            mission.galleryLink = 'https://www.isro.gov.in/'+ soup.select("a[href*=Gallery]")[0]['href']
        
    print('GalleryLinks Scraped, visiting each page to gather image links')
    return missions

def GetImageLinks(missions):
    for mission in missions:
        print(mission.id)
        if len(mission.galleryLink)>2:
            response = requests.get(mission.galleryLink)
            soup = BeautifulSoup(response.text, 'html.parser')
            tempImageList=[]

            for links in soup.find_all("a"):
                link = links["href"]
                if 'jpg' in link:
                    tempImageList.append('https://www.isro.gov.in'+link)

            print('ImageLinks Gathered for Mission : '+mission.title+', Id: '+mission.id)
            mission.OriginalImageLinks = tempImageList

    return missions

async def download_image(url, file_name):
    res = requests.get(url, stream=True)

    if res.status_code == 200:
        with open(file_name, 'wb') as f:
            shutil.copyfileobj(res.raw, f)
        print(f'Image successfully Downloaded: {file_name}')
    else:
        print(f'Image could not be retrieved: {url}')

async def DownloadImages(missions):
    tasks = []
    for mission in missions:
        for url in mission.OriginalImageLinks:
            file_name = 'images\\' + mission.title.replace('\\','').replace('/','').replace(' ','') + (str)(random.randint(1000,9999)) + '.jpg'
            mission.imageFileName = file_name

            task = asyncio.create_task(download_image(url, file_name))
            tasks.append(task)

    await asyncio.gather(*tasks)

    return missions

async def main(urls):
    missions=[]
    for url in urls:
        print('Scraping - '+url)
        missions = GetMissionPageData(missions,url)
        missions = GetGalleryLinks(missions)
        missions = GetImageLinks(missions)

    missions = await DownloadImages(missions)
    #SaveToCSV(missions)

    print('***********DONE**********')

urls=['https://www.isro.gov.in/PSLV_Launchers.html']
#'https://www.isro.gov.in/PSLV_Launchers.html','https://www.isro.gov.in/GSLV_Launchers.html','https://www.isro.gov.in/LVM3_Launchers.html','https://www.isro.gov.in/SSLV_Launchers.html'
asyncio.run(main(urls))
