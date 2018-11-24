
from __future__ import unicode_literals
import urllib
import urlparse
import urllib2
import requests
import socket
import mechanize
import cookielib
import sys
import re
import os
import json
import time
import string
import random
import shutil
import subprocess
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
from HTMLParser import HTMLParser
import resources.lib.ScrapeUtils as ScrapeUtils
from BeautifulSoup import BeautifulSoup
import ssl
from pyDes import *
import uuid
from base64 import b64encode, b64decode


addon = xbmcaddon.Addon()
addonID = addon.getAddonInfo('id')
addonFolder = xbmc.translatePath('special://home/addons/'+addonID).decode('utf-8')
addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID).decode('utf-8')

icon = os.path.join(addonFolder, "icon.png")#.encode('utf-8')


def translation(id):
    return addon.getLocalizedString(id) #.encode('utf-8')

if not os.path.exists(os.path.join(addonUserDataFolder, "settings.xml")):
    xbmc.executebuiltin(unicode('XBMC.Notification(Info:,'+translation(30081)+',10000,'+icon+')').encode("utf-8"))
    addon.openSettings()

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
cj = cookielib.MozillaCookieJar()
cacheFolder = os.path.join(addonUserDataFolder, "cache")
#cacheFolderFanartTMDB = os.path.join(cacheFolder, "fanart")
addonFolderResources = os.path.join(addonFolder, "resources")
defaultFanart = os.path.join(addonFolderResources, "fanart.jpg")
siteVersion = addon.getSetting("siteVersion")
siteVersionsList = ["com", "co.uk", "de"]
siteVersion = siteVersionsList[int(siteVersion)]
urlMainS = "https://www.amazon."+siteVersion
urlMain = urlMainS
quality = addon.getSetting("quality")
audioQuality = ["HIGH", "MEDIUM", "LOW"][int(quality)]
forceDVDPlayer = addon.getSetting("forceDVDPlayer") == "true"
defaultview_songs = addon.getSetting("songDefaultView")
defaultview_playlists = addon.getSetting("playlistDefaultView")
defaultview_albums = addon.getSetting("albumDefaultView")

cookieFile = os.path.join(addonUserDataFolder, siteVersion + ".cookies")

NODEBUG = False

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
userAgent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2566.0 Safari/537.36"
opener.addheaders = [('User-agent', userAgent)]


if addon.getSetting('ssl_verif') == 'true' and hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context


def index():
    loginResult = login()
    if loginResult=="success":
        addDir(translation(30002), urlMain+"/s/ref=dmm_pr_bbx_album?ie=UTF8&bbn=5686557031&rh=i%3Adigital-music-album", 'listAlbums', "")
        addDir(translation(30003), urlMain+"/s/ref=s9_rbpl_bw_srch?__mk_de_DE=%C5M%C5Z%D5%D1&rh=i%3Adigital-music-playlist%2Cn%3A5686557031%2Cp_n_format_browse-bin%3A5686558031&sort=featured-rank", 'listAlbums', "")
        addDir(translation(30004), "", 'listGenres', "")
        addDir(translation(30005), urlMain+"/s/ref=s9_aas_bw_srch?__mk_de_DE=%C5M%C5Z%D5%D1&rh=i%3Adigital-music-album%2Cn%3A5686557031%2Cp_n_format_browse-bin%3A180848031%2Cp_n_date_first_available_prime%3A6969880031&bbn=5686557031&sort=featured-rank&rw_html_to_wsrp=1&pf_rd_m=A3JWKAKR8XB7XF&pf_rd_s=merchandised-search-5&pf_rd_r=6RVAXVCW0CXA3QF4F86R&pf_rd_t=101&pf_rd_p=805206707&pf_rd_i=7457104031", 'listAlbums', "")
        addDir(translation(30016), "albums", 'search', "")
        addDir(translation(30017), "songs", 'search', "")
        addDir(translation(30010), "playlists", 'listOwnPlaylists', "")
        addDir(translation(30011), "", 'listOwnAlbums', "")
        addDir(translation(30014), "", 'listOwnArtists', "")
        addDir(translation(30012), "", 'listFollowed', "")
        addDir(translation(30013), "", 'listRecentlyPlayed', "")
        xbmcplugin.endOfDirectory(pluginhandle)
    elif loginResult == "captcha_req":
        xbmc.executebuiltin(unicode('XBMC.Notification(Info:,'+translation(30083)+',10000,'+icon+')').encode("utf-8"))
    elif loginResult == "noprime":
        xbmc.executebuiltin(unicode('XBMC.Notification(Info:,'+translation(30084)+',10000,'+icon+')').encode("utf-8"))
    else:
        xbmc.executebuiltin(unicode('XBMC.Notification(Info:,'+translation(30082)+',10000,'+icon+')').encode("utf-8"))


def listAlbums(url):
    xbmcplugin.setContent(pluginhandle, "albums")
    content = getUnicodePage(url)
    debug(content)
    content = content.replace("\\","")
    if 'id="catCorResults"' in content:
        content = content[:content.find('id="catCorResults"')]
    args = urlparse.parse_qs(url[1:])
    page = args.get('page', None)
    if page is not None:
        if int(page[0]) > 1:
            content = content[content.find('breadcrumb.breadcrumbSearch'):]
    if siteVersion=="de":
        if 'nstimmung mit Produkten, wir haben daher die Kategorie' in content:
            xbmcplugin.endOfDirectory(pluginhandle)
            xbmc.sleep(100)
            return
    spl = content.split('id="result_')
    videoimage = ScrapeUtils.VideoImage()
    addDir(translation(30006), "", 'index', "")
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('asin="(.+?)"', re.DOTALL).findall(entry)
        if match :
            match1 = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
            title = ""
            if match1:
                title = match1[0]
            else:
                continue
            title = cleanInput(title)
            artist = ""
            match1 = re.compile('von </span><span class="a-size-small a-color-secondary"><.+?>(.+?)<', re.DOTALL).findall(entry)
            if match1:
                artist = match1[0]
                artist += ": "
            year = ""
            match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumbUrl = ""
            if match:
                thumbUrl = videoimage.ImageFile(match[0])
            albumUrl = ""
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            if match:
                albumUrl = match[0]
            else:
                continue
            addDir(artist + title, albumUrl, "listSongs", thumbUrl)
    match_nextpage = re.compile('ass="pagnNext".*?href="(.+?)">', re.DOTALL).findall(content)
    if match_nextpage:
        addDir(translation(30001), urlMain + match_nextpage[0].replace("&amp;","&"), "listAlbums", "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if defaultview_albums:
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_albums)
    xbmc.sleep(100)

def listPlaylists(url):
    xbmcplugin.setContent(pluginhandle, "albums")
    raw_content = getUnicodePage(url)
    debug(raw_content)
    raw_content = raw_content.replace("\\","")
    if 'id="catCorResults"' in raw_content:
        raw_content = raw_content[:raw_content.find('id="catCorResults"')]

    args = urlparse.parse_qs(url[1:])
    page = args.get('page', None)
    if page is not None:
        if int(page[0]) > 1:
            raw_content = raw_content[raw_content.find('breadcrumb.breadcrumbSearch'):]

    spl = raw_content.split('div id="mainResults"')
    if len(spl) > 1:
        content = spl[1]
    else:
        content = raw_content
    spl = content.split('><a class="a-link-normal a-text-normal"')
    videoimage = ScrapeUtils.VideoImage()
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('asin="(.+?)"', re.DOTALL).findall(entry)
        if match :
            match1 = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
            title = ""
            if match1:
                title = match1[0]
            else:
                continue
            title = cleanInput(title)
            match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            if match:
                thumbUrl = videoimage.ImageFile(match[0])
            else:
                thumbUrl = ""
            albumUrl = ""
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            if match:
                albumUrl = match[0]
            else:
                continue
            addDir(title, albumUrl, "listSongs", thumbUrl)
    match_nextpage = re.compile('ass="pagnNext".*?href="(.+?)">', re.DOTALL).findall(content)
    if match_nextpage:
        addDir(translation(30001), urlMain + match_nextpage[0].replace("&amp;","&"), "listPlaylists", "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if defaultview_playlists:
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_playlists)
    xbmc.sleep(100)


def listSongs(url):
    xbmcplugin.setContent(pluginhandle, "songs")
    content = getUnicodePage(url)
    debug(content)
    content = content.replace("\\","")
    if 'id="catCorResults"' in content:
        content = content[:content.find('id="catCorResults"')]

    args = urlparse.parse_qs(url[1:])
    page = args.get('page', None)
    if page is not None:
        if int(page[0]) > 1:
            content = content[content.find('breadcrumb.breadcrumbSearch'):]

    spl = content.split('id="dmusic_tracklist_player_row_')
    videoimage = ScrapeUtils.VideoImage()
    album_thumb_match = re.compile('<img alt=".+?" src="(.+?)"', re.DOTALL).findall(content)
    album_thumb_url = ""
    if album_thumb_match:
        album_thumb_url = videoimage.ImageFile(album_thumb_match[0])
    artist_match = re.compile('roductInfoArtistLink".+?">(\S.+?)</', re.DOTALL).findall(content)
    artist = ""
    run_per_song_check = False
    if artist_match:
        artist = artist_match[0]
    else:
        run_per_song_check = True
    album_title = ""
    album_title_match = re.compile('<h1 class="a-size-large a-spacing-micro">(.+?)</h1>', re.DOTALL).findall(content)
    if album_title_match:
        album_title = album_title_match[0]
    album_songs = getSongList(content, run_per_song_check)
    if run_per_song_check == True:
        for song in album_songs:
            addLink(song["title"], "playTrack", song["trackID"], album_thumb_url, "", song["track_nr"], song["artist"], song["album_title"], song["year"], show_artist_and_title = True)
    else:
        for song in album_songs:
            addLink(song["title"], "playTrack", song["trackID"], album_thumb_url, "", song["track_nr"], artist, album_title, song["year"])
    xbmcplugin.endOfDirectory(pluginhandle)
    if defaultview_songs:
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_songs)
    xbmc.sleep(100)


def getSongList(content, with_album_and_artist=False):
    songs = []
    spl = content.split('id="dmusic_tracklist_player_row_')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        if not 'contentSubscriptionMode&quot;:&quot;UNLIMITED&quot;' in entry and not 'contentSubscriptionMode&quot;:&quot;PRIME&quot;' in entry:
            continue
        match = re.compile('data-asin="(.+?)"', re.DOTALL).findall(entry)
        if match :
            trackID = match[0]
            match1 = re.compile('TitleLink a-text-bold" href.+?">(.+?)<', re.DOTALL).findall(entry)
            title = ""
            if match1:
                title = match1[0]
            else:
                continue
            title = cleanInput(title)
            year = ""
            artist=""
            album_title=""
            if with_album_and_artist == True:
                artist_match = re.compile('ArtistLink" href.+?">(.+?)<', re.DOTALL).findall(entry)
                if artist_match:
                    artist = artist_match[0]
                album_title_match = re.compile('a-size-mini" href=.+?">(.+?)<', re.DOTALL).findall(entry)
                if album_title_match:
                    album_title = album_title_match[0]
            album_track_nr = ""
            album_track_nr_match = re.compile('TrackNumber">(.+?)<', re.DOTALL).findall(entry)
            if album_track_nr_match:
                album_track_nr = album_track_nr_match[0]
            song = { 'trackID' : trackID , 'title' : title, 'year' : year, 'track_nr' : album_track_nr , 'artist' : artist, 'album_title' : album_title }
            songs.append(song)
    return songs


def listSearchedSongs(url):
    xbmcplugin.setContent(pluginhandle, "songs")
    content = getUnicodePage(url)
    debug(content)
    content = content.replace("\\","")
    if 'id="catCorResults"' in content:
        content = content[:content.find('id="catCorResults"')]

    args = urlparse.parse_qs(url[1:])
    page = args.get('page', None)
    if page is not None:
        if int(page[0]) > 1:
            content = content[content.find('breadcrumb.breadcrumbSearch'):]

    spl = content.split('class="songTitle s-music-track-title"')
    addDir(translation(30006), "", 'index', "")
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('asin="(.+?)"', re.DOTALL).findall(entry)
        if match :
            trackID = match[0]
            match1 = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
            title = ""
            if match1:
                title = match1[0]
            else:
                continue
            title = cleanInput(title)
            year = ""
            artist = ""
            album_title = ""
            artist_match = re.compile('artist-redirect.+?">(.+?)<', re.DOTALL).findall(entry)
            if artist_match:
                artist = artist_match[0]
            album_title_match = re.compile('album-redirect.+?">(.+?)<', re.DOTALL).findall(entry)
            if album_title_match:
                album_title = album_title_match[0]
            addLink(artist+": "+title, "playTrack", trackID, "", "", "", artist, album_title, year)
    match_nextpage = re.compile('ass="pagnNext".*?href="(.+?)">', re.DOTALL).findall(content)
    if match_nextpage:
        addDir(translation(30001), urlMain + match_nextpage[0].replace("&amp;","&"), "listSearchedSongs", "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if defaultview_songs:
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_songs)
    xbmc.sleep(100)

def setPlayItemInfo(play_item):
    tracknumber = xbmc.getInfoLabel('ListItem.TrackNumber') if xbmc.getInfoLabel('ListItem.TrackNumber') != '' else xbmc.getInfoLabel('Playlist.Position')
    play_item.setInfo('music', {'album': g_album, 'artist': g_artist, 'title': name, 'TrackNumber': tracknumber})
    play_item.setArt({'thumb': thumb})
    return play_item


def playTrack(asin):
    content = trackPostUnicodeGetHLSPage('https://music.amazon.de/dmls/', asin)
    temp_file_path = addonUserDataFolder
    if forceDVDPlayer:
        temp_file_path += "/temp.mp4"
    else:
        temp_file_path += "/temp.m3u8"
    if xbmcvfs.exists(temp_file_path):
        xbmcvfs.delete(temp_file_path)
    m3u_temp_file = xbmcvfs.File(temp_file_path, 'w')
    manifest_match = re.compile('manifest":"(.+?)"',re.DOTALL).findall(content)
    if manifest_match:
        m3u_string = manifest_match[0]
        m3u_string = m3u_string.replace("\\n", os.linesep)
        m3u_temp_file.write(m3u_string.encode("ascii"))
    m3u_temp_file.close()
    play_item = xbmcgui.ListItem(path=temp_file_path)
    play_item = setPlayItemInfo(play_item)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem=play_item)


def listGenres():
    addDir(translation(30020), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180643031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30021), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180530031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30022), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180548031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30023), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180599031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30024), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180607031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30025), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180620031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30026), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180621031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30027), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180627031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30028), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180635031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30029), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180654031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30030), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180542031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30031), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180557031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30032), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180671031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30033), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180679031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30034), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180680031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30035), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180690031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30036), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180723031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30037), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180696031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30038), urlMain+"/s?rh=n%3A5686557031%2Cn%3A213656031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30039), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180708031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    addDir(translation(30040), urlMain+"/s?rh=n%3A5686557031%2Cn%3A180712031%2Cp_n_format_browse-bin%3A180848031&bbn=5686557031&sort=featured-rank&ie=UTF8", 'listAlbums', "")
    xbmcplugin.endOfDirectory(pluginhandle)

def deleteCookies():
    if os.path.exists(cookieFile):
        os.remove(cookieFile)
    addon.setSetting('csrf_tsToken', "")
    addon.setSetting('csrf_rndToken', "")
    addon.setSetting('csrf_Token', "")
    addon.setSetting('req_dev_id', "")
    addon.setSetting('customerID', "")
    addon.setSetting('access', "")


def deleteCache():
    if os.path.exists(cacheFolder):
        try:
            shutil.rmtree(cacheFolder)
        except:
            shutil.rmtree(cacheFolder)

def getUnicodePage(url):
    print url
    req = opener.open(url)
    content = ""
    if "content-type" in req.headers and "charset=" in req.headers['content-type']:
        encoding=req.headers['content-type'].split('charset=')[-1]
        content = unicode(req.read(), encoding)
    else:
        content = unicode(req.read(), "utf-8")
    return content


def showPlaylistContent():
    content = playlistPostUnicodePage('https://music.amazon.de/cirrus/', url)
    debug(content)
    obj = json.loads(content)
    videoimage = ScrapeUtils.VideoImage()
    root = obj['getPlaylistsResponse']['getPlaylistsResult']['playlistInfoList'][0]
    tracks = root['playlistEntryList']
    for track in tracks:
        coid = track['trackAdriveId']
        meta = track['metadata']
        artist = meta['albumArtistName']
        album_title = meta['albumName']
        songTitle = meta['title']
        asin = ''
        if('asin' in meta):
            asin = meta['asin']
        objectId = meta['objectId']
        status = meta['status']
        icon = ''
        albumAsin = meta['albumAsin']
        if('albumCoverImageFull' in meta):
            listIcon = meta['albumCoverImageFull']
            cacheIdentifyer = albumAsin if albumAsin else objectId
            icon = videoimage.GetImage(cacheIdentifyer,listIcon)
        if songTitle and status == "AVAILABLE":
            if (('primeStatus' in meta and meta['primeStatus'] == "PRIME") 
                    or ('purchased' in meta and meta['purchased'] == "true")
                    or ('instantImport' in meta and meta['instantImport'] == "true")):
                addLink(artist+": "+songTitle, "playTrack", asin, icon, "", "", artist, album_title)
            elif ('isMusicSubscription' in meta and meta['isMusicSubscription'] == "true"):
                addLink(artist+": "+songTitle, "playTrack", asin, icon, "", "", artist, album_title, unlimited_color = True)
    next_available=re.compile('"nextResultsToken":"(.+?)"').findall(content)
    if next_available and next_available[0].isdigit():
        playlist_id = url.split('&')
        addDir(translation(30001), playlist_id[0] + "&nextResultsToken=" + next_available[0], "showPlaylistContent", "")
    playlist_title = ""
    playlist_title_matches = re.compile('}],"title":"(.+?)"').findall(content)
    if playlist_title_matches:
        playlist_title = playlist_title_matches[0]
    xbmcgui.Window(10000).setProperty("AmazonMusic-CurrentPlaylist",playlist_title)
    xbmcplugin.endOfDirectory(pluginhandle)
    if defaultview_songs:
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_songs)
    xbmc.sleep(100)

def listOwnPlaylists():
    xbmcplugin.setContent(pluginhandle, "albums")
    content = playlistPostUnicodePage('https://music.amazon.de/cirrus/')
    spl = content.split("adriveId")
    for i in range(1, len(spl), 1):
        entry = spl[i]

        listId=re.compile(':"(.+?)"').findall(entry)
        listTitle=re.compile('"title":"(.+?)"').findall(entry)
        if listTitle:
            addDir(listTitle[0], listId[0]+"&nextResultsToken=" ,"showPlaylistContent", "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if defaultview_songs:
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_playlists)
    xbmc.sleep(100)

def listOwnAlbums():
    xbmcplugin.setContent(pluginhandle, "albums")
    content = albumPostUnicodePage('https://music.amazon.de/cirrus/', url)
    spl = content.split("albumArtLocator")
    videoimage = ScrapeUtils.VideoImage()
    for i in range(1, len(spl), 1):
        entry = spl[i]
        listId=re.compile(':"(.+?)"').findall(entry)
        listArtist=re.compile('"albumArtistName":"(.+?)"').findall(entry)
        listTitle=re.compile('"albumName":"(.+?)"').findall(entry)
        sortArtist=re.compile('"sortAlbumArtistName":"(.+?)"').findall(entry)
        sortTitle=re.compile('"sortAlbumName":"(.+?)"').findall(entry)
        listIcon=re.compile('"albumCoverImageFull":"(.+?)"').findall(entry)
        albumAsin=re.compile('"albumAsin":"(.+?)"').findall(entry)
        if albumAsin[0]:
            cacheIdentifyer = albumAsin[0]
        else:
            objectId = re.compile('"objectId":"(.+?)"').findall(entry)
            cacheIdentifyer = objectId[0]
        try:
            thumbUrl = videoimage.GetImage(cacheIdentifyer,listIcon[0])
        except:
            thumbUrl = ''
        if listTitle:
            addDir(listArtist[0] + " - " + listTitle[0], listId[0] + "&nextResultsToken=" ,"showAlbumContent", thumbUrl, sortArtist[0], sortTitle[0] )
    next_available=re.compile('"nextResultsToken":"(.+?)"').findall(content)
    if next_available and next_available[0].isdigit():
        addDir(translation(30001), "&nextResultsToken=" + next_available[0], "listOwnAlbums", "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if defaultview_songs:
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_albums)
    xbmc.sleep(100)


def listOwnArtists():
    xbmcplugin.setContent(pluginhandle, "artists")
    content = albumPostUnicodePage('https://music.amazon.de/cirrus/', url, True)
    spl = content.split("albumArtLocator")
    videoimage = ScrapeUtils.VideoImage()
    for i in range(1, len(spl), 1):
        entry = spl[i]
        listId=re.compile(':"(.+?)"').findall(entry)
        listArtist=re.compile('"artistName":"(.+?)"').findall(entry)
        sortArtist=re.compile('"sortAlbumArtistName":"(.+?)"').findall(entry)
        sortTitle=re.compile('"sortAlbumName":"(.+?)"').findall(entry)
        listIcon=re.compile('"albumCoverImageFull":"(.+?)"').findall(entry)
        albumAsin=re.compile('"albumAsin":"(.+?)"').findall(entry)
        if albumAsin[0]:
            cacheIdentifyer = albumAsin[0]
        else:
            objectId = re.compile('"objectId":"(.+?)"').findall(entry)
            cacheIdentifyer = objectId[0]
        try:
            thumbUrl = videoimage.GetImage(cacheIdentifyer,listIcon[0])
        except:
            thumbUrl = ''
        if listArtist:
            addDir(listArtist[0], listId[0] + "&nextResultsToken=" ,"showArtistContent", thumbUrl, sortArtist[0] )
    next_available=re.compile('"nextResultsToken":"(.+?)"').findall(content)
    if next_available and next_available[0].isdigit():
        addDir(translation(30001), "&nextResultsToken=" + next_available[0], "listOwnArtists", "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if defaultview_songs:
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_songs)
    xbmc.sleep(100)


def showListFollowed():
    xbmcplugin.setContent(pluginhandle, "albums")
    head = { 'User-Agent' : userAgent,
             'X-Requested-With' : 'XMLHttpRequest',
             'X-Amz-Target' : 'com.amazon.musicplaylist.model.MusicPlaylistService.getFollowedPlaylistsInLibrary',
             'Accept-Encoding' : 'gzip,deflate,br',
             'Accept-Language' : 'de,en-US;q=0.7,en;q=0.3',
             'Content-Encoding' : 'amz-1.0',
             'Referer' : 'https://music.amazon.de/home',
             'Accept' : '*/*',
             'content-type' : 'application/json',
             'csrf-token' : addon.getSetting('csrf_Token'),
             'csrf-rnd' : addon.getSetting('csrf_rndToken'),
             'csrf-ts' : addon.getSetting('csrf_tsToken') }

    url = 'https://music.amazon.de/EU/api/playlists/'

    data ='{'
    data = data + '\"pageSize\":20,'
    data = data + '\"entryOffset\":0,'
    data = data + '\"optIntoSharedPlaylists\":true,'
    data = data + '\"deviceId\":\"' + addon.getSetting('req_dev_id') + '\",'
    data = data + '\"deviceType\":\"A16ZV8BU3SN1N3\",'
    data = data + '\"musicTerritory\":\"DE\",'
    data = data + '\"customerId\":\"' + addon.getSetting('customerID') + '\"'
    data = data + '}'

    resp = requests.post(url, data, headers=head, cookies=cj)

    obj = json.loads(resp.text)
    items = obj['playlists']

    for item in items:
        asin = item['asin']
        title = item['title']
        desc = item['description']
        icon = item['fourSquareImage']['url']
        addDir(title, '', "lookupList&asin=" + asin, icon)

    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.sleep(100)

def showLookupList(asin):
    xbmcplugin.setContent(pluginhandle, "songs")
    head = { 'User-Agent' : userAgent,
             'X-Requested-With' : 'XMLHttpRequest',
             'X-Amz-Target' : 'com.amazon.musicensembleservice.MusicEnsembleService.lookup',
             'Accept-Encoding' : 'gzip,deflate,br',
             'Accept-Language' : 'de,en-US;q=0.7,en;q=0.3',
             'Content-Encoding' : 'amz-1.0',
             'Referer' : 'https://music.amazon.de/playlists/' + asin,
             'Accept' : '*/*',
             'content-type' : 'application/json',
             'csrf-token' : addon.getSetting('csrf_Token'),
             'csrf-rnd' : addon.getSetting('csrf_rndToken'),
             'csrf-ts' : addon.getSetting('csrf_tsToken') }

    url = 'https://music.amazon.de/EU/api/muse/legacy/lookup'

    data ='{'
    data = data + '\"asins\":[\"' + asin + '\"],'
    data = data + '\"features\":'
    data = data + '[\"collectionLibraryAvailability\",'
    data = data + '\"expandTracklist\",'
    data = data + '\"playlistLibraryAvailability\",'
    data = data + '\"trackLibraryAvailability\",'
    data = data + '\"hasLyrics\"],'
    data = data + '\"requestedContent\":\"MUSIC_SUBSCRIPTION\",'
    data = data + '\"deviceId\":\"' + addon.getSetting('req_dev_id') + '\",'
    data = data + '\"deviceType\":\"A16ZV8BU3SN1N3\",'
    data = data + '\"musicTerritory\":\"DE\",'
    data = data + '\"customerId\":\"' + addon.getSetting('customerID') + '\"'
    data = data + '}'

    resp = requests.post(url, data, headers=head, cookies=cj)

    obj = json.loads(resp.text)
    items = obj['playlistList'][0]['tracks']

    for item in items:
            asin = item['asin']

            album =  item['album']['title']
            artist = item['artist']['name']

            title = item['title']
            dura = item['duration']
            icon = item['album']['image']

            addLink(artist + ": " + title, "playTrack", asin, icon, "", "", artist, album)

    xbmcplugin.endOfDirectory(pluginhandle)
    if defaultview_songs:
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_songs)
    xbmc.sleep(100)

def showListRecentlyPlayed():
    xbmcplugin.setContent(pluginhandle, "songs")
    head = { 'User-Agent' : userAgent,
             'X-Requested-With' : 'XMLHttpRequest',
             'X-Amz-Target' : 'com.amazon.nimblymusicservice.NimblyMusicService.GetRecentTrackActivity',
             'Accept-Encoding' : 'gzip,deflate,br',
             'Accept-Language' : 'de,en-US;q=0.7,en;q=0.3',
             'Content-Encoding' : 'amz-1.0',
             'Referer' : 'https://music.amazon.de/recently/played',
             'Accept' : '*/*',
             'content-type' : 'application/json',
             'csrf-token' : addon.getSetting('csrf_Token'),
             'csrf-rnd' : addon.getSetting('csrf_rndToken'),
             'csrf-ts' : addon.getSetting('csrf_tsToken') }

    url = 'https://music.amazon.de/EU/api/nimbly/'

    data ='{'
    data = data + '\"activityTypeFilters\":[\"PLAYED\"],'
    data = data + '\"lang\":\"de\",'
    data = data + '\"deviceId\":\"' + addon.getSetting('req_dev_id') + '\",'
    data = data + '\"deviceType\":\"A16ZV8BU3SN1N3\",'
    data = data + '\"musicTerritory\":\"DE\",'
    data = data + '\"customerId\":\"' + addon.getSetting('customerID') + '\"'
    data = data + '}'

    resp = requests.post(url, data, headers=head, cookies=cj)
    debug(resp.text)
    obj = json.loads(resp.text)
    items = obj['recentActivityMap']['PLAYED']['recentTrackList']

    for item in items:

        asin = ''
        if('asin' in item):
            asin = item['asin']
        coid = ''
        if('objectId' in item):
            coid = item['objectId']

        title = item['displayName']

        icon = ''
        if('imageFull' in item):
            icon = item['imageFull']

        status = True if ((item['isInstantImport'] == 'true') or (item['isMusicSubscription'] == 'true') or (item['isPrime'] == 'true') or (item['isPurchased'] == 'true')) else False
        artistName = item['artistName']
        albumName = item['albumName']

        if status:
            addLink(artistName + ": " + title, "playTrack", asin, icon, "", "", artistName, albumName, unlimited_color = (item['isPrime'] == 'false' and item['isMusicSubscription'] == 'true'))

    xbmcplugin.endOfDirectory(pluginhandle)
    if defaultview_songs:
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_songs)
    xbmc.sleep(100)

def albumPostUnicodePage(url, nextSite = "", searchArtist = False):
    br = prepareMechanizeBrowser()
    if searchArtist:
        search_ret_type = 'ARTISTS'
        album_sort_column = 'sortArtistName'
    else:
        search_ret_type = 'ALBUMS'
        album_sort_column = 'sortAlbumArtistName'
    resp = ''
    content = ''
    postDict = {
        'searchReturnType' : search_ret_type,
        'searchCriteria.member.1.attributeName' : 'status',
        'searchCriteria.member.1.comparisonType' : 'EQUALS',
        'searchCriteria.member.1.attributeValue' : 'AVAILABLE',
        'searchCriteria.member.2.attributeName' : 'trackStatus',
        'searchCriteria.member.2.comparisonType' : 'IS_NULL',
        'albumArtUrlsSizeList.member.1' : 'FULL',
        'selectedColumns.member.1' : 'albumArtistName',
        'selectedColumns.member.2' : 'albumName',
        'selectedColumns.member.3' : 'artistName',
        'selectedColumns.member.4' : 'objectId',
        'selectedColumns.member.5' : 'primaryGenre',
        'selectedColumns.member.6' : 'sortAlbumArtistName',
        'selectedColumns.member.7' : 'sortAlbumName',
        'selectedColumns.member.8' : 'sortArtistName',
        'selectedColumns.member.9' : 'albumCoverImageFull',
        'selectedColumns.member.10' : 'albumAsin',
        'selectedColumns.member.11' : 'artistAsin',
        'selectedColumns.member.12' : 'gracenoteId',
        'selectedColumns.member.13' : 'physicalOrderId',
        'maxResults' : '50',
        'Operation' : 'searchLibrary',
        'caller' : 'getAllDataByMetaType',
        'sortCriteriaList.member.1.sortColumn' : album_sort_column,
        'sortCriteriaList.member.1.sortType' : 'ASC',
        'ContentType' : 'JSON',
        'customerInfo.customerId' : addon.getSetting('customerID'),
        'customerInfo.deviceId' :  addon.getSetting('req_dev_id'),
        'customerInfo.deviceType' : 'A16ZV8BU3SN1N3'
        }
    if not searchArtist:
        postDict['sortCriteriaList.member.2.sortColumn'] = 'sortAlbumName'
        postDict['sortCriteriaList.member.2.sortType'] = 'ASC'
    params = urllib.urlencode(postDict)
    if nextSite:
        params += nextSite
    try:
        resp = br.open(url, params)
        content = unicode(resp.read(), "utf-8")
    except urllib2.HTTPError as e :
        log(e.read())
    return content


def showAlbumContent(ArtistName, AlbumName):
    artist = ArtistName
    title = AlbumName
    content = albumTracksPostUnicodePage('https://music.amazon.de/cirrus/', artist, title) 
    videoimage = ScrapeUtils.VideoImage()
    listIcon=re.compile('"albumCoverImageFull":"(.+?)"').search(content).group(1)
    albumAsin=re.compile('"albumAsin":"(.+?)"').search(content).group(1)
    if albumAsin:
        cacheIdentifyer = albumAsin
    else:
        cacheIdentifyer = re.compile('"objectId":"(.+?)"').search(content).group(1)
    try:
        thumbUrl = videoimage.GetImage(cacheIdentifyer,listIcon)
    except:
        thumbUrl = ''

    obj = json.loads(content)
    root = obj['selectTrackMetadataResponse']['selectTrackMetadataResult']
    tracks = root['trackInfoList']
    for track in tracks:
        coid = track['adriveId']
        meta = track['metadata']

        artistName = meta['albumArtistName']
        albumName = meta['albumName']
        title = meta['title']
        status = meta['status']
        asin =''
        if('asin' in meta):
            asin = meta['asin']
        if status == "AVAILABLE":
            if('primeStatus' in meta):
                addLink(title, "playTrack", asin, thumbUrl, "", "", artistName, albumName)

    xbmcplugin.endOfDirectory(pluginhandle)
    if defaultview_songs:
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_songs)
    xbmc.sleep(100)


def albumTracksPostUnicodePage(url, artist, title):
    br = prepareMechanizeBrowser()
    resp = ''
    content = ''
    postDict = {
        'selectCriteriaList.member.1.attributeName' : 'status',
        'selectCriteriaList.member.1.comparisonType' : 'EQUALS',
        'selectCriteriaList.member.1.attributeValue' : 'AVAILABLE',
        'selectCriteriaList.member.2.attributeName' : 'trackStatus',
        'selectCriteriaList.member.2.comparisonType' : 'IS_NULL',
        'selectCriteriaList.member.3.attributeName' : 'sortAlbumArtistName',
        'selectCriteriaList.member.3.comparisonType' : 'EQUALS',
        'selectCriteriaList.member.3.attributeValue' : artist,
        'selectCriteriaList.member.4.attributeName' : 'sortAlbumName',
        'selectCriteriaList.member.4.comparisonType' : 'EQUALS',
        'selectCriteriaList.member.4.attributeValue' : title,
        'albumArtUrlsSizeList.member.1' : 'FULL',
        'albumArtUrlsSizeList.member.2' : 'LARGE',
        'albumArtUrlsRedirects' : 'false',
        'maxResults' : '100',
        'Operation' : 'selectTrackMetadata',
        'distinctOnly' : 'false',
        'countOnly' : 'false',
        'caller' : 'getServerData',
        'selectedColumns.member.1' : '*',
        'sortCriteriaList.member.1.sortColumn' : 'trackNum',
        'sortCriteriaList.member.1.sortType' : 'ASC',
        'ContentType' : 'JSON',
        'customerInfo.customerId' : addon.getSetting('customerID'),
        'customerInfo.deviceId' :  addon.getSetting('req_dev_id'),
        'customerInfo.deviceType' : 'A16ZV8BU3SN1N3'
        }
    params = urllib.urlencode(postDict)  

    try:
        resp = br.open(url, params)
        content = unicode(resp.read(), "utf-8")
    except urllib2.HTTPError as e :
        log(e.read())
    return content


def showArtistContent(ArtistName ):
    artist = ArtistName
    content = artistTracksPostUnicodePage('https://music.amazon.de/cirrus/', artist )
    videoimage = ScrapeUtils.VideoImage()

    obj = json.loads(content)
    root = obj['selectTrackMetadataResponse']['selectTrackMetadataResult']
    tracks = root['trackInfoList']
    for track in tracks:
        coid = track['adriveId']
        meta = track['metadata']

        listIcon = meta['albumCoverImageFull']
        albumAsin = meta['albumAsin']
        if albumAsin:
            cacheIdentifyer = albumAsin
        else:
            cacheIdentifyer = meta['objectId']
        try:
            thumbUrl = videoimage.GetImage(cacheIdentifyer,listIcon)
        except:
            thumbUrl = ''

        artistName = meta['albumArtistName']
        albumName = meta['albumName']
        title = meta['title']
        status = meta['status']
        asin =''
        if('asin' in meta):
            asin = meta['asin']
        if status == "AVAILABLE":
            if('primeStatus' in meta):
                addLink(albumName + ' - ' + title, "playTrack", asin, thumbUrl, "", "", artistName, albumName)

    xbmcplugin.endOfDirectory(pluginhandle)
    if defaultview_songs:
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_songs)
    xbmc.sleep(100)



def artistTracksPostUnicodePage(url, artist):
    br = prepareMechanizeBrowser()
    resp = ''
    content = ''
    postDict = {
        'selectCriteriaList.member.1.attributeName' : 'sortArtistName',
        'selectCriteriaList.member.1.comparisonType' : 'EQUALS',
        'selectCriteriaList.member.1.attributeValue' : artist,
        'selectCriteriaList.member.2.attributeName' : 'status',
        'selectCriteriaList.member.2.comparisonType' : 'EQUALS',
        'selectCriteriaList.member.2.attributeValue' : 'AVAILABLE',
        'selectCriteriaList.member.3.attributeName' : 'trackStatus',
        'selectCriteriaList.member.3.comparisonType' : 'IS_NULL',
        'albumArtUrlsSizeList.member.1' : 'FULL',
        'albumArtUrlsSizeList.member.2' : 'LARGE',
        'albumArtUrlsRedirects' : 'false',
        'maxResults' : '100',
        'Operation' : 'selectTrackMetadata',
        'distinctOnly' : 'false',
        'countOnly' : 'false',
        'caller' : 'getServerData',
        'selectedColumns.member.1' : '*',
        'sortCriteriaList.member.1.sortColumn' : 'sortAlbumName',
        'sortCriteriaList.member.1.sortType' : 'ASC',
        'sortCriteriaList.member.2.sortColumn' : 'discNum',
        'sortCriteriaList.member.2.sortType' : 'ASC',
        'sortCriteriaList.member.3.sortColumn' : 'trackNum',
        'sortCriteriaList.member.3.sortType' : 'ASC',
        'ContentType' : 'JSON',
        'customerInfo.customerId' : addon.getSetting('customerID'),
        'customerInfo.deviceId' :  addon.getSetting('req_dev_id'),
        'customerInfo.deviceType' : 'A16ZV8BU3SN1N3'
        }
    params = urllib.urlencode(postDict)

    try:
        resp = br.open(url, params)
        content = unicode(resp.read(), "utf-8")
    except urllib2.HTTPError as e :
        log(e.read())
    return content



def playlistPostUnicodePage(url, playlistId = ""):
    br = prepareMechanizeBrowser()
    resp = ''
    content = ''
    postDict = {
        'maxResults' : '100',
        'Operation' : 'getPlaylists',
        'caller' : 'getServerListSongs',
        'albumArtUrlsRedirects' : 'false',
        'albumArtUrlsSizeList.member.1' : 'FULL',
        'trackColumns.member.1' : 'albumAsin',
        'trackColumns.member.2' : 'artistAsin',
        'trackColumns.member.3' : 'albumArtistName',
        'trackColumns.member.4' : 'albumName',
        'trackColumns.member.5' : 'artistName',
        'trackColumns.member.6' : 'assetType',
        'trackColumns.member.7' : 'duration',
        'trackColumns.member.8' : 'objectId',
        'trackColumns.member.9' : 'sortAlbumArtistName',
        'trackColumns.member.10' : 'sortAlbumName',
        'trackColumns.member.11' : 'sortArtistName',
        'trackColumns.member.12' : 'title',
        'trackColumns.member.13' : 'asin',
        'trackColumns.member.14' : 'primeStatus',
        'trackColumns.member.15' : 'status',
        'trackColumns.member.16' : 'extension',
        'trackColumns.member.17' : 'purchased',
        'trackColumns.member.18' : 'uploaded',
        'trackColumns.member.19' : 'instantImport',
        'trackColumns.member.20' : 'albumCoverImageFull',
        'trackColumns.member.21' : 'isMusicSubscription',
        'ContentType' : 'JSON',
        'customerInfo.customerId' : addon.getSetting('customerID'),
        'customerInfo.deviceId' :  addon.getSetting('req_dev_id'),
        'customerInfo.deviceType' : 'A16ZV8BU3SN1N3'
        }
    if playlistId:
        postDict['includeTrackMetadata'] = 'true'
        postDict['trackCountOnly'] = 'false'
    else:
        postDict['includeTrackMetadata'] = 'false'
        postDict['trackCountOnly'] = 'true'
        postDict['playlistIdList'] = '' 
        postDict['nextResultsToken'] = ''
    data = urllib.urlencode(postDict)
    if playlistId:
        data += "&playlistIdList.member.1=" + playlistId
    debug(data)
    try:
        resp = br.open(url, data)
        content = unicode(resp.read(), "utf-8")
    except urllib2.HTTPError as e :
        log(e.read())

    return content

def trackPostUnicodeGetHLSPage(url, asin, isRetry = False):
    print url
    post_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    headers = { 'User-agent': userAgent,
                'Content-Encoding': 'amz-1.0',
                'Content-Type': 'application/json',
                'X-Amz-Target': 'com.amazon.digitalmusiclocator.DigitalMusicLocatorServiceExternal.getHLSManifest',
                'csrf-token': addon.getSetting('csrf_Token'),
                'csrf-rnd': addon.getSetting('csrf_rndToken'),
                'csrf-ts': addon.getSetting('csrf_tsToken')
                }
    data = '{"customerId":"' + addon.getSetting('customerID') + '","deviceToken":{"deviceTypeId":"A16ZV8BU3SN1N3","deviceId":"' + addon.getSetting('req_dev_id') + '"},"appMetadata":{"https":"true"},"clientMetadata":{"clientId":"WebCP"},"contentId":{"identifier":"' + asin + '","identifierType":"ASIN"},"bitRateList":["' + audioQuality + '"],"hlsVersion":"V3"}'
    coded_req = urllib2.Request(url, data, headers)
    content = ""
    try:
        req = post_opener.open(coded_req)
        if "content-type" in req.headers and "charset=" in req.headers['content-type']:
            encoding=req.headers['content-type'].split('charset=')[-1]
            content = unicode(req.read(), encoding)
        else:
            content = unicode(req.read(), "utf-8")
    except urllib2.HTTPError as e:
        log(unicode(e.read(), "utf-8"))
        doLogin()
        if not isRetry:
            return trackPostUnicodeGetHLSPage(url, asin, True)

    return content

def trackPostUnicodeGetRestrictedPage(url, trackId, isRetry = False):
    post_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    headers = { 'User-agent': userAgent,
                'Content-Encoding': 'amz-1.0',
                'Content-Type': 'application/json',
                'X-Amz-Target': 'com.amazon.digitalmusiclocator.DigitalMusicLocatorServiceExternal.getRestrictedStreamingURL',
                'csrf-token': addon.getSetting('csrf_Token'),
                'csrf-rnd': addon.getSetting('csrf_rndToken'),
                'csrf-ts': addon.getSetting('csrf_tsToken')
                }
    data = '{"customerId":"' + addon.getSetting('customerID') + '","deviceToken":{"deviceTypeId":"A16ZV8BU3SN1N3","deviceId":"' + addon.getSetting('req_dev_id') + '"},"appMetadata":{"https":"true"},"clientMetadata":{"clientId":"WebCP"},"contentId":{"identifier":"' + trackId + '","identifierType":"COID"},"bitRateList":"' + audioQuality + '"}'
    coded_req = urllib2.Request(url, data, headers)
    content = ""
    try:
        req = post_opener.open(coded_req)
        if "content-type" in req.headers and "charset=" in req.headers['content-type']:
            encoding=req.headers['content-type'].split('charset=')[-1]
            content = unicode(req.read(), encoding)
        else:
            content = unicode(req.read(), "utf-8")
    except urllib2.HTTPError as e:
        log("Error on requestin restricted track: " + unicode(e.read(), "utf-8"))
    return content



def getAsciiPage(url):
    req = opener.open(url)
    content = req.read()
    if "content-type" in req.headers and "charset=" in req.headers['content-type']:
        encoding=req.headers['content-type'].split('charset=')[-1]
        content = unicode(content, encoding)
    else:
        content = unicode(content, "utf-8")
    return content.encode("utf-8")

def search(type):
    keyboard = xbmc.Keyboard('', translation(30015))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = unicode(keyboard.getText(), "utf-8").replace(" ", "+")
        search_string = urllib.quote_plus(search_string.encode("utf8"))
        if siteVersion=="de":
            if type=="albums":
                listAlbums(urlMain+"/s?rh=n%3A5686557031%2Ck%2Cp_n_format_browse-bin%3A180848031&keywords="+search_string+"&ie=UTF8")
            elif type=="songs":
                listSearchedSongs(urlMain+"/s/ref=sr_nr_p_n_format_browse-bi_2?fst=as%3Aoff&rh=n%3A5686557031%2Ck%2Cp_n_format_browse-bin%3A180849031&bbn=5686557031&keywords="+search_string+"&ie=UTF8")
#        elif siteVersion=="com":
#            if type=="movies":
#                listMovies(urlMain+"/mn/search/ajax/?_encoding=UTF8&url=node%3D7613704011&field-keywords="+search_string)
#            elif type=="tv":
#                listShows(urlMain+"/mn/search/ajax/?_encoding=UTF8&url=node%3D2858778011&field-keywords="+search_string)
#        elif siteVersion=="co.uk":
#            if type=="movies":
#                listMovies(urlMain+"/mn/search/ajax/?_encoding=UTF8&url=node%3D3356010031&field-keywords="+search_string)
#            elif type=="tv":
#                listShows(urlMain+"/mn/search/ajax/?_encoding=UTF8&url=node%3D3356011031&field-keywords="+search_string)


def getmac():
    mac = uuid.getnode()
    if (mac >> 40) % 2:
        mac = node()
    return uuid.uuid5(uuid.NAMESPACE_DNS, str(mac)).bytes


def encode(data):
    k = triple_des(getmac(), CBC, b'\0\0\0\0\0\0\0\0', padmode=PAD_PKCS5)
    d = k.encrypt(data)
    return b64encode(d)


def decode(data):
    if not data:
        return ''
    k = triple_des(getmac(), CBC, b'\0\0\0\0\0\0\0\0', padmode=PAD_PKCS5)
    d = k.decrypt(b64decode(data))
    return d


def writeConfig(cfile, value):
    cfgfile = os.path.join(addonUserDataFolder, cfile)
    if not xbmcvfs.exists(addonUserDataFolder):
        xbmcvfs.mkdirs(addonUserDataFolder)
    f = xbmcvfs.File(cfgfile, 'w')
    f.write(value.__str__())
    f.close()
    return True


def getConfig(cfile, value=''):
    cfgfile = os.path.join(addonUserDataFolder, cfile)
    if xbmcvfs.exists(cfgfile):
        f = xbmcvfs.File(cfgfile, 'r')
        value = f.read()
        f.close()
    return value


def requestPassword():
    password = ''
    keyboard = xbmc.Keyboard('', translation(30091), True)
    keyboard.setHiddenInput(True)
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        password = keyboard.getText()
    return password

def storePassword():
    password = requestPassword()
    if password:
        writeConfig('foo_bar', encode(password))

def deletePassword():
    writeConfig('foo_bar', '')


def login():
    status = checkLoginStatus()
    if status == "none":
        return doLogin()
    else:
        return status


def doLogin():
    deleteCookies()
    email = addon.getSetting('email')
    pw = decode(getConfig('foo_bar'))
    if pw:
        password = unicode(pw, "utf-8")
    else:
        password = pw
    if not email:
        keyboard = xbmc.Keyboard('', translation(30090))
        keyboard.doModal()
        if keyboard.isConfirmed() and unicode(keyboard.getText(), "utf-8"):
            email = unicode(keyboard.getText(), "utf-8")
    if not password:
        password = unicode(requestPassword(), "utf-8")
    br = mechanize.Browser()
    br.set_cookiejar(cj)
    br.set_handle_gzip(True)
    br.set_handle_robots(False)
    br.addheaders = [('User-Agent', userAgent)]
    content = br.open(urlMainS+"/gp/aw/si.html")
    br.select_form(name="signIn")
    br["email"] = email
    br["password"] = password
    br.addheaders = [('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
             ('Accept-Encoding', 'gzip, deflate'),
             ('Accept-Language', 'de,en-US;q=0.7,en;q=0.3'),
             ('Cache-Control', 'no-cache'),
             ('Connection', 'keep-alive'),
             ('Content-Type', 'application/x-www-form-urlencoded'),
             ('User-Agent', userAgent),
             ('Upgrade-Insecure-Requests', '1')]
    br.submit()
    resp = br.response().read()
    content = unicode(resp, "utf-8")
    while 'action="verify"' in content :
        soup = parseHTML(content)
        if 'name="claimspicker"' in content:
            # step 1
            log('MFA form step 1')
            form = soup.find('form', attrs={'name': 'claimspicker'})
            msgheading = form.find('h1').renderContents().strip()
            msgtxt = form.find('div', attrs={'class': 'a-row'}).renderContents().strip()
            if xbmcgui.Dialog().yesno(msgheading, msgtxt):
                br.select_form(nr=0)
            else:
                return "none"
        elif 'name="code"' in content:
            # step 2
            log('MFA form step 2')
            form = soup.find('form', attrs={'class': 'cvf-widget-form fwcim-form a-spacing-none'})
            msgtxt = form.find('div', attrs={'class': 'a-row a-spacing-none'}).getText().strip()
            kb = xbmc.Keyboard('', msgtxt)
            kb.doModal()
            if kb.isConfirmed() and kb.getText():
                br.select_form(nr=0)
                br['code'] = kb.getText()
            else:
                return "none"
        else:
            # Unknown form
            return "none"
        xbmc.executebuiltin('ActivateWindow(busydialog)')
        br.submit()
        resp = br.response().read()
        content = unicode(resp, "utf-8")
        xbmc.executebuiltin('Dialog.Close(busydialog)')
    content = content.replace("\\","")
    captcha_match = re.compile('ap_captcha_title', re.DOTALL).findall(content)
    if captcha_match:
        log("Captcha required!")
        return "captcha_req"
    return checkLoginStatus(True)


def checkLoginStatus(updateSettings = False):
    signed_out_expression = '"customerId":0'
    is_unlimited_expression = '"hawkfireAccess":1'
    is_prime_expression = '"primeAccess":1'
    access = "none"
    music_content = getUnicodePage("https://music.amazon.de")
    music_content = music_content.replace("\\","")
    if signed_out_expression in music_content:
        return "none"
    elif is_unlimited_expression in music_content:
        access = "unlimited"
    elif is_prime_expression in music_content:
        access = "prime"
    else:
        return "noprime"

    if updateSettings:
        addon.setSetting('access', access)
        log('access: ' + access)
        match = re.compile('"csrf_ts":"(.+?)"', re.DOTALL).findall(music_content)
        if match:
            addon.setSetting('csrf_tsToken', match[0])
            log(match[0])
        match = re.compile('"csrf_rnd":"(.+?)"', re.DOTALL).findall(music_content)
        if match:
            addon.setSetting('csrf_rndToken', match[0])
            log(match[0])
        match = re.compile('"csrf_token":"(.+?)"', re.DOTALL).findall(music_content)
        if match:
            addon.setSetting('csrf_Token', match[0])
            log(match[0])
        cj.save(cookieFile, ignore_discard=True, ignore_expires=True)
        for cookie in cj:
            if cookie.name == "ubid-acbde":
                dev_id = cookie.value.replace("-", "")
                addon.setSetting('req_dev_id', dev_id)
        customer_match = re.compile('"customerId":"(.+?)"', re.DOTALL).findall(music_content)
        if customer_match:
            addon.setSetting('customerID', customer_match[0])
            log(customer_match[0])
    return "success"


def parseHTML(response):
    response = re.sub(r'(?i)(<!doctype \w+).*>', r'\1>', response)
    soup = BeautifulSoup(response, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return soup


def cleanInput(str):
    if type(str) is not unicode:
        str = unicode(str, "iso-8859-15")
        xmlc = re.compile('&#(.+?);', re.DOTALL).findall(str)
        for c in xmlc:
            str = str.replace("&#"+c+";", unichr(int(c)))
    p = HTMLParser()
    str = p.unescape(str)
    return str


def debug(content):
    if (NODEBUG):
        return
    #print unicode(content).encode("utf-8")
    #log(content, xbmc.LOGDEBUG)
    log(unicode(content), xbmc.LOGDEBUG)

def log(msg, level=xbmc.LOGNOTICE):
    # xbmc.log('%s: %s' % (addonID, msg), level)
    log_message = u'{0}: {1}'.format(addonID, msg)
    xbmc.log(log_message.encode("utf-8"), level)
    """
    xbmc.LOGDEBUG = 0
    xbmc.LOGERROR = 4
    xbmc.LOGFATAL = 6
    xbmc.LOGINFO = 1
    xbmc.LOGNONE = 7
    xbmc.LOGNOTICE = 2
    xbmc.LOGSEVERE = 5
    xbmc.LOGWARNING = 3
    """

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addDir(name, url, mode, iconimage, Artist=None, Album=None):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url.encode("utf8"))+"&mode="+str(mode)+"&thumb="+urllib.quote_plus(iconimage.encode("utf8"))
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=iconimage)
    liz.setInfo(type="music", infoLabels={"title": name})
    liz.setProperty("fanart_image", defaultFanart)
    if Artist:
        u+="&artist="+urllib.quote_plus(Artist.encode("utf8"))
    if Album:
        u+="&album="+urllib.quote_plus(Album.encode("utf8"))
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addLink(name, mode, asin , iconimage, duration, trackNr="", artist="", album_title="", year="", genre="", rating="", show_artist_and_title = False, unlimited_color = False):
#    filename = (''.join(c for c in url if c not in '/\\:?"*|<>')).strip()+".jpg"
#    fanartFile = os.path.join(cacheFolderFanartTMDB, filename)
    if unlimited_color:
        link_name = '[COLOR gold]%s[/COLOR]'
    else:
        link_name = '%s'
    u = sys.argv[0]+"?mode="+str(mode)+"&asin="+ str(asin)+"&name="+urllib.quote_plus(name.encode("utf8"))+"&thumb="+urllib.quote_plus(iconimage.encode("utf8"))+"&artist="+urllib.quote_plus(artist.encode("utf8"))+"&album="+urllib.quote_plus(album_title.encode("utf8"))
    ok = True
    if show_artist_and_title == True:
        link_name = link_name % (artist + ": " + name)
        liz = xbmcgui.ListItem(link_name, iconImage="DefaultMusicSongs.png", thumbnailImage=iconimage)
    else:
        link_name = link_name % (name)

        liz = xbmcgui.ListItem(link_name, iconImage="DefaultMusicSongs.png", thumbnailImage=iconimage)
    liz.setInfo(type="music", infoLabels={"title": name, "duration": duration, "year": year, "genre": genre, "rating": rating, "tracknumber": trackNr, "artist": artist, "album": album_title })
#    liz.setProperty("fanart_image", fanartFile)
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def prepareMechanizeBrowser():
    br = mechanize.Browser()
    br.set_cookiejar(cj)
    br.set_handle_gzip(True)
    br.set_handle_robots(False)
    br.addheaders = [('User-Agent', userAgent),
                ('X-Requested-With', 'XMLHttpRequest'),
                ('Accept-Encoding', 'gzip, deflate'),
                ('Content-Type', 'application/x-www-form-urlencoded'),
                ('Accept', 'application/json, text/javascript, */*; q=0.01'),
                ('csrf-token', addon.getSetting('csrf_Token')),
                ('csrf-rnd', addon.getSetting('csrf_rndToken')),
                ('csrf-ts', addon.getSetting('csrf_tsToken'))]
    return br


"""
following part that does consist of the two variabled _hexdig and _hextobyte and the two methods
__unquote_to_bytes(string) and __unquote(string, encoding='utf-8', errors='replace') and the regexp _asciire
are needed because the unquoting method of the urllib in python 2.7 is broken. Thus I used the one from python 3
"""
_hexdig = '0123456789ABCDEFabcdef'

_hextobyte = None

def __unquote_to_bytes(string):
    string = string.encode('utf-8')
    bits = string.split(b'%')
    if len(bits) == 1:
        return string
    res = [bits[0]]
    append = res.append
    # Delay the initialization of the table to not waste memory
    # if the function is never called
    global _hextobyte
    if _hextobyte is None:
        _hextobyte = dict((a+b, chr(int(a+b,16))) for a in _hexdig for b in _hexdig)
    for item in bits[1:]:
        try:
            append(_hextobyte[item[:2]])
            append(item[2:])
        except KeyError:
            append(b'%')
            append(item)
    return b''.join(res)

_asciire = re.compile('([\x00-\x7f]+)')

def __unquote(string, encoding='utf-8', errors='replace'):
    string = string.replace('+', ' ')
    if '%' not in string:
        string.split
        return string
    if encoding is None:
        encoding = 'utf-8'
    if errors is None:
        errors = 'replace'
    bits = _asciire.split(string)
    res = [bits[0]]
    append = res.append
    for i in range(1, len(bits), 2):
        append(__unquote_to_bytes(bits[i]).decode(encoding, errors))
        append(bits[i + 1])
    return ''.join(res)


params = parameters_string_to_dict(sys.argv[2])
mode = __unquote(params.get('mode', ''))
url = __unquote(params.get('url', ''))
asin = __unquote(params.get('asin', ''))
thumb = __unquote(params.get('thumb', ''))
name = __unquote(params.get('name', ''))
g_artist = __unquote(params.get('artist', ''))
g_album = __unquote(params.get('album', ''))

if not os.path.isdir(addonUserDataFolder):
    os.mkdir(addonUserDataFolder)
if not os.path.isdir(cacheFolder):
    os.mkdir(cacheFolder)
#if not os.path.isdir(cacheFolderFanartTMDB):
#    os.mkdir(cacheFolderFanartTMDB)

if os.path.exists(os.path.join(addonUserDataFolder, "cookies")):
    os.rename(os.path.join(addonUserDataFolder, "cookies"), cookieFile)

if mode == 'playTrack':
    playlist_name = ""
    playlist_name = xbmcgui.Window(10000).getProperty("AmazonMusic-CurrentPlaylist")
    if playlist_name:
        xbmcgui.Window(10000).setProperty("AmazonMusic-PlayingPlaylist", playlist_name)
else:
    xbmcgui.Window(10000).clearProperty("AmazonMusic-CurrentPlaylist")
    xbmcgui.Window(10000).clearProperty("AmazonMusic-PlayingPlaylist")

#log(mode)

if os.path.exists(cookieFile):
    cj.load(cookieFile)

    if mode == 'listAlbums':
        listAlbums(url)
    elif mode == 'listPlaylists':
        listPlaylists(url)
    elif mode == 'listSongs':
        listSongs(url)
    elif mode == 'listSearchedSongs':
        listSearchedSongs(url)
    elif mode == 'listGenres':
        listGenres()
    elif mode == 'playTrack':
        playTrack(asin)
    elif mode == 'search':
        search(url)
    elif mode == 'login':
        login()
    elif mode == 'deleteCookies':
        deleteCookies()
    elif mode == 'deleteCache':
        deleteCache()
    elif mode == 'listOwnPlaylists':
        listOwnPlaylists()
    elif mode == 'showPlaylistContent':
        showPlaylistContent()
    elif mode == 'listOwnAlbums':
        listOwnAlbums()
    elif mode == 'listOwnArtists':
        listOwnArtists()
    elif mode == 'showAlbumContent':
        showAlbumContent(g_artist, g_album)
    elif mode == 'showArtistContent':
        showArtistContent(g_artist)
    elif mode == 'storePassword':
        storePassword()
    elif mode == 'deletePassword':
        deletePassword()
    elif mode == 'listFollowed':
        showListFollowed()
    elif mode == 'lookupList':
        showLookupList(asin)
    elif mode == 'listRecentlyPlayed':
        showListRecentlyPlayed()
    else:
        index()
else:
    index()

