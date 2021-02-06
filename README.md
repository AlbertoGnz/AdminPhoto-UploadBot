# AdminPhoto-UploadBot
Bot created to automate the uploading process to AdminPhoto platform.
Project to automate gallery creation and upload

Automated with Python and Selenium. Allows me to drop folders with raw files, and automatically resize, watemark, extract gallery title and password from the foldername, create the gallery with this data and upload it to Sunshine Photo Cart plugin in Wordpress.

# Before run.
Change your blog URL, login details, mail (Including SMTP and login details), and notification receiver mail.
Make sure to point correct path to selenium driver.


# How to run it.
I have a cron job to run test.py everyday early morning.
Simply drop the folders that contains images to "En cola" (Means on queue) with the follow name mask: email. Gallery
The "." separates the password and the gallery tittle
Customer gets notified when the gallery is published.
If everything runs correctly, you will get the galleries created automatically and the folder will be moved to "Procesados" (Processed)
In case of error, the folder will be moved to "Con errores" (With errors)
Expect and email with the job output. Sucess or error notification are delivered on each run to the defined notification mail.
