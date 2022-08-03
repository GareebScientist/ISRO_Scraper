require('dotenv').config();
const request = require("request-promise");
const cheerio = require("cheerio");
const fs = require('fs');
const client = require('https');
const path = require('path');
const Twitter = require("twitter")
const dotenv = require("dotenv")

async function main() {

    //Gather list of launches and mission page links
    let result = await request.get("https://www.isro.gov.in/launchers/pslv");
    let $ = cheerio.load(result);
    let missions = [];

    $("#block-system-main > div > div > div > div > div > div > div > div.span12.well.well-large > div.span8 > div > div > table > tbody > tr").each((index, element) => {

        if (index === 0) return true;
        let tds = $(element).find("td");
        let id = RemoveNewLineAndTrim($(tds[0]).text());
        let Event = RemoveNewLineAndTrim($(tds[1]).text());
        let MissionPageLink = "https://www.isro.gov.in" + ($(tds[1]).find("a").attr("href"));
        let Date = RemoveNewLineAndTrim($(tds[2]).text());
        let Vehicle = RemoveNewLineAndTrim($(tds[3]).text());
        let Orbit = RemoveNewLineAndTrim($(tds[4]).text());
        let Satellite = RemoveNewLineAndTrim($(tds[5]).text());
        let tableRow = { id, Event, Date, Vehicle, Orbit, Satellite, MissionPageLink };
        missions.push(tableRow);
    });

    //get Gallery Links by visiting mission pages
    for (var i = 0; i < missions.length; i++) {

        let result = await request.get(missions[i].MissionPageLink);
        let $ = cheerio.load(result);
        let GalleryLink = "https://www.isro.gov.in" + $('li:contains("Gallery")').find("a").attr("href");

        if (GalleryLink != 'https://www.isro.gov.inundefined')
            missions[i].GalleryLink = GalleryLink;
        else
            missions[i].GalleryLink = null;

        //console.log(missions[i].GalleryLink);
    }

    const client = new Twitter({
        consumer_key: process.env.CONSUMER_KEY,
        consumer_secret: process.env.CONSUMER_SECRET,
        access_token_key: process.env.ACCESS_TOKEN_KEY,
        access_token_secret: process.env.ACCESS_TOKEN_SECRET
    })

    await client.post("statuses/update", { status: "I tweeted from Node.js!" }, function (error, tweet, response) {
        if (error) {
            console.log(error)
        } else {
            console.log(tweet)
        }
    })


    //downloading the Images from respective gallery links
    for (var i = 0; i < missions.length; i++) {

        if (missions[i].GalleryLink != null) {
            let result = await request.get(missions[i].GalleryLink);
            let $ = cheerio.load(result);
            missions[i].TwitterImages=[];

            $('a').each(function () { // Go through all links
                var imgName=null;
                if ($(this).attr("href").includes("jpg")) {
                    imgName = "temp\\"+ missions[i].Vehicle + Math.random(1000)+".jpg";
                }
                if( $(this).attr("href").includes("png"))
                {
                    imgName = "temp\\"+ missions[i].Vehicle + Math.random(1000)+".png";
                }

                if(imgName!=null)
                {
                    downloadImage($(this).attr("href"), imgName);

                    //tweet upload
                    //var imageData = fs.readFileSync(imgName);
                    // client.post("media/upload", {media: imageData}, function(error, media, response) {
                    //     if (error) {
                    //       console.log(error)
                    //     } else {
                    //         missions[i].TwitterImages.push(media.media_id_string);
                    //     }
                    //   })

                }
                
            });
            console.log('Download complete for ' + missions[i].id)
        }
    }

}

function RemoveNewLineAndTrim(text) {
    text = text.replace("\n", "");
    text = text.trim();
    return text;
}

function downloadImage(url, name) {
    const file = fs.createWriteStream(name);
    //console.log(url);
    try {
        const request = client.get(url, function (response) {
            response.pipe(file);

            // after download completed close filestream
            file.on("finish", () => {
                file.close();
                //console.log("Download Completed for " + name);
            });
        });
    } catch (e) { }
}

main();