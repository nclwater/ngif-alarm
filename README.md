# NGIF Alarm

![build](https://github.com/fmcclean/ngif-alarm/workflows/build/badge.svg)

Python script that checks the NGIF database and sends emails

## Usage
`docker run -d --env MONGO_URI=mongodb://user:password@hostname:27017/database?authSource=admin --env EMAIL_USERNAME=user@domain.com --env EMAIL_PASSWORD=pass --env INTERVAL=60 --restart unless-stopped --name ngif-alarm fmcclean/ngif-alarm` 

## Dependencies
`pip install -r requirements.txt`
