import datetime

from five import grok
from plone.dexterity.interfaces import IDexterityFTI
from zope.cachedescriptors.property import CachedProperty
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.i18nmessageid import MessageFactory
import z3c.table.table
import z3c.table.column
from z3c.table.interfaces import IBatchProvider

from plone.batching.interfaces import IBatch
from plone import api

PMF = MessageFactory('plone')

grok.templatedir('templates')


class TableViewlet(grok.Viewlet):
    grok.baseclass()
    grok.template('filesviewlet')
    __table__ = NotImplemented
    label = NotImplemented
    noresult_message = NotImplemented

    def update(self):
        self.table = self.__table__(self.context, self.request)
        self.table.viewlet = self
        self.table.update()


class Table(z3c.table.table.Table):
    cssClassEven = u'even'
    cssClassOdd = u'odd'
    cssClasses = {'table': 'listing nosort'}
    sortOn = None
    batchSize = 10000  # not used
    startBatchingAt = 10000  # not used
    batchProviderName = 'plonebatch'

    def batchRows(self):
        # this is not self.rows that is batched, but self.values
        pass

    def updateBatch(self):
        if IBatch.providedBy(self.values):
            self.batchProvider = getMultiAdapter((self.context,
                self.request, self), IBatchProvider,
                name=self.batchProviderName)
            self.batchProvider.update()

    @CachedProperty
    def translation_service(self):
        return api.portal.get_tool('translation_service')

    @CachedProperty
    def wtool(self):
        return api.portal.get_tool('portal_workflow')

    @CachedProperty
    def portal_url(self):
        return api.portal.get().absolute_url()

    def update(self):
        super(Table, self).update()

    def format_date(self, date, long_format=None, time_only=None):
        if date is None:
            return u""

        # If date is a datetime object, isinstance(date, datetime.date)
        # returns True, so we use type here.
        if type(date) == datetime.date:
            date = date.strftime('%Y/%m/%d')
        elif type(date) == datetime.datetime:
            date = date.strftime('%Y/%m/%d %H:%M')

        return self.translation_service.ulocalized_time(
            date,
            long_format=long_format,
            time_only=time_only,
            context=self.context,
            domain='plonelocales',
            request=self.request)

    def renderRow(self, row, cssClass=None):
        from .column import StateColumn, get_value
        isSelected = self.isSelectedRow(row)
        if isSelected and self.cssClassSelected and cssClass:
            cssClass = '%s %s' % (self.cssClassSelected, cssClass)
        elif isSelected and self.cssClassSelected:
            cssClass = self.cssClassSelected
        cells = [self.renderCell(item, col, colspan)
                 for item, col, colspan in row]

        for index in (
                'can_last_version_validate',
                'has_last_version_accept',
                'has_last_version_refuse',
        ):
            if getattr(item, index, False):
                cssClass += ' row-state-%s' % index

        fti = getUtility(IDexterityFTI, name=item.portal_type)
        if 'pfwbgedlink' in getattr(fti, 'allowed_content_types', []):
            cssClass += ' row-state-linkable'

        state_column = [x for x in row if isinstance(x[1], StateColumn)]
        if state_column:
            state_column = state_column[0]
            state_value = get_value(self.request, state_column[0], 'review_state')
            if state_value:
                cssClass += ' row-state-%s' % state_value

        from pfwbged.collection.searchview import TaskTypeColumn
        type_column = [x for x in row if isinstance(x[1], TaskTypeColumn)]
        if type_column:
            type_column = type_column[0]
            type_value = get_value(self.request, type_column[0], 'portal_type')
            if type_value:
                cssClass += ' row-type-%s' % type_value

        cssClass = self.getCSSClass('tr', cssClass)
        return u'\n    <tr%s>%s\n    </tr>' % (cssClass, u''.join(cells))
