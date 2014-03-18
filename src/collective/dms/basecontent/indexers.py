import logging

from ZODB.POSException import ConflictError
from five import grok
from Products.CMFCore.utils import getToolByName
from plone.indexer import indexer

from .dmsdocument import IDmsDocument

@indexer(IDmsDocument)
def document_dynamic_searchable_text_indexer(obj):
    indexed_elements = [obj.title]

    # if there is no path to text/plain, do nothing
    transforms = getToolByName(obj, 'portal_transforms')

    had_version = False
    for child in reversed(obj.values()):
        if child.portal_type in ('dmsmainfile', 'dmsappendixfile'):
            if not child.file or child.file.getSize() == 0:
                continue

            if not transforms._findPath(child.file.contentType, 'text/plain'):
                continue

            # only index the latest version
            if child.portal_type == 'dmsmainfile' and had_version:
                continue
            had_version = True

            # convert it to text/plain
            try:
                datastream = transforms.convertTo(
                    'text/plain', child.file.data, mimetype=child.file.contentType,
                    filename=child.file.filename)
                indexed_elements.append(unicode(datastream.getData(), 'utf-8'))
            except (ConflictError, KeyboardInterrupt):
                raise
            except Exception as e:
                # ignore transformation errors, too bad
                log = logging.getLogger('collective.dms.basecontent')
                log.exception(e)

    return u' '.join(indexed_elements)

grok.global_adapter(document_dynamic_searchable_text_indexer,
                    name='SearchableText')
