# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.sections.constructor import ConstructorSection
from DateTime import DateTime
from plone import api
from plone import namedfile
from plone.app.textfield.value import RichTextValue
from redturtle.importer.rer import logger
from zope.event import notify
from zope.interface import alsoProvides
from zope.interface import classProvides
from zope.interface import implementer
from zope.lifecycleevent import ObjectAddedEvent

try:
    from rer.subsites.interfaces import IRERSubsiteEnabled
except Exception:
    pass

import base64
import os
import re
import urllib2


@implementer(ISection)
class RERCustomBeforeConstructor(ConstructorSection):
    classProvides(ISectionBlueprint)

    def fix_download_in_tiny(self, text):
        if 'resolveuid' not in text:
            return text
        if 'at_download' in text:
            text = text.replace('at_download/file', '@@download/file')
        return text

    def fix_image_url_in_tiny(self, text):
        for size in ['big', 'newshome', 'maxi', 'custom', 'micro']:
            if ('/image_{0}'.format(size)) in text:
                # print "UPDATE: %s (%s) %s" % (brain.getPath(), brain.portal_type, size)
                # TODO: regexp ?
                text = text.replace(
                    '/image_{0}'.format(size),
                    '/@@images/image/{0}'.format(size)
                )
        return text

    def __init__(self, transmogrifier, name, options, previous):
        super(RERCustomBeforeConstructor, self).__init__(
            transmogrifier, name, options, previous)

    def __iter__(self):
        for item in self.previous:
            keys = item.keys()
            typekey = self.typekey(*keys)[0]
            pathkey = self.pathkey(*keys)[0]

            if not (typekey and pathkey):
                logger.warn('Not enough info for item: {0}'.format(item))
                yield item
                continue
            type_, path = item[typekey], item[pathkey]

            item['is_rer_subsite'] = False
            if type_ == 'RERSubsite':
                type_ = 'Folder'
                item[typekey] = 'Folder'
                item['is_rer_subsite'] = True

            # delete default view from this migrate object
            if type_ == 'BulletinBoard' \
                    or type_ == 'Advertisement' \
                    or type_ == 'BookCrossing':
                if item.get('_layout'):
                    del item['_layout']

            if item.get('text'):
                text_fixed = self.fix_download_in_tiny(item['text'])
                text_fixed = self.fix_image_url_in_tiny(text_fixed)
                item['text'] = text_fixed

            # check exchange_method of BulletinBoard
            if type_ == 'BulletinBoard' and item.get('bookcrossingExchangeMethods', None):
                exchange_methods = api.portal.get_registry_record(
                    'rer.ads.bookcrossing.interfaces.IRERAdsBookCrossingSettings.exchange_methods')
                if exchange_methods:
                    exchange_methods = map(lambda x: x.split(
                        '|')[0], exchange_methods.split('\r\n'))
                else:
                    exchange_methods = []
                new_methods = filter(
                    lambda x: x not in exchange_methods, item['bookcrossingExchangeMethods'])
                methods = map(lambda x: x + '|' + x + '\r\n',
                              exchange_methods + new_methods)
                methods[-1] = methods[-1].replace('\r\n', '')
                api.portal.set_registry_record(
                    'rer.ads.bookcrossing.interfaces.IRERAdsBookCrossingSettings.exchange_methods',
                    ''.join(
                        methods
                    )
                )

            yield item


@implementer(ISection)
class RERCustomAfterConstructor(ConstructorSection):
    classProvides(ISectionBlueprint)

    def __init__(self, transmogrifier, name, options, previous):
        super(RERCustomAfterConstructor, self).__init__(
            transmogrifier, name, options, previous)

        if os.environ.get('remote_user'):
            self.remote_username = os.environ.get('remote_user')
        if os.environ.get('remote_password'):
            self.remote_password = os.environ.get('remote_password')

    def __iter__(self):
        for item in self.previous:
            keys = item.keys()
            typekey = self.typekey(*keys)[0]
            pathkey = self.pathkey(*keys)[0]

            if not (typekey and pathkey):
                logger.warn('Not enough info for item: {0}'.format(item))
                yield item
                continue
            type_, path = item[typekey], item[pathkey]

            obj = self.context.unrestrictedTraverse(
                str(item[pathkey]).lstrip('/'),
                None
            )

            if not obj:
                yield item
                continue

            if getattr(obj, 'text', None):
                raw_text = obj.text.raw
                if '@@download' in raw_text:
                    fixed_text = re.sub(r'(/@@download/.*?)"', r'"', raw_text)
                    setattr(
                        obj,
                        'text',
                        RichTextValue(
                            raw=fixed_text,
                            outputMimeType='text/x-html-safe',
                            mimeType=u'text/html')
                    )

            if type_ == 'Folder' and item['is_rer_subsite']:
                if not IRERSubsiteEnabled.providedBy(obj):
                    alsoProvides(obj, IRERSubsiteEnabled)
                    obj.reindexObject(idxs=['object_provides'])
                    obj.subsite_color = item.get('subsite_color', None)

                    if item.get('_datafield_image', None):
                        image_params = item['_datafield_image']
                        image_data = urllib2.urlopen(
                            image_params['data_uri']
                        ).read()
                        obj.image = namedfile.NamedBlobImage(
                            image_data,
                            contentType=image_params['content_type'],
                            filename=image_params['filename']
                        )

            if type_ == 'SchedaER':
                links_info = [
                    'toDeepen',
                    'rulesAndActs',
                    'modules',
                    'ongoingProjects',
                    'initiatives',
                    'publications',
                    'usefulLinks',
                    'seeOther'
                ]
                for el in links_info:
                    link_data = ''
                    if item.get(el, ''):
                        for line in item.get(el):
                            if line['link'].startswith('http'):
                                link_data += '<p><ul><li><a href="' \
                                    + line['link'] \
                                    + '" data-linktype="external" data-val="' \
                                    + line['link'] + '">' \
                                    + line['title'] \
                                    + '</a></li></ul></p>'
                            else:
                                link_data += '<p><ul><li><a href="../resolveuid/' \
                                    + line['uid'] \
                                    + '" data-linktype="internal" data-val="' \
                                    + line['uid'] \
                                    + '">' \
                                    + line['title'] \
                                    + '</a></li></ul></p>'
                        tmp_text = RichTextValue(
                            link_data,
                            'text/html',
                            'text/x-plone-outputfilters-html'
                        )
                        setattr(obj, el, tmp_text)
                        del item[el]

            if type_ == 'LinkNormativa':
                if getattr(obj, 'lawType', None):
                    setattr(obj, 'lawType', item.get('lawType'))
                logger.info('Fired event to setup remoteUrl for: {0}'.format(
                    obj.absolute_url())
                )
                notify(ObjectAddedEvent(obj))

            if type_ == 'Pubblicazione':
                if item['publicationDate']:
                    obj.publicationDate = DateTime(
                        item['publicationDate']
                    ).asdatetime()
                if item.get('_datafield_image', None):
                    image_params = item['_datafield_image']
                    image_data = urllib2.urlopen(
                        image_params['data_uri']
                    ).read()
                    obj.image = namedfile.NamedBlobImage(
                        image_data,
                        contentType=image_params['content_type'],
                        filename=image_params['filename']
                    )
                if item.get('_datafield_file', None):
                    file_params = item['_datafield_file']
                    file_data = urllib2.urlopen(
                        file_params['data_uri']
                    ).read()
                    obj.publicationFile = namedfile.NamedBlobFile(
                        file_data,
                        filename=file_params['filename']
                    )

            if type_ == 'Circolare':
                if getattr(obj, 'file1') and obj.file1.getSize() == 0:
                    del obj.file1
                if getattr(obj, 'file2') and obj.file2.getSize() == 0:
                    del obj.file2
                if getattr(obj, 'file3') and obj.file3.getSize() == 0:
                    del obj.file3

            # bisogna prendere solo le immagini all'interno degli annunci del
            # mercatino
            if type_ == 'Image' and \
                    (obj.aq_parent.portal_type == 'Advertisement' or
                     obj.aq_parent.portal_type == 'BookCrossing'):
                if item.get('_datafield_image', None):
                    image_params = item['_datafield_image']

                    request = urllib2.Request(image_params['data_uri'])
                    base64string = base64.encodestring(
                        '{0}:{1}'.format(
                            self.remote_username, self.remote_password
                        )
                    ).replace('\n', '')
                    request.add_header(
                        'Authorization', 'Basic {0}'.format(base64string)
                    )

                    image_data = urllib2.urlopen(request).read()
                    obj.image = namedfile.NamedBlobImage(
                        image_data,
                        contentType=image_params['content_type'],
                        filename=image_params['filename']
                    )

            yield item
