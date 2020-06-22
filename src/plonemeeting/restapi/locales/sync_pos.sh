#!/usr/bin/env bash
files="plone imio.history"
languages="en fr"

for file in $files; do
    for language in $languages; do
        touch $language/LC_MESSAGES/$file.po
        i18ndude sync --pot $file.pot $language/LC_MESSAGES/$file.po
        msgfmt -o $language/LC_MESSAGES/$file.mo $language/LC_MESSAGES/$file.po
    done
done
