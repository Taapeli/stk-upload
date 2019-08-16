'''
Created on Aug 16, 2019

@author: kari
'''
import os
from PIL import Image 

from flask_security import current_user 

media_base_folder = "media"

def make_thumbnail(fname, thumbname):
    #os.system(f"convert '{fname}' -resize 200x200  '{thumbname}'")
    im = Image.open(fname)
    size = 128, 128
    im.thumbnail(size)
    im.save(thumbname, "JPEG")

def get_media_files_folder(username):
    media_folder = os.path.join(media_base_folder,username)
    media_files_folder = os.path.join(media_folder,"files")
    return media_files_folder
    
def get_media_thumbnails_folder(username):
    media_folder = os.path.join(media_base_folder,username)
    thumbnails_files_folder = os.path.join(media_folder,"thumbnails")
    return thumbnails_files_folder

def get_fullname(name):
    media_files_folder = get_media_files_folder(current_user.username)
    fname = os.path.join(media_files_folder,name)
    fullname = os.path.abspath(fname)
    return fullname

def get_thumbname(name):
    fname = get_fullname(name)
    media_thumbnails_folder = get_media_thumbnails_folder(current_user.username)
    thumbname = os.path.join(media_thumbnails_folder,name)
    if not os.path.exists(thumbname):
        thumbdir, x = os.path.split(thumbname)
        os.makedirs(thumbdir, exist_ok=True)
        make_thumbnail(fname,thumbname)
    fullname = os.path.abspath(thumbname)
    return fullname

