import zope.component

from zope.schema.interfaces import ISource, IContextSourceBinder
from zope.interface import implementer
import z3c.form.interfaces

from z3c.form import interfaces, util, value

from collective.z3cform.chosen.widget import AjaxChosenMultiSelectionWidget

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
