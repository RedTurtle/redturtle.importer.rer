# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from collective.transmogrifier.transmogrifier import Transmogrifier
from plone import api
from plone.app.uuid.utils import uuidToObject
from plone.dexterity.utils import iterSchemata
from redturtle.importer.base import logger
from redturtle.importer.base.browser.migrations import RedTurtlePlone5MigrationMain  # noqa
from transmogrify.dexterity.interfaces import IDeserializer
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
        return self.request.response.redirect(
            '{0}/migration-results'.format(api.portal.get().absolute_url())
        )
