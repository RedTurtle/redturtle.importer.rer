from DateTime import DateTime
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher
from collective.transmogrifier.utils import traverse
from zope.interface import classProvides
from zope.interface import implementer


@implementer(ISection)
class RERCollectionMapping(object):
    """Map collection criterion on the right type
    """
    classProvides(ISectionBlueprint)

    def __init__(self, transmogrifier, name, options, previous):
        """
        """
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')

    def __iter__(self):

        for item in self.previous:

            pathkey = self.pathkey(*item.keys())[0]
            if not pathkey:  # not enough info
                yield item
                continue
            path = item[pathkey]

            ob = traverse(self.context, str(path).lstrip('/'), None)
            if ob is None:
                yield item
                continue  # object not found
            query = item.get('query', None)

            if query and hasattr(ob, 'query'):
                for criterion in query:
                    if 'portal_type' in criterion.values():
                        tmp_list = []
                        for ctype in criterion['v']:
                            if ctype == 'RTRemoteVideo' or ctype == 'RTInternalVideo':  # noqa
                                ctype = 'WildcardVideo'
                            tmp_list.append(ctype)
                        criterion.update({'v': tmp_list})

            yield item
