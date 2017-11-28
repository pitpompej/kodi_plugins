
from __future__ import unicode_literals
import urllib
import urlparse
import urllib2
#import requests
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
import base64
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
from HTMLParser import HTMLParser
import resources.lib.ScrapeUtils as ScrapeUtils
from BeautifulSoup import BeautifulSoup
import ssl

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
addon.setSetting('email', '')
addon.setSetting('password', '')
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
    if loginResult=="prime":
        addDir(translation(30002), urlMain+"/s/ref=dmm_pr_bbx_album?ie=UTF8&bbn=5686557031&rh=i%3Adigital-music-album", 'listAlbums', "")
        addDir(translation(30003), urlMain+"/s/ref=s9_rbpl_bw_srch?__mk_de_DE=%C5M%C5Z%D5%D1&rh=i%3Adigital-music-playlist%2Cn%3A5686557031%2Cp_n_format_browse-bin%3A5686558031&sort=featured-rank", 'listAlbums', "")
        addDir(translation(30004), "", 'listGenres', "")
        addDir(translation(30005), urlMain+"/s/ref=s9_aas_bw_srch?__mk_de_DE=%C5M%C5Z%D5%D1&rh=i%3Adigital-music-album%2Cn%3A5686557031%2Cp_n_format_browse-bin%3A180848031%2Cp_n_date_first_available_prime%3A6969880031&bbn=5686557031&sort=featured-rank&rw_html_to_wsrp=1&pf_rd_m=A3JWKAKR8XB7XF&pf_rd_s=merchandised-search-5&pf_rd_r=6RVAXVCW0CXA3QF4F86R&pf_rd_t=101&pf_rd_p=805206707&pf_rd_i=7457104031", 'listAlbums', "")
        addDir(translation(30016), "albums", 'search', "")
        addDir(translation(30017), "songs", 'search', "")
        addDir(translation(30010), "playlists", 'listOwnPlaylists', "")
        xbmcplugin.endOfDirectory(pluginhandle)
    elif loginResult == "captcha_req":
        xbmc.executebuiltin(unicode('XBMC.Notification(Info:,'+translation(30083)+',10000,'+icon+')').encode("utf-8"))
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
            videoID = match[0]
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
            videoID = match[0]
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

def playMP3Track(songId):
    content = trackPostUnicodeGetRestrictedPage('https://music.amazon.de/dmls/', songId)
    url_list_match = re.compile('urlList":\["(.+?)"',re.DOTALL).findall(content)
    if url_list_match:
        mp3_file_string = url_list_match[0]
        play_item = xbmcgui.ListItem(path=mp3_file_string)
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
    spl = content.split("metadata")
    for i in range(1, len(spl), 1):
        entry = spl[i]

        listId=re.compile(':"(.+?)"').findall(entry)
        songTitle=re.compile('"title":"(.+?)"').findall(entry)
        artist=re.compile('"artistName":"(.+?)"').findall(entry)
        album_title=re.compile('"albumName":"(.+?)"').findall(entry)
        trackID=re.compile('"asin":"(.+?)"').findall(entry)
        album_image_match = ""
        album_image=re.compile('"albumCoverImageLarge":"(.+?)"').findall(entry)
        if album_image:
            album_image_match = album_image[0]
        if songTitle and ('"primeStatus":"PRIME"' in entry or '"primeStatus":"NOT_PRIME"' in entry) and '"status":"AVAILABLE"' in entry:
            addLink(artist[0]+": "+songTitle[0], "playTrack", trackID[0], album_image_match, "", "", artist[0], album_title[0])
        elif songTitle and ('"purchased":"true"' in entry or '"instantImport":"true"' in entry):
            trackID=re.compile('"objectId":"(.+?)"').findall(entry)
            addLink(artist[0]+": "+songTitle[0], "playMP3Track", trackID[0], album_image_match, "", "", artist[0], album_title[0])
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
        xbmc.executebuiltin('Container.SetViewMode(%s)' % defaultview_songs)
    xbmc.sleep(100)


def playlistPostUnicodePage(url, playlistId = ""):
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
    resp = ''
    content = ''
    data = "maxResults=100&Operation=getPlaylists&caller=getServerListSongs&albumArtUrlsRedirects=false&albumArtUrlsSizeList.member.1=LARGE&trackColumns.member.1=albumAsin&trackColumns.member.2=artistAsin&trackColumns.member.3=albumArtistName&trackColumns.member.4=albumName&trackColumns.member.5=artistName&trackColumns.member.6=assetType&trackColumns.member.7=duration&trackColumns.member.8=objectId&trackColumns.member.9=sortAlbumArtistName&trackColumns.member.10=sortAlbumName&trackColumns.member.11=sortArtistName&trackColumns.member.12=title&trackColumns.member.13=asin&trackColumns.member.14=primeStatus&trackColumns.member.15=status&trackColumns.member.16=extension&trackColumns.member.17=purchased&trackColumns.member.18=uploaded&trackColumns.member.19=instantImport&trackColumns.member.20=albumCoverImageLarge&ContentType=JSON&customerInfo.customerId=" + addon.getSetting('customerID') + "&customerInfo.deviceId=" + addon.getSetting('req_dev_id') + "&customerInfo.deviceType=A16ZV8BU3SN1N3"
    if playlistId:
        data += "&includeTrackMetadata=true&trackCountOnly=false&playlistIdList.member.1=" + playlistId
    else:
        data += "&includeTrackMetadata=false&trackCountOnly=true&playlistIdList=&nextResultsToken="
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
        deleteCookies()
        login("dummy")
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


def login(content = None, statusOnly = False):
    is_prime_expression = "config.isPrimeMember',true"
    if content is None:
        content = getUnicodePage(urlMainS)
    signoutmatch = re.compile("declare\('config.signOutText',(.+?)\);", re.DOTALL).findall(content)
    if is_prime_expression in content: #
        return "prime"
    elif signoutmatch and signoutmatch[0].strip() != "null":
        return "noprime"
    else:
        if statusOnly:
            return "none"
        deleteCookies()
        content = ""
        keyboard = xbmc.Keyboard('', translation(30090))
        keyboard.doModal()
        if keyboard.isConfirmed() and unicode(keyboard.getText(), "utf-8"):
            email = unicode(keyboard.getText(), "utf-8")
            keyboard = xbmc.Keyboard('', translation(30091), True)
            keyboard.setHiddenInput(True)
            keyboard.doModal()
            if keyboard.isConfirmed() and unicode(keyboard.getText(), "utf-8"):
                password = unicode(keyboard.getText(), "utf-8")
                br = mechanize.Browser()
                br.set_cookiejar(cj)
                br.set_handle_gzip(True)
                br.set_handle_robots(False)
                br.addheaders = [('User-Agent', userAgent)]
                content = br.open(urlMainS+"/gp/dmusic/marketing/CloudPlayerLaunchPage/ref=dm_dp_mcn_cp")
                br.select_form(name="signIn")
                br["email"] = email
                br["password"] = password
                br.addheaders = [('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
                         ('Accept-Encoding', 'gzip, deflate'),
                         ('Accept-Language', 'de,en-US;q=0.8,en;q=0.6'),
                         ('Cache-Control', 'max-age=0'),
                         ('Connection', 'keep-alive'),
                         ('Content-Type', 'application/x-www-form-urlencoded'),
                         ('User-Agent', userAgent),
                         ('Upgrade-Insecure-Requests', '1')]
                br.submit()
                resp = br.response().read()
                content = unicode(resp, "utf-8")
                while 'auth-mfa-form' in content :
                    soup = parseHTML(content)
                    log('MFA form')
                    if 'auth-mfa-form' in content:
                        msg = soup.find('form', attrs={'id': 'auth-mfa-form'})
                        msgtxt = msg.p.renderContents().strip()
                        kb = xbmc.Keyboard('', msgtxt)
                        kb.doModal()
                        if kb.isConfirmed() and kb.getText():
                            xbmc.executebuiltin('ActivateWindow(busydialog)')
                            br.select_form(nr=0)
                            br['otpCode'] = kb.getText()
                        else:
                            return "none"
                    br.submit()
                    resp = br.response().read()
                    content = unicode(resp, "utf-8")
                    soup = parseHTML(content)
                    xbmc.executebuiltin('Dialog.Close(busydialog)')
                content = content.replace("\\","")
                captcha_match = re.compile('ap_captcha_title', re.DOTALL).findall(content)
                if captcha_match:
                    log("Captcha required!")
                    return "captcha_req"
                match = re.compile('"csrf_ts":"(.+?)"', re.DOTALL).findall(content)
                if match:
                    addon.setSetting('csrf_tsToken', match[0])
                    log(match[0])
                match = re.compile('"csrf_rnd":"(.+?)"', re.DOTALL).findall(content)
                if match:
                    addon.setSetting('csrf_rndToken', match[0])
                    log(match[0])
                match = re.compile('"csrf_token":"(.+?)"', re.DOTALL).findall(content)
                if match:
                    addon.setSetting('csrf_Token', match[0])
                    log(match[0])
                cj.save(cookieFile, ignore_discard=True, ignore_expires=True)
                for cookie in cj:
                    if cookie.name == "ubid-acbde":
                        dev_id = cookie.value.replace("-", "")
                        addon.setSetting('req_dev_id', dev_id)
                content = getUnicodePage(urlMainS)
                customer_match = re.compile('"customerID":"(.+?)"', re.DOTALL).findall(content)
                if customer_match:
                    addon.setSetting('customerID', customer_match[0])
                    log(customer_match[0])
        signoutmatch = re.compile("declare\('config.signOutText',(.+?)\);", re.DOTALL).findall(content)
        if is_prime_expression in content: #
            return "prime"
        elif signoutmatch[0].strip() != "null":
            return "noprime"
        else:
            return "none"


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


def addDir(name, url, mode, iconimage, context_entries=[]):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url.encode("utf8"))+"&mode="+str(mode)+"&thumb="+urllib.quote_plus(iconimage.encode("utf8"))
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=iconimage)
    liz.setInfo(type="music", infoLabels={"title": name})
    liz.setProperty("fanart_image", defaultFanart)
    if len(context_entries) > 0:
        liz.addContextMenuItems(context_entries)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addLink(name, mode, asin , iconimage, duration, trackNr="", artist="", album_title="", year="", genre="", rating="", show_artist_and_title = False):
#    filename = (''.join(c for c in url if c not in '/\\:?"*|<>')).strip()+".jpg"
#    fanartFile = os.path.join(cacheFolderFanartTMDB, filename)
    u = sys.argv[0]+"?mode="+str(mode)+"&asin="+ str(asin)+"&name="+urllib.quote_plus(name.encode("utf8"))+"&thumb="+urllib.quote_plus(iconimage.encode("utf8"))+"&artist="+urllib.quote_plus(artist.encode("utf8"))+"&album="+urllib.quote_plus(album_title.encode("utf8"))
    ok = True
    if show_artist_and_title == True:
        liz = xbmcgui.ListItem(artist + ": " + name, iconImage="DefaultMusicSongs.png", thumbnailImage=iconimage)
    else:
        liz = xbmcgui.ListItem(name, iconImage="DefaultMusicSongs.png", thumbnailImage=iconimage)
    liz.setInfo(type="music", infoLabels={"title": name, "duration": duration, "year": year, "genre": genre, "rating": rating, "tracknumber": trackNr, "artist": artist, "album": album_title })
#    liz.setProperty("fanart_image", fanartFile)
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


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
    elif mode == 'playMP3Track':
        playMP3Track(asin)
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
    else:
        index()
else:
    index()

