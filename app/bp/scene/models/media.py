'''
Created on Aug 16, 2019

@author: kari
'''
import os
from PIL import Image 

#from flask_security import current_user 

import shareds

media_base_folder = "media"

def make_thumbnail(fname, thumbname):
    #os.system(f"convert '{fname}' -resize 200x200  '{thumbname}'")
    try:
        im = Image.open(fname)
        size = 128, 128
        im.thumbnail(size)
        im.convert('RGB').save(thumbname, "JPEG")
    except FileNotFoundError as e:
        print(f'ERROR in bp.scene.models.media.make_thumbnail file "{fname}"\n{e}')

def get_media_files_folder(batch_id):
    media_folder = os.path.join(media_base_folder,batch_id)
    media_files_folder = os.path.join(media_folder,"files")
    return os.path.abspath(media_files_folder)
    
def get_media_thumbnails_folder(batch_id):
    media_folder = os.path.join(media_base_folder,batch_id)
    media_thumbnails_folder = os.path.join(media_folder,"thumbnails")
    return os.path.abspath(media_thumbnails_folder)

def get_fullname(uuid):
    rec = shareds.driver.session().run("match (m:Media{uuid:$uuid}) return m",uuid=uuid).single()
    m = rec['m']
    batch_id = m['batch_id']
    src = m['src']
    mimetype = m['mime']
    media_files_folder = get_media_files_folder(batch_id)
    fullname = os.path.join(media_files_folder,src)
    return fullname,mimetype

def get_thumbname(uuid):
    rec = shareds.driver.session().run("match (m:Media{uuid:$uuid}) return m",uuid=uuid).single()
    if rec:
        m = rec['m']
        batch_id = m['batch_id']
        src = m['src']
        media_thumbnails_folder = get_media_thumbnails_folder(batch_id)
        thumbname = os.path.join(media_thumbnails_folder,src)
        if not os.path.exists(thumbname):
            media_files_folder = get_media_files_folder(batch_id)
            fname = os.path.join(media_files_folder,src)
            thumbdir, _x = os.path.split(thumbname)
            os.makedirs(thumbdir, exist_ok=True)
            make_thumbnail(fname,thumbname)
        return thumbname
    return ""

def get_image_size(path):
    # Get image size as tuple (width, height)
    image = Image.open(path)
    return image.size

def get_cropped_image(path, crop, thumbsize=False):
    ''' From given Image file, crop image by given % coordinates.
        If thumbsize=True, scale to 128 x 128 size

        crop "0,15,100,96" -> upper_left=(0%,15%), lower_right(100%,96%) 
        
        The coordinate system that starts with (0, 0) in the upper left corner.
        The first two values of the box tuple specify the upper left starting 
        position of the crop box. The third and fourth values specify the 
        distance in pixels from this starting position towards the right and 
        bottom direction respectively.
    '''
    x1,y1, x2,y2 = crop.split(',')
    image = Image.open(path)
    width, heigth = image.size
    box = [float(x1)*width/100., float(y1)*heigth/100.,
           float(x2)*width/100., float(y2)*heigth/100.]
    print(f"size=({width},{heigth}), crop={crop} => box={box}")
    image = image.crop(box)
    if thumbsize:
        image.thumbnail((128,128))
    return image
