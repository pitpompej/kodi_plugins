from __future__ import unicode_literals
from urlparse import urlparse
import urllib
import xbmc
import xbmcaddon
import os

class Movies():
    def __init__(self):
        pass

class AmazonWebContent():
    def __init__(self):
        pass

class VideoImage():

    def __init__(self):
        addonID = 'plugin.audio.prime_music'
        addon = xbmcaddon.Addon(id=addonID)
        addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
        self.cacheFolder = os.path.join(addonUserDataFolder, "cache", "covers")
        if not os.path.exists(self.cacheFolder):
            os.makedirs(self.cacheFolder)
        pass

    def ImageFile(self, imgsrc):
        urlinfo = urlparse(imgsrc)
        path = urlinfo[2]
        imgbasename = path[path.rfind("/")+1:]
        imgfile = imgbasename[:imgbasename.find(".")] + ".jpg"
        imgsrc = imgsrc[:imgsrc.rfind("/")+1] + imgfile
        return imgsrc

    
    def ImageDownload(self, asin, imgsrc):
        urllib.urlretrieve(imgsrc, os.path.join(self.cacheFolder, asin + ".jpg")) 


    def HasCachedImage(self, asin):
        imgfile = os.path.join(self.cacheFolder, asin + ".jpg")
        if (os.path.exists(imgfile)):
            return True
        return False


    def GetImage(self, asin, imgsrc):
        if not self.HasCachedImage(asin):
            self.ImageDownload(asin, imgsrc)
        return os.path.join(self.cacheFolder, asin + ".jpg")
    
