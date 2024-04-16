import re
import unicodedata
from time import time

from Products.LDAPMultiPlugins.interfaces import ILDAPMultiPlugin
from five import grok
from plone import api
from plone.memoize import ram
from plone.principalsource.source import PrincipalSource
from plone.principalsource.source import PrincipalSourceBinder
from z3c.formwidget.query.interfaces import IQuerySource
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm


# By default, we list groups and we can search for users in ajax
class PrincipalSource(PrincipalSource):

    BLACKLIST = ('AuthenticatedUsers', 'Administrators', 'Site Administrators', 'Reviewers')

    extra_default_values = None

    def search_principals(self, groups_first=False, **kw):
        if kw:
            results = self.acl_users.searchPrincipals(groups_first=True, **kw)
        else:
            # if no kw, we have been called from source __iter__ because
            # of Chosen widget populate_select attribute is set to True
            results = self.acl_users.searchGroups()
            if self.extra_default_values:
                # cf widget.py, CustomAjaxChosenMultiSelectionWidget::source
                results = list(results)
                user_ids = (
                    [self.extra_default_values]
                    if type(self.extra_default_values) not in (list, tuple)
                    else self.extra_default_values
                )
                for user_id in user_ids:
                    results.extend(self.acl_users.searchUsers(id=user_id))
        return [r for r in results if r.get('groupid', None) not in self.BLACKLIST]

    def searchGroups(self, **kwargs):
        result = self.acl_users.searchGroups(**kwargs)
        return [x for x in result if x['id'] not in self.BLACKLIST]

    @property
    def _search(self):
        if self.users and self.groups:
            return self.search_principals
        elif self.users:
            return self.acl_users.searchUsers
        elif self.groups:
            return self.searchGroups

    def search(self, query_string):
        query_string = unicodedata.normalize('NFKD', query_string).encode('ascii', 'ignore').decode('ascii')
        query_string = re.sub('[^\w\s-]', '', query_string).strip().lower()
        return super(PrincipalSource, self).search(query_string)


class PrincipalSourceBinder(PrincipalSourceBinder):

    def __call__(self, context):
        return PrincipalSource(context, self.users, self.groups)


class PrincipalsVocabularyFactory(grok.GlobalUtility):
    """Vocabulary for principals"""
    grok.name('dms.principals')
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        principals = PrincipalSourceBinder(users=True, groups=True)
        return principals(context)


class TreatingGroupsVocabulary(grok.GlobalUtility):
    """Vocabulary for treating groups"""
    grok.name('collective.dms.basecontent.treating_groups')
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        principals = PrincipalSourceBinder(users=True, groups=True)
#        principals = queryUtility(IVocabularyFactory, name=u'plone.principalsource.Principals')
        return principals(context)


class RecipientGroupsVocabulary(grok.GlobalUtility):
    """Vocabulary for recipient groups"""
    grok.name('collective.dms.basecontent.recipient_groups')
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
#        principals = queryUtility(IVocabularyFactory, name=u'plone.principalsource.Principals')
        principals = PrincipalSourceBinder(users=True, groups=True)
        return principals(context)


class LDAPEmailsVocabulary(grok.GlobalUtility):
    """Vocabulary for LDAP Emails"""
    grok.name('collective.dms.basecontent.ldap_emails')
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        return LDAPEmailSource()


class LDAPEmailSource(object):
    implements(IQuerySource)

    def __init__(self):
        portal = api.portal.get()
        ldap_plugins = [obj for obj in portal.acl_users.objectValues()
                        if ILDAPMultiPlugin.providedBy(obj)]
        if ldap_plugins:
            self.ldap_plugin = ldap_plugins[0]
            self.user_folder = self.ldap_plugin._getLDAPUserFolder()
        else:
            self.ldap_plugin = None
            self.user_folder = None

    def search(self, query_string):
        for email in self._get_ldap_emails():
            if query_string.lower() in email.lower():
                yield SimpleTerm(email)

    def __len__(self):
        return len(self._get_ldap_emails())

    def __iter__(self):
        for email in self._get_ldap_emails():
            yield SimpleTerm(email)

    def __contains__(self, value):
        try:
            self.getTerm(value)
        except LookupError:
            return False
        else:
            return True

    def getTermByToken(self, token):
        if token in self._get_ldap_emails():
            return SimpleTerm(token)
        else:
            raise LookupError(token)

    def getTerm(self, value):
        if value in self._get_ldap_emails():
            return SimpleTerm(value)
        else:
            raise LookupError(value)

    @ram.cache(lambda *args: time() // (60 * 60))
    def _get_ldap_emails(self):
        emails = set([])
        if not self.ldap_plugin:
            return emails

        users = self.ldap_plugin.enumerateUsers()
        for user in users:
            email = self._get_ldap_email(user['login'])
            if email:
                emails.add(email)

        return emails

    def _get_ldap_email(self, login):
        if not self.user_folder:
            return None

        unmangled_userid = self.ldap_plugin._demangle(login)
        ldap_user = self.user_folder.getUserById(unmangled_userid)
        if ldap_user is None:
            return None

        email = ldap_user._properties.get('email')
        return email
