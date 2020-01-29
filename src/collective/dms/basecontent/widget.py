import z3c.form.interfaces
import zope.component
from collective.select2.browser import BaseSearch
from collective.z3cform.chosen.widget import AjaxChosenMultiSelectionWidget
from z3c.form import interfaces
from zope.component import getUtility
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory


class CustomAjaxChosenMultiSelectionWidget(AjaxChosenMultiSelectionWidget):
    @property
    def source(self):
        # We have a custom source property because we know it will be a
        # PrincipalSource and it would only be prefilled with groups,
        # while we may need to also have some users in that list if the
        # default value has some. (otherwise to would be cleaned up as invalid
        # values before presenting the form to the user, removing the users
        # from the default value, only keeping the groups)
        source = self.field.bind(self.context).value_type.source
        adapter = zope.component.queryMultiAdapter(
                (self.context, self.request, self.form, self.field, self),
                interfaces.IValue, name='default')
        if adapter:
            source.extra_default_values = adapter.get()
        return source


@implementer(z3c.form.interfaces.IFieldWidget)
def AjaxChosenMultiFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field,
        CustomAjaxChosenMultiSelectionWidget(request))
    widget.populate_select = True
    widget.ignoreMissing = True
    return widget


class LDAPEmailsSearch(BaseSearch):
    """Search for LDAP emails, allow dynamic option selection"""
    def results(self, search_term, add_terms=False):
        factory = getUtility(
            IVocabularyFactory,
            'collective.dms.basecontent.ldap_emails',
        )
        vocabulary = factory(self.context)
        found = False

        for term in vocabulary:
            if search_term.lower() in term.token.lower():
                found = True
                yield {
                    "text": term.value,
                    "id": term.value,
                }

        # make the search term a selectable value
        # if it doesn't match any existing email
        if add_terms and not found:
            yield {
                "text": search_term,
                "id": search_term
            }
