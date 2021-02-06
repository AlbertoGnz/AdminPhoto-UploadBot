import time
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
import os
import glob
import smtplib, ssl
import email.message
from shutil import rmtree
from shutil import move
from tabulate import tabulate
from PIL import Image, ExifTags
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

# ============================== INI VARIABLES ==================================
##AdminPhoto
url_login = "https://software.adminphoto.com/galerias2"					#LoginURL
url_create = "https://software.adminphoto.com/galerias2/create"
user = "USER"
passw = "PASSWORD"

##Mail
port = 587  # For SSL
smtp_server = "smtp.server.com"
sender_email = "robot@mail.com"  # Enter your address
password = "PasswordExample"


##Path
production_mode = True
if production_mode:
    receiver_email = ["notifications@mail.com"]
  
    path = "/RobotWeb_AdminPhoto/en_cola"
    errors = "/RobotWeb_AdminPhoto/con_errores"
    processed = "/RobotWeb_AdminPhoto/procesados"
    water_mark = "/RobotWeb_AdminPhoto/watemark.png"

    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')

    
else:
    receiver_email = ["notifications@mail.com"]
    
    cwd = os.getcwd()
    path = os.path.join(os.getcwd(), r"en_cola")
    errors = os.path.join(os.getcwd(), r"con_errores")
    processed = os.path.join(os.getcwd(), r"procesados")
    water_mark = os.path.join(os.getcwd(),  "watemark.png")
    
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    

##Variables
error_notification = []
sucess_notification = []
dic_exif = {
    1: 0,
    8: 90,
    3: 180,
    6: -90}

python_watemark = True
allow_comments = True
block_after_seleccion = True
add_watemark = False
send_customer_email = True
extra_image = False

# ============================== FUNCTIONS ==================================
def login(user, passw):
    username = driver.find_element_by_name("email")	
    username.send_keys(user)
    password = driver.find_element_by_name("password")		
    password.send_keys(passw)
    password.send_keys(Keys.ENTER)
    driver.get(url_create)
    return


def scanfolders(path):
    folders = []
    for root, dirs, files in os.walk(path, topdown=False):
       # for file in files:
       #    print(os.path.join(root, file))
       for folder in dirs:
          if folder != "@eaDir":
              folders.append(folder)
          # print(os.path.join(root, folder))
          # print(folder)

    return folders

def files_in_folder(path, folder):
    extensions = ("*JPG","*.jpg","*.jpeg",)
    list = []
    for extension in extensions:
        list.extend(glob.glob(os.path.join(path, folder) + "/" + extension))
    return list        
        
def stripe_folder_data(folder):
    try:
        mail = re.search(r'[\w\.-]+@[\w\.-]+', folder)
        mail = mail.group(0)
        mail = mail.replace(".com.", ".com")
        mail = mail.replace(".es.", ".es")
        name_gallery = folder.replace(mail, "")
    except:
        mail = ""
        name_gallery = folder
        
    return mail, name_gallery

def moverFolderFinished(destination):
    ## If already move, delete and move new.
    if os.path.isdir(os.path.join(destination, folder)):
        rmtree(os.path.join(destination, folder), ignore_errors=True)
    move(os.path.join(path, folder), destination)
    
    # ## If already move, delete and move new.
    # if os.path.isdir(os.path.join(processed, folder)):
    #     rmtree(os.path.join(processed, folder), ignore_errors=True)
    # move(os.path.join(path, folder), processed)

    return


def sanitycheck():
    sanity_check_pass = True
    ##Move folders with empty email to error folder
    if mail == "":
        ## If already move, delete and move new.
        # if os.path.isdir(os.path.join(errors, folder)):
        #     rmtree(os.path.join(errors, folder), ignore_errors=True)
        # move(os.path.join(path, folder), errors)
        moverFolderFinished(errors)
        error_notification.append([folder, "NO subido - Falta email"])
        sanity_check_pass = False
        
    elif name_gallery == "":
        ## If already move, delete and move new.
        # if os.path.isdir(os.path.join(errors, folder)):
        #     rmtree(os.path.join(errors, folder), ignore_errors=True)
        # move(os.path.join(path, folder), errors)
        moverFolderFinished(errors)
        error_notification.append([folder, "NO subido - Falta titulo galeria"])
        sanity_check_pass = False

    ##Move empty folders to error folder
    elif len(images) == 0:
        ## If already move, delete and move new.
        # if os.path.isdir(os.path.join(errors, folder)):
        #     rmtree(os.path.join(errors, folder), ignore_errors=True)
        # move(os.path.join(path, folder), errors)
        moverFolderFinished(errors)
        error_notification.append([folder, "NO subido - Carpeta sin imagenes"])
        sanity_check_pass = False

    return sanity_check_pass

##Function
def resize_rotate_watemark():
    error_image_preprocessing = False
    for image_path in tqdm(images):        
        ##Load image
        main = Image.open(image_path)
        mark = Image.open(water_mark)
    
        # mask = mark.convert('L').point(lambda x: min(x, 25))
        # mark.putalpha(mask)
        
        ##Try rotate
        try: ##Read orientation tag
            exif = {ExifTags.TAGS[k]: v for k, v in main._getexif().items() if k in ExifTags.TAGS}
        except: ##If there is no orientation tag available
            exif = {'Orientation': 1}
            error_image_preprocessing = True

        ##Orientation to degree:
        try: ##If conversion orientation-degree exists
            degree = dic_exif[exif['Orientation']]
            main = main.rotate(degree, expand=1)

        except: ## If doesnt exists, dont rotate.
            error_image_preprocessing = True
            
        ##Watemark and scale
        try:    
            mark_width, mark_height = mark.size
            main_width, main_height = main.size
            aspect_ratio = mark_width / mark_height
            new_mark_width = main_width * 0.25
            mark.thumbnail((new_mark_width, new_mark_width / aspect_ratio), Image.ANTIALIAS)
        
            tmp_img = Image.new('RGB', main.size)
        
            for i in range(0, tmp_img.size[0], mark.size[0]):
                for j in range(0, tmp_img.size[1], mark.size[1]):
                    main.paste(mark, (i, j), mark)
                    main.thumbnail((8000, 8000), Image.ANTIALIAS)
                    # main.save(final_image_path, quality=100)
                    
            main.thumbnail((1024, 1024))
            main.save(image_path, quality=100)
            
        except:
            error_image_preprocessing = True
            
    return error_image_preprocessing

        

# def expires():
#     date_after_month = (datetime.today() + relativedelta(months=1)).strftime("%d/%m/20%y")  
#     date_after_month = date_after_month.strftime("%d/%m/20%y")    
#     return date_after_month

def create_gallery():
    driver.get(url_create)
    
    gallerytittle = driver.find_element_by_name("name")	
    gallerytittle.send_keys(folder)
    #gallerytittle.send_keys(name_gallery)
    time.sleep(2)

    ###Select client dropdown
    select = Select(driver.find_element_by_id('id_cliente'))
    select.select_by_value("116949")
    time.sleep(2)

    ###Selected pictures limit
    limitphotos = driver.find_element_by_name("selectablelimit")	
    limitphotos.clear()
    limitphotos.send_keys("999")
    time.sleep(2)

    
    ##Add watemark
    if add_watemark:
        watemark = driver.find_element_by_xpath("//div[@class='form-group has-feedback  col-lg-12'][1]//div[@class='col-lg-6']//div[@id='name']//div[@class='toggle btn btn-default off']//div[@class='toggle-group']//label[@class='btn btn-default active toggle-off']")
        watemark.click()
        time.sleep(1)
        
    ##Add extra images
    if extra_image:
        extra = driver.find_element_by_xpath("//div[@class='form-group has-feedback  col-lg-12'][2]//div[@class='col-lg-6']//div[@id='name']//div[@class='toggle btn btn-default off']//div[@class='toggle-group']//label[@class='btn btn-default active toggle-off']")
        extra.click()
        time.sleep(1)

    ###Block gallery after selection
    if block_after_seleccion:
        limitphotos = driver.find_element_by_xpath("//div[@class='form-group has-feedback  col-lg-12'][3]//div[@class='col-lg-6']//div[@id='name']//div[@class='toggle btn btn-default off']//div[@class='toggle-group']//label[@class='btn btn-default active toggle-off']")
        limitphotos.click()
        time.sleep(1)

    ###Allow comments
    if allow_comments:
        comments = driver.find_element_by_xpath("//div[@class='panel panel-default']//div[@class='panel-body']//div[@class='row']//div[@class='col-lg-9']//div[@class='row'][2]//div[@class='panel panel-default col-lg-5'][1]//div[@class='panel-body']//div[@class='row'][2]//div[@class='form-group has-feedback ']//div[@class='col-lg-3']//div[@id='name']//div[@class='toggle btn btn-default off']")        
        comments.click()
        time.sleep(1)
        
    selected_extension = driver.find_element_by_xpath("//div[@class='panel panel-default']//div[@class='panel-body']//div[@class='row']//div[@class='col-lg-9']//div[@class='row'][2]//div[@class='panel panel-default col-lg-5'][2]//div[@class='panel-body']//div[@class='row'][2]//div[@class='form-group has-feedback ']//div[@class='col-lg-3']//div[@id='name']//div[@class='toggle btn btn-default off']")        
    selected_extension.click()
    time.sleep(1)

    ##expiration date
    expiration_date = driver.find_element_by_name("expired_at")	
    expiration_date.send_keys((datetime.today() + relativedelta(months=1)).strftime("%d/%m/20%y"))
    time.sleep(1)

    ##Save
    save = driver.find_element_by_xpath("//div[@class='panel panel-default padding-left1pct padding-right1pct noborder noshadow']//div[@class='width100 padding-bottom10 padding-top34']//button[@class='btn btn-success width100 margin-bottom10']")
    save.click()
    time.sleep(3)

def upload():
    print("Anadiendo imagenes a la galeria")
    time.sleep(1)

    ##click button add images
    button_add = driver.find_element_by_xpath("//div[@class='wrapper']//div[@class='content-wrapper']//section[@class='content']//div[@class='panel panel-default']//div[@id='imagezone']//div[@class='row']//div[@class='col-xs-12'][2]//div[@class='btn-group']//a[@class='btn btn-info']")
    button_add.click()
    time.sleep(3)
    
    ##Add images
    for image in images:
    # for image in tqdm(images):
        driver.find_element_by_id("AttachImageUploader").send_keys(image)
        time.sleep(1)
    time.sleep(3)

    ##Save images after add it.
    # button_save_images = driver.find_element_by_xpath("//div[@id='uploadimages_4849']//div[@class='modal-dialog modal-dialog']//div[@class='modal-content']//div[@class='modal-footer']//button[@id='uploadimages_4849_footer_button_3CHbFKd81t']")
    button_save_images = driver.find_element_by_xpath("//*[contains(@id, 'uploadimages_')]//*[contains(@class, 'btn btn-success')]")
    button_save_images.click()
    time.sleep(2)

    ## Wait until loader dissapear.
    while True:
        try:
            WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//li[@class='fileuploader-item file-type-image file-ext-jpg upload-loading']")))
        except:
            break
    time.sleep(3)
    
    ##Save
    save = driver.find_element_by_xpath("//div[@class='panel panel-default padding-left1pct padding-right1pct noborder noshadow']//div[@class='width100 padding-bottom10 padding-top34']//button[@class='btn btn-success width100 margin-bottom10']")
    save.click()
    time.sleep(2)

def notify_customer():
    time.sleep(1)

    ##Sent email to customer
    if send_customer_email:
        send_email_button = driver.find_element_by_xpath("//div[@class='panel panel-default backgroundColorGray padding-left1pct padding-right1pct']//div[@class='width100 padding-bottom10'][1]//a[@class='btn btn-warning width100 margin-bottom10']")
        send_email_button.click()
        time.sleep(3)
        
        email_field = driver.find_element_by_name("ClientEmail")	
        email_field.send_keys(mail)
        time.sleep(1)
        
        sent_button = driver.find_element_by_xpath("//button[contains(text(),'Enviar')]")
        sent_button.click()
        
    time.sleep(2)
    return



  
def notifications():
    msg = email.message.Message()
    msg.add_header('Content-Type','text/html')
    
    ##If there is some error
    if len(error_notification) > 0:
        body = [['/!\ Errores --------', '--- MOTIVO ---']] + error_notification + [['OK procesados', '=======']] + sucess_notification
        body = tabulate(body, tablefmt='html')
        msg['Subject'] = '/!\ Error Robot - Galerias AdminPhoto'
        msg.set_payload(body)
        send_email(msg)
        
    #If everything is OK.
    else:
        body = [['|OK| procesados =======', '==========']] + sucess_notification
        body = tabulate(body, tablefmt='html')
        msg['Subject'] = 'OK Robot - Galerias AdminPhoto'
        msg.set_payload(body)
        send_email(msg)
        
    return


def send_email(msg):
    msg['From'] = sender_email
    try:
        with smtplib.SMTP(smtp_server, port) as server:
            context = ssl.create_default_context()
            server.starttls(context=context)
            server.login(sender_email, password)
            msg['To'] = ", ".join(receiver_email)                
            server.sendmail(msg['From'], receiver_email, msg.as_string())
            server.quit()

                
    except Exception as e:
        print("No se puede conectar con el servicio de email.", e)
        
    return
# ============================== LOGIC ==================================
folders = scanfolders(path)
print(folders)

##If there is some work to be done
if len(folders) > 0:
    # ###load webdriver
    driver = webdriver.Chrome(chrome_options=chrome_options)
    # driver = webdriver.Chrome()
    driver.get(url_create)
    
    ##Login
    login(user, passw)
    
    ##New gallery
    pbar = tqdm(folders)
    for folder in pbar:
        pbar.set_description("%s" % folder)
        ##List images
        images = files_in_folder(path, folder)
        ##Extract data from folder
        mail, name_gallery = stripe_folder_data(folder)
        ##Sanity check before start
        sanity_check_pass = sanitycheck()
        
        
        if sanity_check_pass:
            try:
                
                if python_watemark:
                    error_image_preprocessing = resize_rotate_watemark()
                    if error_image_preprocessing:
                        error_notification.append([folder, "Error: marca de agua y rotacion"])
                
                create_gallery()
                upload()
                notify_customer()
                moverFolderFinished(processed)
                sucess_notification.append([folder, "OK - subido"])

                
            except Exception as e:
                # driver.get_screenshot_as_file(str(folder) + ".png")
                error_notification.append([folder, "No publicado: " + str(e)])
            
    
    notifications()
    
    print(error_notification + sucess_notification)
