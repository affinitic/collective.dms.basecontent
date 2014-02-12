from zope.interface import implementer
import z3c.form.interfaces

from collective.z3cform.chosen.widget import AjaxChosenMultiSelectionWidget


@implementer(z3c.form.interfaces.IFieldWidget)
def AjaxChosenMultiFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field,
        AjaxChosenMultiSelectionWidget(request))
    widget.populate_select = True
    widget.ignoreMissing = True
    return widget
