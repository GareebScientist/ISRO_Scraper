from bs4 import BeautifulSoup
import requests
import shutil
import random
import csv

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
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    rows = soup.find_all('table')[-1].find("tbody").find_all("tr")

    for row in rows:
        mission = Mission()
        cells = row.find_all("td")
        mission.id = RemoveNewLineAndTrim(cells[0].get_text())
        mission.title = RemoveNewLineAndTrim(cells[1].get_text())
        mission.date = RemoveNewLineAndTrim(cells[2].get_text())
        mission.vehicle = RemoveNewLineAndTrim(cells[3].get_text())
        if 'gslv-mk-iii' in url:
            mission.orbit = ''
            mission.payload = RemoveNewLineAndTrim(cells[4].get_text())
            mission.remarks = RemoveNewLineAndTrim(cells[5].get_text())
        else:
            mission.orbit = RemoveNewLineAndTrim(cells[4].get_text())
            mission.payload = RemoveNewLineAndTrim(cells[5].get_text())
            mission.remarks = RemoveNewLineAndTrim(cells[6].get_text())

        mission.pageLink ='https://www.isro.gov.in'+ cells[1].find_all('a', href=True)[0]['href']
        mission.galleryLink=''
        mission.imageFileName=''
        mission.OriginalImageLinks=[]
        mission.TwitterImageLinks=[]
        missions.append(mission)
        print('Scraped Data for : '+mission.title+', Id: '+mission.id)

    print('Main Page Scraped, proceeding to Scrape GalleryLinks')
    return missions

def GetGalleryLinks(missions):
    for mission in missions:
        page = requests.get(mission.pageLink)
        soup = BeautifulSoup(page.text, 'html.parser')
        if len(soup.select("a[href*=gallery]"))>0:
            mission.galleryLink = 'https://www.isro.gov.in'+ soup.select("a[href*=gallery]")[0]['href']
        
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
                    tempImageList.append(link)

            print('ImageLinks Gathered for Mission : '+mission.title+', Id: '+mission.id)
            mission.OriginalImageLinks = tempImageList

    return missions

def DownloadImages(missions):
    for mission in missions:
        for url in mission.OriginalImageLinks:
            file_name = 'D:\DownloadedImages\\' + mission.vehicle + (str)(random.randint(1000,9999)) + '.jpg'
            mission.imageFileName = file_name

            res = requests.get(url, stream = True)

            if res.status_code == 200:
                with open(file_name,'wb') as f:
                    shutil.copyfileobj(res.raw, f)
                print('Image sucessfully Downloaded: ',file_name)
            else:
                print('Image Couldn\'t be retrieved')

    return missions

def main(urls):
    missions=[]
    for url in urls:
        print('Scraping - '+url)
        missions = GetMissionPageData(missions,url)
        missions = GetGalleryLinks(missions)
        missions = GetImageLinks(missions)
        #missions = DownloadImages(missions)
    
    SaveToCSV(missions)
    print('***********DONE**********')

urls=['https://www.isro.gov.in/launchers/pslv','https://www.isro.gov.in/launchers/gslv','https://www.isro.gov.in/launchers/gslv-mk-iii']
main(urls)