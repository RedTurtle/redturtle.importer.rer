# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from collective.transmogrifier.transmogrifier import Transmogrifier
from plone import api
from plone.app.uuid.utils import uuidToObject
from plone.dexterity.utils import iterSchemata
from redturtle.importer.base import logger
from redturtle.importer.base.browser.migrations import RedTurtlePlone5MigrationMain  # noqa
from rer.linknormativa.base.interfaces import INormativaType
from transmogrify.dexterity.interfaces import IDeserializer
from urlparse import urlparse
from zope.component import getAdapter
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema import getFieldsInOrder

import transaction


def _domain_extractor(url):
    name = urlparse(url)[1].replace('www.', '')
    # print u"Dominio rilevato: {}".format(name)
    return name


def _domain_fix(url):
    """ Questa funzione prende un url con dominio che finisce per '.tv' e lo
    sistema mettendoci .it per poi restituirlo.
    """
    fixed_url = url.replace(
        'multipler.lepida.tv',
        'multipler.lepida.it',
    )
    return fixed_url


class RERPlone5MigrationMain(RedTurtlePlone5MigrationMain):

    def scripts_post_migration(self):
        super(RERPlone5MigrationMain, self).scripts_post_migration()
        self.fix_linkNormativa()
        self.fix_multipler_video_link()

    def fix_linkNormativa(self):
        brains = api.content.find(portal_type='LinkNormativa')
        print 'Found {0} items.'.format(len(brains))
        for brain in brains:
            normativa = brain.getObject()
            adapter = getAdapter(
                normativa,
                INormativaType,
                getattr(normativa, 'lawType', '')
            )
            normativa_url = adapter.createNormativaLink(
                normativa.effective_date,
                getattr(normativa, 'lawNumber', '')
            )

            setattr(normativa, 'remoteUrl', normativa_url)

            logger.warn('Fixed {0}'.format(normativa.absolute_url()))

    def fix_multipler_video_link(self):
        urls_changed = 0  # used for partial commit
        total_urls_changes = 0
        empty_urls = 0

        site = api.portal.get()
        print u'Getting all the video objects in the site...'
        video_brains = site.portal_catalog.unrestrictedSearchResults(
            portal_type=['WildcardVideo'],
        )
        print u'Checkin all the URLs...'
        for brain in video_brains:
            video_obj = brain.getObject()
            url = video_obj.video_url
            if url:
                domain = _domain_extractor(url)
                if domain.endswith('.tv'):
                    urls_changed += 1
                    print u'Fixing url for: {0}'.format(brain.getPath())
                    fixed_url = _domain_fix(url)

                    print u'From:\t{0}\nTo:\t{1}'.format(
                        url,
                        fixed_url,
                    )

                    video_obj.video_url = fixed_url
                    total_urls_changes += 1

                if urls_changed > 10:
                    try:
                        print 'Partial Commit...'
                        transaction.commit()
                        print 'Partial Commit: OK'
                    except Exception as e:
                        logger.error(
                            u'Error while committing transaction.')
                        logger.error(u'{0}'.format(e))
                    urls_changed = 0
            else:
                empty_urls += 1
                print u'ERROR: Wrong video_url field (empty) for: {0}'.format(
                    brain.getPath())

        print u'Total Video objects: {0}'.format(len(video_brains))
        print u'Video with empty URL fields: {0}'.format(empty_urls)
        print u'Total Video URLs changes: {0}'.format(total_urls_changes)
