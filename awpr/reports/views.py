# PR2019-05-22
from django.shortcuts import render, redirect #, get_object_or_404
from awpr import functions as f

import logging
logger = logging.getLogger(__name__)


def download(request):
    # PR2018-04-29
    # function get_headerbar_param sets:
    # - activates request.user.language
    # - display/select schoolyear, schoolyear list, color red when not this schoolyear
    # - display/select school, school list
    # - display user dropdown menu
    # note: schoolyear, school and user are only displayed when user.is_authenticated

    # set headerbar parameters PR2018-08-06
    _display_school = False
    if request.user:
        _display_school = True
    _param = f.get_headerbar_param(request, {
        'display_school': _display_school
    })
    # PR2019-02-15 go to login form if user is not authenticated
    if request.user.is_authenticated:    # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'downloads.html', _param)
    else:
        return redirect('login')
