# -*- coding: utf-8 -*-
from redturtle.importer.base.interfaces import IMigrationContextSteps
from zope.interface import implementer

try:
    from plone.formwidget.geolocation.geolocation import Geolocation
except Exception:
    pass


@implementer(IMigrationContextSteps)
class VenueSteps(object):
    """
    """

    def __init__(self, context):
        self.context = context

    def doSteps(self, item):
        """
        Initialize Geolocation field
        """
        try:
            geolocation_obj = Geolocation(item.get('latitude'), item.get('longitude'))
            setattr(self.context, 'geolocation', geolocation_obj)
        except:
            pass
