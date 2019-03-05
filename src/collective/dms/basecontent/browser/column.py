import os.path
import Missing
from AccessControl import getSecurityManager
from Products.CMFCore.utils import getToolByName
from five import grok
from z3c.table import interfaces
from zope.i18nmessageid import MessageFactory
from zope.i18n import translate
import z3c.table.table
import z3c.table.column
from Products.CMFCore.WorkflowCore import WorkflowException
from zope.schema.interfaces import IVocabularyFactory
from zope.component import getUtility
import plone.api
from plone.memoize import ram
from zope.component import queryMultiAdapter

from collective.dms.basecontent import _

PMF = MessageFactory('plone')

grok.templatedir('templates')


class Column(z3c.table.column.Column, grok.MultiAdapter):
    grok.baseclass()
    grok.provides(interfaces.IColumn)

    def renderHeadCell(self):
        if not self.header:
            return ''
        if not hasattr(self, 'attribute'):
            return translate(self.header, context=self.request)
        return '<span data-sortable="%s">%s</span>' % (self.attribute,
                translate(self.header, context=self.request))


def _get_value_cachekey(method, request, item, attribute, default=None):
    return (item.getPath(), request.__dict__, attribute, default)


@ram.cache(_get_value_cachekey)
def get_value(request, item, attribute, default=None):
    try:
        value = getattr(item, attribute)
        if value is Missing.Value:
            return default
    except AttributeError:
        try:
            obj = get_object(request, item)
        except KeyError:
            # ouch
            return '-'
        value = getattr(obj, attribute, default)

    if callable(value):
        value = value()

    return value


def _get_object_cachekey(method, request, item):
    return (item.getPath(), request.__dict__)


@ram.cache(_get_object_cachekey)
def get_object(request, item):
    try:
        obj = item.getObject()
    except KeyError:
        # ouch
        return None
    else:
        return obj


class DateColumn(Column):
    grok.baseclass()
    attribute = NotImplemented

    def renderCell(self, item):
        value = get_value(self.request, item, self.attribute)
        return self.table.format_date(value)


class DateTimeColumn(Column):
    grok.baseclass()
    attribute = NotImplemented

    def renderCell(self, item):
        value = get_value(self.request, item, self.attribute)
        return self.table.format_date(value, long_format=True)


class PrincipalColumn(Column):
    grok.baseclass()
    attribute = NotImplemented

    def renderCell(self, item):
        value = get_value(self.request, item, self.attribute, default=())

        if not isinstance(value, (list, tuple)):
            value = (value,)

        factory = getUtility(IVocabularyFactory, 'plone.principalsource.Principals')
        principals_vocab = factory(self.context)

        principals = []
        for principal_id in value:
            if principal_id in principals_vocab:
                principals.append(principals_vocab.getTermByToken(principal_id).title)
            else:
                principals.append(unicode(principal_id))

        return ', '.join(principals)


class LinkColumn(z3c.table.column.LinkColumn, Column):
    grok.baseclass()

    def getLinkURL(self, item):
        """Setup link url."""
        if self.linkName is not None:
            return '%s/%s' % (item.getURL(), self.linkName)
        return item.getURL()

    def renderHeadCell(self):
        if not self.header:
            return ''
        if not hasattr(self, 'attribute'):
            return translate(self.header, context=self.request)
        return '<span data-sortable="%s">%s</span>' % (self.attribute,
                translate(self.header, context=self.request))



class TitleColumn(LinkColumn):
    grok.baseclass()
    header = PMF("Title")
    weight = 10
    cssClasses = {'td': 'title-column'}

    def getLinkContent(self, item):
        title = get_value(self.request, item, 'Title')
        if isinstance(title, unicode):
            return title
        else:
            return unicode(title, 'utf-8', 'ignore')

    def renderHeadCell(self):
        return '<span data-sortable="sortable_title">%s</span>' % (
                translate(self.header, context=self.request))


class IconColumn(object):
    cssClasses = {'td': 'icon-column'}

    def getLinkContent(self, item):
        content = super(IconColumn, self).getLinkContent(item)
        return u"""<img title="%s" src="%s" />""" % (
                content,
                '%s/%s' % (self.table.portal_url, self.iconName))


class ColourColumn(Column):
    grok.baseclass()
    header = u""
    weight = -1
    cssClasses = {'td': 'colour-column'}

    def renderCell(self, item):
        if hasattr(item, 'path_string'):
            path = item.path_string
        else:
            path = item.getPath()
        if item.portal_type in ('opinion', 'validation'):
            return u''
        return u"""<label><input type="checkbox" data-value="%s"></label>""" % path

    def renderHeadCell(self):
        return u"""<span class="colour-column-head"></span>"""


class DeleteColumn(IconColumn, LinkColumn):
    grok.baseclass()
    header = u""
    weight = 9
    linkName = "delete_confirmation"
    linkContent = PMF('Delete')
    linkCSS = 'edm-delete-popup'
    iconName = "++resource++delete_icon.png"
    linkContent = PMF(u"Delete")

    def getLinkCSS(self, item):
        obj = get_object(self.request, item)
        view = queryMultiAdapter((obj, self.request), name='can_be_trashed')
        if view and view.render():
            return ''
        return super(DeleteColumn, self).getLinkCSS(item)

    def getLinkURL(self, item):
        obj = get_object(self.request, item)
        view = queryMultiAdapter((obj, self.request), name='can_be_trashed')
        if view and view.render():
            return '%s/%s' % (item.getURL(), 'redirect_to_dmsdocument?workflow_action=send_to_trash')
        return super(DeleteColumn, self).getLinkURL(item)

    def actionAvailable(self, item):
        obj = get_object(self.request, item)
        if not obj:
            return False
        sm = getSecurityManager()
        return sm.checkPermission('Delete objects', obj)

    def renderCell(self, item):
        if not self.actionAvailable(item):
            return u""

        obj = get_object(self.request, item)
        if plone.api.content.get_state(obj, None) == 'trashed':
            return '<span>DEL</span>'

        return super(DeleteColumn, self).renderCell(item)


class DownloadColumn(IconColumn, LinkColumn):
    grok.baseclass()
    header = u""
    weight = 1
    linkName = "@@download"
    iconName = "download_icon.png"
    linkContent = _(u"Download file")


class ExternalEditColumn(IconColumn, LinkColumn):
    grok.baseclass()
    header = u""
    weight = 3
    linkName = "@@external_edit"
    iconName = "++resource++extedit_icon.png"
    linkContent = PMF(u"Edit with external application")

    def actionAvailable(self, item):
        obj = get_object(self.request, item)
        if not obj:
            return False
        sm = getSecurityManager()
        if not sm.checkPermission('Modify portal content', obj):
            return False

        if obj.file is None:
            return False

        ext = os.path.splitext(obj.file.filename)[-1].lower()
        if ext in (u'.pdf', u'.jpg', '.jpeg'):
            return False

        if not obj.restrictedTraverse('@@externalEditorEnabled').available():
            return False

        return True

    def renderCell(self, item):
        if not self.actionAvailable(item):
            return u""

        return super(ExternalEditColumn, self).renderCell(item)


class EditColumn(IconColumn, LinkColumn):
    grok.baseclass()
    header = u""
    weight = 2
    linkName = "edit"
    iconName = "edit.png"
    linkContent = PMF(u"Edit")
    linkCSS = 'overlay-form-reload'

    def actionAvailable(self, item):
        obj = get_object(self.request, item)
        if not obj:
            return False
        sm = getSecurityManager()
        return sm.checkPermission('Modify portal content', obj)

    def renderCell(self, item):
        if not self.actionAvailable(item):
            return u""

        return super(EditColumn, self).renderCell(item)


class StateColumn(Column):
    grok.baseclass()
    header = PMF(u"State")
    weight = 50

    def renderCell(self, item):
        try:
            wtool = self.table.wtool
            portal_type = get_value(self.request, item, 'portal_type')
            review_state = get_value(self.request, item, 'review_state')
            if not review_state:
                return u""
            state_title = wtool.getTitleForStateOnType(review_state,
                                                       portal_type)
            return translate(PMF(state_title), context=self.request)
        except WorkflowException:
            return u""

    def renderHeadCell(self):
        return '<span data-sortable="review_state">%s</span>' % (
                translate(self.header, context=self.request))


class LabelColumn(Column):
    grok.baseclass()
    attribute = NotImplemented

    def renderCell(self, item):
        value = get_value(self.request, item, self.attribute)
        if value is None or value == 'None':
            value = ''
        return value
