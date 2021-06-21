# -*- coding: utf-8 -*-

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
                value = {"token": term.token, "title": term.title}
            # Some fields (e.g. language) have a default value that is not in
            # vocabulary
            except LookupError:
                pass
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
        return json_compatible(value)
