from AccessControl import getSecurityManager
from zope.interface import implements, implementer
from zope.cachedescriptors.property import CachedProperty
from zope.component import adapter, getUtility
from zope.intid.interfaces import IIntIds

from zc.relation.interfaces import ICatalog

from z3c.form.interfaces import IFormLayer, IFieldWidget
from z3c.form.widget import FieldWidget
from z3c.relationfield.interfaces import IRelationList
from z3c.relationfield.schema import RelationChoice, RelationList

from plone.formwidget.contenttree.widget import MultiContentTreeWidget
from plone.formwidget.contenttree import ObjPathSourceBinder

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class IRelatedDocs(IRelationList):
    """"""

class RelatedDocsWidget(MultiContentTreeWidget):
    display_template = ViewPageTemplateFile('related-docs-display.pt')

    def __init__(self, display_backrefs, request):
        self.display_backrefs = display_backrefs
        super(RelatedDocsWidget, self).__init__(request)

    def get_url(self, v):
        return self.request.physicalPathToURL(v)

    def get_label(self, v):
        term = self.terms.getTermByToken(v)
        return term.title

    def get_content_type(self, v):
        portal = self.context.portal_url.getPortalObject()
        document = portal.unrestrictedTraverse(v)
        return document.Type()

    def update(self):
        super(RelatedDocsWidget, self).update()
        if self.mode == 'display':
            if self.tuples and not self.value:
                # hack to not have the 'empty' class added to the field
                self.value = ["don't hide field"]

    @CachedProperty
    def tuples(self):
        refs = [(
            self.get_url(x),
            self.get_label(x),
            self.get_content_type(x),
        ) for x in self.value]
        if self.display_backrefs:
            intids = getUtility(IIntIds)
            catalog = getUtility(ICatalog)
            try:
                doc_intid = intids.getId(self.context)
            except KeyError:
                pass
            else:
                sm = getSecurityManager()
                for ref in catalog.findRelations({'to_id': doc_intid}):
                    obj = ref.from_object
                    if not sm.checkPermission('View', obj):
                        continue
                    url = self.get_url(ref.from_path)
                    tp = (url, obj.Title(), obj.Type())
                    if tp not in refs:
                        refs.append(tp)
        return refs


@adapter(IRelatedDocs, IFormLayer)
@implementer(IFieldWidget)
def RelatedDocsFieldWidget(field, request):
    return FieldWidget(field, RelatedDocsWidget(field.display_backrefs, request))


class RelatedDocs(RelationList):
    implements(IRelatedDocs)

    def __init__(self, portal_types=None,
                       display_backrefs=False, **kwargs):
        self.display_backrefs = display_backrefs
        kw = dict()
        if portal_types:
            kw['portal_type'] = portal_types
        RelationList.__init__(self,
                        value_type=RelationChoice(
                            title=u'',
                            source=ObjPathSourceBinder(**kw)),
                        **kwargs)
