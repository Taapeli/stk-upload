'''
Created on Aug 16, 2019

@author: kari
'''
import os
from PIL import Image 

from flask_security import current_user 

import shareds

media_base_folder = "media"

def make_thumbnail(fname, thumbname):
    #os.system(f"convert '{fname}' -resize 200x200  '{thumbname}'")
    try:
        im = Image.open(fname)
        size = 128, 128
        im.thumbnail(size)
        im.save(thumbname, "JPEG")
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
    media_files_folder = get_media_files_folder(batch_id)
    fullname = os.path.join(media_files_folder,src)
    return fullname

def get_thumbname(uuid):
    rec = shareds.driver.session().run("match (m:Media{uuid:$uuid}) return m",uuid=uuid).single()
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
