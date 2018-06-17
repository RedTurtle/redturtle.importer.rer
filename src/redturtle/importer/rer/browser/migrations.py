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
from zope.component import getAdapter
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema import getFieldsInOrder


class RERPlone5MigrationMain(RedTurtlePlone5MigrationMain):

    def do_migrate(self, REQUEST=None):
        authenticator = api.content.get_view(
            context=api.portal.get(),
            request=self.request,
            name=u'authenticator')
        if not authenticator.verify():
            raise Unauthorized

        self.cleanup_log_files()
        portal = api.portal.get()
        transmogrifier = Transmogrifier(portal)
        transmogrifier('rer.plone5.main')

        # nel transmogrifier c'e' una lista di tuple:
        # (path, fieldname, value) per le quali vanno rifatte le relations
        for (path, fieldname, value) in getattr(transmogrifier, "fixrelations", []):  # noqa
            logger.info('fix %s %s %s', path, fieldname, value)
            obj = self.context.unrestrictedTraverse(path)
            for schemata in iterSchemata(obj):
                for name, field in getFieldsInOrder(schemata):
                    if name == fieldname:
                        if isinstance(value, basestring):
                            value = uuidToObject(value)
                        else:
                            value = [uuidToObject(uuid) for uuid in value]
                        deserializer = IDeserializer(field)
                        value = deserializer(
                            value, [], {}, True, logger=logger)
                        # self.disable_constraints,
                        # logger=self.log,
                        field.set(field.interface(obj), value)
                        notify(ObjectModifiedEvent(obj))

        api.portal.show_message(
            message='Migration done. Check logs for a complete report.',
            request=self.request
        )

        # run scripts after migration
        self.scripts_post_migration()

        return self.request.response.redirect(
            '{0}/migration-results'.format(api.portal.get().absolute_url())
        )

    def scripts_post_migration(self):
        self.fix_linkNormativa()

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
