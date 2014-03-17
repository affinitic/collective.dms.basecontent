import tempfile

from Acquisition import aq_parent
from BTrees.Length import Length

from five import grok

from zope import schema
from zope.annotation.interfaces import IAnnotations
from zope.interface import implements
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from plone.autoform import directives as form
from plone.dexterity.content import Item
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.directives.form import default_value
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from plone.app.contenttypes.interfaces import IFile

from . import _


class IDmsFile(model.Schema, IFile):
    """Schema for DmsFile"""
    title = schema.TextLine(
        title=_(u'Version number'),
        required=False
    )
    form.mode(title='hidden')

    model.primary('file')
    file = NamedBlobFile(
        title=_(u"File"),
        required=True,
    )

    label = schema.TextLine(
        title=_(u'Label'),
        required=False,
    )

    signed = schema.Bool(
        title=_("Signed version"),
        default=False)


class DmsFile(Item):
    """DmsFile"""
    implements(IDmsFile)
    __ac_local_roles_block__ = True

    incomingmail = False

    def Title(self):
        if self.incomingmail:
            return _(u"Incoming mail")
        elif hasattr(self, 'signed') and self.signed:
            return _(u"Signed version")
        else:
            return self.title


class DmsFileSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for DmsFile"""

    def bases(self, schemaName, tree):
        return (IDmsFile, )


class IDmsAppendixFile(model.Schema, IFile):
    """Schema for DmsAppendixFile"""
    model.primary('file')
    file = NamedBlobFile(
        title=_(u"File"),
        required=True,
    )


class DmsAppendixFile(Item):
    """DmsAppendixFile"""
    implements(IDmsAppendixFile)
    __ac_local_roles_block__ = True


class DmsAppendixFileSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for DmsAppendixFile"""

    def bases(self, schemaName, tree):
        return (IDmsAppendixFile, )


@default_value(field=IDmsFile['title'])
def titleDefaultValue(data):
    container = data.context
    annotations = IAnnotations(container)
    if 'higher_version' not in annotations:
        version_number = 1
    else:
        version_number = annotations['higher_version'].value + 1
    return unicode(version_number)


@grok.subscribe(IDmsFile, IObjectAddedEvent)
def update_higher_version(context, event):
    container = context.getParentNode()
    annotations = IAnnotations(container)
    if 'higher_version' not in annotations:
        annotations['higher_version'] = Length()
    annotations['higher_version'].change(1)


from plone.dexterity.filerepresentation import ReadFileBase, DefaultWriteFile

from zope.component import adapts
from zope.filerepresentation.interfaces import IRawWriteFile

from plone.memoize.instance import memoize


class DmsFileReadFile(ReadFileBase):
    adapts(IDmsFile)

    @property
    def mimeType(self):
        if not self.context.file:
            return None
        return self.context.file.contentType

    @property
    def encoding(self):
        return 'utf-8'

    @property
    def name(self):
        if not self.context.file:
            return None
        return self.context.file.filename

    def size(self):
        if not self.context.file:
            return None
        return self.context.file.getSize()

    @memoize
    def _getStream(self):
        if not self.context.file:
            return None
        out = tempfile.TemporaryFile(mode='w+b')
        out.write(self.context.file.data)
        out.seek(0)
        return out


class DmsFileWriteFile(DefaultWriteFile):
    implements(IRawWriteFile)
    adapts(IDmsFile)

    def close(self):
        self._message = self._parser.close()
        self._closed = True
        self.context.file.data = self._message.get_payload()


@grok.subscribe(IDmsFile, IObjectModifiedEvent)
def reindex_document_on_changed_file(context, event):
    document = aq_parent(context)
    document.reindexObject()
