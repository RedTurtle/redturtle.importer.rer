# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import defaultKeys
from collective.transmogrifier.utils import defaultMatcher
from collective.transmogrifier.utils import Matcher
from DateTime import DateTime
from plone.i18n.normalizer.interfaces import IIDNormalizer
from redturtle.importer.rer import logger
from zope.component import getUtility
from zope.interface import classProvides
from zope.interface import implementer

import copy

SKIP_TYPES = [
    'Aforisma',
    'AreaReferenti',
    'ChiediEsperto',
    'Corso',
    'ERNews',
    'ERNewsExternal',
    'ERPortletPage',
    'Event',
    'Materia',
    'PloneBoard',
    'PlonePopoli',
    'PoiIssue',
    'PoiTracker',
    'RERAssessore',
    'SimpleVocabulary',
    'SimpleVocabularyTerm',
    'Sub Survey',
    'Survey Matrix Question',
    'Survey Select Question',
    'Survey Text Question',
    'Survey',
    'VocabularyLibrary',
]


@implementer(ISection)
class RERCustomMapping(object):
    """Mapping for specific RER content type
    """

    classProvides(ISectionBlueprint)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)

        self.typekey = defaultMatcher(
            options, 'type-key', name, 'type', ('portal_type', 'Type')
        )

    def __iter__(self):
        for item in self.previous:
            keys = item.keys()
            typekey = self.typekey(*keys)[0]
            pathkey = self.pathkey(*keys)[0]

            if not (typekey and pathkey):
                logger.warn('Not enough info for item: {0}'.format(item))
                yield item
                continue

            if not pathkey:  # not enough info
                yield item
                continue
            path = item[pathkey]
            # not private content
            if item.get('is_private', None):
                continue
            if item[typekey] == 'RERSubsite':
                item[typekey] = 'RERSubsite'
                item['subsite_color'] = item['subsiteColor']
                if item.get('_datafield_image', None):
                    item['_datafield_image'] = item['_datafield_image']
                yield item
                continue
            elif item[typekey] == 'Folder Deepening':
                item[typekey] = 'Folder'
                yield item
                continue
            elif item[typekey] == 'FolderTaxonomy':
                item[typekey] = 'Folder'
                yield item
                continue
            elif item[typekey] == 'RERAreaTematica':
                # item[typekey] = 'Folder'
                # yield item
                continue
            elif item[typekey] == 'RERLinksFolder':
                # item[typekey] = 'Folder'
                # yield item
                continue
            elif item[typekey] == 'GeoLocation':
                item[typekey] = 'Venue'
                yield item
                continue
            elif item[typekey] == 'Structured Document':
                item[typekey] = 'Folder'
                yield item

                pageitem = copy.deepcopy(item)
                pageitem[typekey] = 'Document'
                pageitem[pathkey] += '/index.html'
                pageitem['_id'] = 'index.html'
                pageitem['id'] = 'index.html'
                pageitem['_uid'] = None
                pageitem['_layout'] = 'structured_content_view'
                yield pageitem
                continue
            elif item[typekey] == 'RTRemoteVideo':
                item[typekey] = 'WildcardVideo'
                item['retrieve_thumb'] = True
                item['video_url'] = item['remoteUrl']

                # TODO : fix video_url

                item['transcript'] = item['text']  # ???
                yield item
                continue
            elif item[typekey] == 'RTInternalVideo':
                item[typekey] = 'WildcardVideo'
                item['transcript'] = item['text']  # ???
                if '_datafield_file' in item:
                    item['_datafield_video_file'] = item['_datafield_file']
                yield item
                continue
            elif item[typekey] == 'ALPubblicazione':
                item[typekey] = 'Pubblicazione'
                yield item
                continue

            # passaparola
            elif item[typekey] == 'Classifieds':
                item[typekey] = 'BulletinBoard'
                yield item
                continue
            elif item[typekey] == 'ClassifiedsCategory':
                item[typekey] = 'AdsCategory'
                yield item
                continue
            elif item[typekey] == 'Classified':
                if (
                    not item.get('expiration_date', None)
                    or DateTime(item['expiration_date']) < DateTime()
                ):
                    continue
                else:
                    item[typekey] = 'Advertisement'
                    yield item

                    # gestione custom dell'immagine addizionale
                    if item.get('additionalImage', None):
                        normalizer = getUtility(IIDNormalizer)

                        additionalImageItem = copy.deepcopy(item)
                        additionalImageItem[typekey] = 'Image'
                        additionalImageItem['title'] = item['additionalImage'][
                            'filename'
                        ]  # noqa
                        additionalImageItem['_datafield_image'] = item[
                            '_datafield_additionalimage'
                        ]  # noqa
                        additionalImageItem[pathkey] += (
                            '/' + additionalImageItem['title']
                        )
                        additionalImageItem['_layout'] = ''
                        additionalImageItem['id'] = normalizer.normalize(
                            additionalImageItem['title']
                        )
                        additionalImageItem['_id'] = normalizer.normalize(
                            additionalImageItem['title']
                        )
                        additionalImageItem['_uid'] = None

                        if additionalImageItem.get('image', None):
                            del additionalImageItem['image']
                        if additionalImageItem.get('additionalImage', None):
                            del additionalImageItem['additionalImage']
                        if additionalImageItem.get(
                            '_datafield_additionalimage', None
                        ):
                            del additionalImageItem[
                                '_datafield_additionalimage'
                            ]  # noqa

                        yield additionalImageItem

                    continue

            # passalibro
            elif item[typekey] == 'Bookcrossing':
                item[typekey] = 'BulletinBoard'
                yield item
                continue
            elif item[typekey] == 'BookcrossingCategory':
                item[typekey] = 'AdsCategory'
                yield item
                continue
            elif item[typekey] == 'BookcrossingInsertion':
                if (
                    not item.get('expiration_date', None)
                    or DateTime(item['expiration_date']) < DateTime()
                ):
                    continue
                else:
                    item[typekey] = 'BookCrossing'
                    yield item
                    continue
            elif item[typekey] == 'Link':
                internal_link = item.get('internal_link', '')
                external_link = item.get('remoteUrl', '')
                if internal_link:
                    item['remoteUrl'] = u'${}/resolveuid/{}'.format(
                        '{portal_url}', internal_link
                    )
                elif external_link:
                    item['remoteUrl'] = external_link
                else:
                    import pdb

                    pdb.set_trace()
                yield item
                continue
            elif item[typekey] in SKIP_TYPES:
                continue

            yield item
