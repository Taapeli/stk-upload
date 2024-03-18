'''
Created on Aug 16, 2019

@author: kari

Renamed scene.models.media -> models.mediafile / JMä 2021-07-26
'''
import os
from PIL import Image 

import shareds
from bl.base import IsotammiException

media_base_folder = "media"
cypher_get_medium = "MATCH (m:Media{iid:$iid}) RETURN m"


def make_thumbnail(src_file, dst_file, crop=None):
    ''' Create a thumbnail size image from src_file to dst_file.
    '''
    #os.system(f"convert '{src_file}' -resize 200x200  '{dst_file}'")
    size = 128, 128
    try:
        if crop:
            # crop dimensions are diescribed as % of width and height
            im = get_cropped_image(src_file, crop, True)
        else:
            im = Image.open(src_file)
        im.thumbnail(size)
        im.convert('RGB').save(dst_file, "JPEG")
    except FileNotFoundError as _e:
        #print(f'models.mediafile.make_thumbnail: {e.strerror}: {src_file}")
        pass

def get_media_files_folder(batch_id):
    media_folder = os.path.join(media_base_folder,batch_id)
    media_files_folder = os.path.join(media_folder,"files")
    return os.path.abspath(media_files_folder)
    
def get_media_thumbnails_folder(batch_id):
    media_folder = os.path.join(media_base_folder,batch_id)
    media_thumbnails_folder = os.path.join(media_folder,"thumbnails")
    return os.path.abspath(media_thumbnails_folder)

def get_fullname(iid):
    """ Finds image file and return file fullname, image mime type and 
        image size tuple (width, height).
    """
    with shareds.driver.session(default_access_mode='READ') as session:
        rec = session.run(cypher_get_medium, iid=iid).single()
        if rec:
            m = rec['m']
            batch_id = m.get('batch_id','no-batch')
            src = m['src']
            mimetype = m['mime']
            media_files_folder = get_media_files_folder(batch_id)
            try:
                fullname = os.path.join(media_files_folder,src)
                image = Image.open(fullname)
                return fullname, mimetype, image.size
            except FileNotFoundError as e:
                print(f"models.mediafile.get_fullname: {e.strerror}: {src}")
                return src, mimetype, -1
    raise IsotammiException(f"models.mediafile.get_fullname can not read {iid!r}")

def get_thumbname(iid, crop=None):
    ''' Find stored thumbnail file name; create a new file, if needed.
        If there is crop parameter, its value is added to thumb file name.
    '''
    if not iid:
        raise FileNotFoundError('models.mediafile.get_thumbname: no iid')

    rec = shareds.driver.session(default_access_mode='READ').run(cypher_get_medium,
                                                                 iid=iid).single()
    if rec:
        # <Record
        #    m=<Node id=29198 labels=frozenset({'Media'}) 
        #        properties={'batch_id': '2020-08-30.001', 'src': 'Dok/Silius-hauta Tampereella.pdf', 
        #            'mime': 'application/pdf', 'change': 1515865209, 'description': 'Silius-hauta pdf', 
        #            'id': 'O0077', 'iid': 'M-dc1a'}>
        # >
        m = rec['m']
        batch_id = m.get('batch_id','no-batch')
        src = m['src']
        mime = m['mime']
        if mime == 'application/pdf':
            print("#models.mediafile.get_thumbname: Show missing pdf thumbnail")
            return "", "pdf"

        # Example: png --> cropped jpg
        #    src       = "Sibelius/CharlottaBorg&CristianSibelius.png"
        #    base      = "Sibelius/CharlottaBorg&CristianSibelius"
        #    src_file  = "files/Sibelius/CharlottaBorg&CristianSibelius.png"
        #    crop_tail = "#47,21,91,67"
        #    dst_file  = "thumbnails/Sibelius/CharlottaBorg&CristianSibelius#47,21,91,67.jpg"
        base, _ext = src.rsplit('.',1)
        if crop:
            crop_tail = '#'+crop.replace(' ', '').replace('(', '').replace(')', '')
        else:
            crop_tail = ""
        media_thumbnails_folder = get_media_thumbnails_folder(batch_id)
        dst_file = os.path.join(media_thumbnails_folder, base) + crop_tail + '.jpg'
        if not os.path.exists(dst_file):
            media_files_folder = get_media_files_folder(batch_id)
            src_file = os.path.join(media_files_folder, src)
            thumbdir, _x = os.path.split(dst_file)
            os.makedirs(thumbdir, exist_ok=True)
            make_thumbnail(src_file, dst_file, crop)
#             print(f"# Created file {dst_file}")
#         else:
#             print(f"# Existing file {dst_file}")
        # Thumbnail picture found/created
        return dst_file, "jpg"

    # No db Media node
    print(f"#models.mediafile.get_thumbname: No media {iid}")
    return "", None

def get_image_size(path):
    """ Get image size as tuple (width, height) """
    try:
        image = Image.open(path)
        return image.size
    except Exception as _e:
        return None

def get_cropped_image(path, crop, thumbsize=False):
    ''' From given Image file, crop image by given % coordinates.
        If thumbsize=True, scale to 128 x 128 size

        crop "0,15,100,96" -> upper_left=(0%,15%), lower_right(100%,96%)
        
        Also crop "(0,15,100,96)" is accepted
        
        The coordinate system that starts with (0, 0) in the upper left corner.
        The first two values of the box tuple specify the upper left starting 
        position of the crop box. The third and fourth values specify the 
        distance in pixels from this starting position towards the right and 
        bottom direction respectively.
    '''
    if isinstance(crop, list):
        x1,y1, x2,y2 = crop
    elif isinstance(crop, str):
        x1,y1, x2,y2 = crop.replace('(','').replace(')','').split(',')
    image = Image.open(path)
    width, heigth = image.size
    box = [float(x1)*width/100., float(y1)*heigth/100.,
           float(x2)*width/100., float(y2)*heigth/100.]
    #print(f"size=({width},{heigth}), crop={crop} => box={box}")
    image = image.crop(box)
    if thumbsize:
        image.thumbnail((128,128))
    return image
