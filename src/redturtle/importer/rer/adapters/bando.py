# -*- coding: utf-8 -*-
from redturtle.importer.base.interfaces import IMigrationContextSteps
from zope.interface import implementer


@implementer(IMigrationContextSteps)
class BandoSteps(object):
    """
    """

    def __init__(self, context):
        self.context = context

    def doSteps(self):
        """
        Remove timezone from dates
        """
        scadenza_bando = getattr(self.context, 'scadenza_bando', None)
        if scadenza_bando:
            if scadenza_bando.tzinfo:
                self.context.scadenza_bando = scadenza_bando.replace(
                    tzinfo=None)
        self.context.reindexObject(idxs=['getScadenza_bando'])
