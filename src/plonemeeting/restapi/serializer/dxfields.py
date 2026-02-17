# -*- coding: utf-8 -*-

from imio.helpers.content import get_schema_fields
from plone.app.textfield.value import RichTextValue
from plone.dexterity.interfaces import IDexterityContent
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.serializer.dxfields import ChoiceFieldSerializer
from plone.restapi.serializer.dxfields import CollectionFieldSerializer
from plonemeeting.restapi import logger
from plonemeeting.restapi.interfaces import IPMRestapiLayer
from zope.component import adapter
from zope.interface import implementer
from zope.schema.interfaces import IChoice
from zope.schema.interfaces import ICollection
from zope.schema.interfaces import IField
from zope.schema.interfaces import IVocabularyTokenized
from zope.schema.vocabulary import SimpleTerm


@adapter(IChoice, IDexterityContent, IPMRestapiLayer)
@implementer(IFieldSerializer)
class PMChoiceFieldSerializer(ChoiceFieldSerializer):
    """Override to take elephantvocabulary into account."""

    def __call__(self):
        # Binding is necessary for named vocabularies
        if IField.providedBy(self.field):
            self.field = self.field.bind(self.context)
        value = self.get_value()
        # XXX with elephanvocabulary, "real" vocab is stored on vocabulary.vocab
        vocab = getattr(self.field.vocabulary, "vocab", self.field.vocabulary)
        if value is not None and IVocabularyTokenized.providedBy(vocab):
            try:
                term = self.field.vocabulary.getTerm(value)
            # If not found, get it from the z3c.form that maybe uses a MissingTerms adapter...
            except LookupError:
                try:
                    view = self.context.restrictedTraverse("@@view")
                    view.update()
                    # widget_name is the field name prefixed with behavior if any
                    widget_name = [field for field in get_schema_fields(self.context, prefix=True)
                                   if field[1].__name__ == self.field.__name__][0][0]
                    widget = view.widgets[widget_name]
                    term = widget.terms.getTerm(value)
                except Exception:
                    # at worse use value as title
                    term = SimpleTerm(value, title=value)
            finally:
                value = {"token": term.token, "title": term.title}

        return json_compatible(value)


@adapter(ICollection, IDexterityContent, IPMRestapiLayer)
@implementer(IFieldSerializer)
class PMCollectionFieldSerializer(CollectionFieldSerializer):
    """Override to take elephantvocabulary into account."""

    def __call__(self):
        # Binding is necessary for named vocabularies
        if IField.providedBy(self.field):
            self.field = self.field.bind(self.context)
        value = self.get_value()
        value_type = self.field.value_type
        if value is not None and IChoice.providedBy(value_type):
            # XXX with elephanvocabulary, "real" vocab is stored on vocabulary.vocab
            vocab = getattr(value_type.vocabulary, "vocab", value_type.vocabulary)
            if IVocabularyTokenized.providedBy(vocab):
                values = []
                for v in value:
                    try:
                        term = value_type.vocabulary.getTerm(v)
                        values.append({u"token": term.token, u"title": term.title})
                    except LookupError:
                        logger.warning("Term lookup error: %r" % v)
                value = values
        # XXX fix for datagridfield containing RichTextValue
        if value and isinstance(value[0], dict):
            new_value = []
            for val in value:
                new_value.append({k: json_compatible(v, self.context) if isinstance(v, RichTextValue) else v
                                  for k, v in val.items()})
            value = new_value
        return json_compatible(value)
