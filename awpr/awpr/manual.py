# PR2021-08-06
from django.contrib.auth.decorators import login_required # PR2018-04-01

from django.shortcuts import render, redirect #, get_object_or_404
from django.views.generic import View

from awpr import constants as c

import logging
logger = logging.getLogger(__name__)

from django.utils.translation import activate

