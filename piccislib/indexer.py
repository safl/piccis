#!/usr/bin/env python
#
# Piccis - Picture control, indexing and synchronization
# Copyright (C) 2012  Simon A. F. Lund <safl@safl.dk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from base64 import b64decode
import fnmatch
import json
import os

import gdata.photos.service
import gdata.media
import gdata.geo

class Indexer(object):

    def __init__(self, name):

        self.name   = name
        self.path   = os.path.expanduser("~/.piccis/%s-index.json" % name)
        self.index  = {}

        if os.path.exists( self.path ):
            self.from_file()

        super(Indexer, self).__init__()

    def refresh(self, limit=[]):
        pass

    def from_file(self, path=None):
        
        if not path:
            path = self.path
        
        with open(path, "r") as fd:
            self.index = json.load( fd )

    def to_file(self, path=None, index=None):

        if not index:
            index = self.index

        if not path:
            path = self.path

        with open(path, "w") as fd:
            json.dump(index, fd, sort_keys=True, indent=1)

class Picasa(Indexer):

    def __init__(self, name, username, password):

        self.username   = username
        self.cli        = gdata.photos.service.PhotosService()

        self.cli.email     = username
        self.cli.password  = password
        self.cli.source    = 'safltech-piccis-0.1a'
        self.cli.ProgrammaticLogin()

        super(Picasa, self).__init__('picasa-%s' % name)

    def refresh(self, limit=[]):
        
        index  = {}
        albums  = self.cli.GetUserFeed(user= self.username)
        count   = len(limit) if limit else len(albums.entry)
        cur     = 1
        
        print "Indexing albums..."
        for album in (a for a in albums.entry if (a.title.text in limit) or not limit):
            print " %d / %d ..." % (cur, count),
            print 'title: %s, number of photos: %s, id: %s' % (album.title.text,
          album.numphotos.text, album.gphoto_id.text)
            cur += 1
            photos = self.cli.GetFeed(
                '/data/feed/api/user/%s/albumid/%s?kind=photo' % (self.cli.email, album.gphoto_id.text)
            )
            if album.title.text not in index:
                index[album.title.text] = []

            for photo in photos.entry:
                p = {
                    'title':        photo.title.text,
                    'size':         int(photo.size.text),
                    'timestamp':    int(photo.timestamp.text)
                }
                index[album.title.text].append(p)

        self.index = index
        return index

class Local(Indexer):

    def __init__(self, name, root):

        self.root = root

        super(Local, self).__init__('local-%s' % name)

    def refresh(self, limit=[]):

        index = {}
        for root, dirs, files in os.walk(self.root):
            text = os.path.basename(root)

            if text not in index:
                index[text] = []

            for fn in files:
                stat = os.stat(root+os.sep+fn)
                index[text].append({'size': stat.st_size, 'timestamp':stat.st_ctime, 'title':fn})

        self.index = index
        return index

if __name__ == "__main__":
    main()
