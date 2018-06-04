# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from redturtle.importer.rer.testing import REDTURTLE_IMPORTER_RER_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that redturtle.importer.rer is properly installed."""

    layer = REDTURTLE_IMPORTER_RER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if redturtle.importer.rer is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'redturtle.importer.rer'))

    def test_browserlayer(self):
        """Test that IRedturtleImporterRerLayer is registered."""
        from redturtle.importer.rer.interfaces import (
            IRedturtleImporterRerLayer)
        from plone.browserlayer import utils
        self.assertIn(
            IRedturtleImporterRerLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = REDTURTLE_IMPORTER_RER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get(userid=TEST_USER_ID).getRoles()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['redturtle.importer.rer'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if redturtle.importer.rer is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'redturtle.importer.rer'))

    def test_browserlayer_removed(self):
        """Test that IRedturtleImporterRerLayer is removed."""
        from redturtle.importer.rer.interfaces import \
            IRedturtleImporterRerLayer
        from plone.browserlayer import utils
        self.assertNotIn(
           IRedturtleImporterRerLayer,
           utils.registered_layers())
