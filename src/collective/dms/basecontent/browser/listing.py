# -*- coding: utf-8 -*-

from five import grok

from zope.interface import Interface
from zope.cachedescriptors.property import CachedProperty
from zope.i18n import translate
from zope.i18nmessageid import MessageFactory

from Products.CMFCore.utils import getToolByName

from collective.dms.basecontent import _
from collective.dms.basecontent.browser import column
from collective.dms.basecontent.browser.table import Table


grok.templatedir('templates')

PMF = MessageFactory('plone')


class BaseTable(Table):

    @CachedProperty
    def values(self):
        portal_catalog = getToolByName(self, 'portal_catalog')
        folder_path = '/'.join(self.context.getPhysicalPath())
        query = {'path': {'query': folder_path},
                 'sort_on': 'getObjPositionInParent',
                 'sort_order': 'ascending'}
        query.update(self.viewlet.contentFilter())
        results = portal_catalog.searchResults(query)
        return results


class VersionsTable(BaseTable):
    @CachedProperty
    def values(self):
        return [x for x in self.context.getFolderContents() if x.portal_type == 'dmsmainfile']


class DmsAppendixTable(VersionsTable):
    @CachedProperty
    def values(self):
        return [x for x in self.context.getFolderContents() if x.portal_type == 'dmsappendixfile']

    def setUpColumns(self):
        columns = super(DmsAppendixTable, self).setUpColumns()
        return [column for column in columns if column.__name__ not in ('dms.state', 'dms.label')]


class TasksTable(BaseTable):
    pass


class InformationsTable(TasksTable):
    pass



class ColourColumn(column.ColourColumn):
    grok.name('dms.colour')
    grok.adapts(Interface, Interface, BaseTable)


class BaseTitleColumn(column.TitleColumn):
    grok.name('dms.title')
    grok.adapts(Interface, Interface, BaseTable)


class VersionsTitleColumn(BaseTitleColumn):
    grok.adapts(Interface, Interface, VersionsTable)
    domain = 'collective.dms.basecontent'
    linkCSS = 'version-link'
    header = _(u"№")

    def getLinkContent(self, item):
        content = super(VersionsTitleColumn, self).getLinkContent(item)
        return translate(content, domain=self.domain, context=self.request)


class AppendixTitleColumn(column.Column):
    grok.adapts(Interface, Interface, DmsAppendixTable)
    grok.name('dms.title')
    weight = 10
    header = PMF("Title")

    def renderCell(self, item):
        title = column.get_value(self.request, item, 'Title')
        if isinstance(title, unicode):
            return title
        else:
            return unicode(title, 'utf-8', 'ignore')


class TaskTitleColumn(BaseTitleColumn):
    grok.adapts(Interface, Interface, TasksTable)
    linkCSS = 'overlay-comment-form'


class DownloadColumn(column.DownloadColumn):
    grok.name('dms.download')
    grok.adapts(Interface, Interface, VersionsTable)


class EditColumn(column.EditColumn):
    grok.name('dms.edit')
    grok.adapts(Interface, Interface, VersionsTable)


class ExternalEditColumn(column.ExternalEditColumn):
    grok.name('dms.extedit')
    grok.adapts(Interface, Interface, VersionsTable)


class DeleteColumn(column.DeleteColumn):
    grok.name('dms.delete')
    grok.adapts(Interface, Interface, VersionsTable)


class AuthorColumn(column.PrincipalColumn):
    grok.name('dms.author')
    grok.adapts(Interface, Interface, VersionsTable)
    header = _(u"Author")
    weight = 30
    attribute = 'Creator'


class UpdateColumn(column.DateColumn):
    grok.name('dms.update')
    grok.adapts(Interface, Interface, VersionsTable)
    header = PMF(u"listingheader_modified")
    attribute = 'modified'
    weight = 40


class StateColumn(column.StateColumn):
    grok.name('dms.state')
    grok.adapts(Interface, Interface, BaseTable)
    weight = 50


class InformationStateColumn(column.StateColumn):
    """StateColumn for informations"""
    grok.name('dms.state')
    grok.adapts(Interface, Interface, InformationsTable)
    weight = 50

    def renderCell(self, item):
        title_mapping = {'todo': _(u'To read'),
                         'done': _(u'Read')
                         }
        if callable(item.review_state):
            review_state = item.review_state()
        else:
            review_state = item.review_state
        state_title = title_mapping[review_state]
        return translate(_(state_title), context=self.request)


class EnquirerColumn(column.PrincipalColumn):
    grok.name('dms.enquirer')
    grok.adapts(Interface, Interface, TasksTable)
    header = _(u"Enquirer")
    weight = 20
    attribute = 'enquirer'


class ResponsibleColumn(column.PrincipalColumn):
    grok.name('dms.responsible')
    grok.adapts(Interface, Interface, TasksTable)
    header = _(u"Responsible")
    weight = 30
    attribute = 'responsible'


class DeadlineColumn(column.DateTimeColumn):
    grok.name('dms.deadline')
    grok.adapts(Interface, Interface, TasksTable)
    header = _(u"Deadline")
    attribute = 'deadline'
    weight = 60

class InformationCreationDateColumn(column.DateTimeColumn):
    grok.name('dms.deadline')
    grok.adapts(Interface, Interface, InformationsTable)
    header = _(u"Creation date")
    attribute = 'created'
    weight = 60


class VersionLabelColumn(column.LabelColumn):
    grok.name('dms.label')
    grok.adapts(Interface, Interface, VersionsTable)
    attribute = 'label'
    header = _(u"Label")
    weight = 15
