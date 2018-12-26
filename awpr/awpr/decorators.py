from django.core.exceptions import PermissionDenied
from functools import wraps
import logging
logger = logging.getLogger(__name__)

# PR2018-11-03 from https://www.python-course.eu/python3_decorators.php

#def our_decorator(func):
#    def function_wrapper(x):
#        print("Before calling " + func.__name__)
#        func(x)
#        print("After calling " + func.__name__)
#    return function_wrapper
#def foo(x):
#    print("Hi, foo has been called with " + str(x))

#print("We call foo before decoration:")
#foo("Hi")
#print("We now decorate foo with f:")
#foo = our_decorator(foo)
#print("We call foo after decoration:")
#foo(42)

#output:
#We call foo before decoration:
#Hi, foo has been called with Hi
#We now decorate foo with f:
#We call foo after decoration:
#Before calling foo
#Hi, foo has been called with 42
#After calling foo



def user_examyear_is_correct(func):
    @wraps(func)
    def wrap(request, *args, **kwargs):
        print("Before calling " + func.__name__)
        entry_id = kwargs['entry_id']
        #entry = Entry.objects.get(pk=entry_id)

        logger.debug("Before calling " + func.__name__ + str(kwargs) + ' Type: ' + str(type(kwargs)))

        func2 = func(request, *args, **kwargs)

        if request.examyear_checked:
            return func2
        else:
            raise PermissionDenied

    return wrap
#=================================

def call_counter(func):
    def helper(*args, **kwargs):
        helper.calls += 1
        return func(*args, **kwargs)
    helper.calls = 0

    return helper

@call_counter
def succ(x):
    return x + 1

@call_counter
def mul1(x, y=1):
    return x*y + 1