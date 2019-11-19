# -*- coding: utf-8 -*-


def listify(value):
    ''' '''
    if not hasattr(value, '__iter__'):
        value = [value]
    return value
