# PR2018-07-20
from django.contrib.auth.decorators import login_required # PR2018-04-01
from django.core.paginator import Paginator # PR2018-07-20
from django.core.exceptions import PermissionDenied # PR2018-11-03

from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

from django.db import connection
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect #, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import UpdateView, DeleteView, View, ListView, CreateView

from schools import models as sch_mod
from awpr import menus as awpr_menu

from subjects import models as subj_mod

from django.contrib.auth.mixins import UserPassesTestMixin

from subjects.forms import SubjectAddForm, SubjectEditForm, \
    LevelAddForm, LevelEditForm, SectorAddForm, SectorEditForm, \
    SubjecttypeAddForm, SubjecttypeEditForm, \
    SchemeAddForm, SchemeEditForm, SchemeitemAddForm, SchemeitemEditForm

from awpr import constants as c
from awpr import downloads as d
from awpr import functions as af
from awpr import validators as av

from schools import models as sch_mod
from subjects import models as sbj_mod

import json # PR2018-10-25
# PR2018-04-27
import logging
logger = logging.getLogger(__name__)

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)

"""

# PR2018-05-06
from django.utils.translation import activate, get_language_info, ugettext_lazy as _
# from https://simpleisbetterthancomplex.com/tips/2016/09/27/django-tip-15-cbv-mixins.html

class GetFormKwargsMixin(object):
    @property
    def form_valid_message(self):
        return NotImplemented

    form_invalid_message = 'Please correct the errors below.'

    def form_valid(self, form):
        messages.success(self.request, self.form_valid_message)
        return super(FormMessageMixin, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, self.form_invalid_message)
        return super(FormMessageMixin, self).form_invalid(form)

"""


@method_decorator([login_required], name='dispatch')
class LevelLogView(View):
    def get(self, request, pk):
        level_log = subj_mod.Level_log.objects.filter(level_id=pk).order_by('-modified_at')
        level = subj_mod.Level.objects.get(id=pk)
        _param = af.get_headerbar_param(request,  {'level_log': level_log, 'level': level})
        return render(request, 'level_log.html', _param)




# === Subjecttype =====================================
@method_decorator([login_required], name='dispatch')
class SubjecttypeListView(ListView):  # PR2018-08-11

    def get(self, request, *args, **kwargs):
        _params = awpr_menu.get_headerbar_param(request, {})
        if request.user.examyear is not None:
            # filter Subjecttypes of request.user.examyear 'Country is parent of Examyear PR2018-10-18
            subjecttypes = subj_mod.Subjecttype.objects.filter(examyear=request.user.examyear)

            _params.update({'subjecttypes': subjecttypes})
        return render(request, 'subjecttype_list.html', _params)


@method_decorator([login_required], name='dispatch')
class SubjecttypeAddView(CreateView):
    # PR2018-08-11
    def get(self, request, *args, **kwargs):
        form = SubjecttypeAddForm(request=request)
        _params = awpr_menu.get_headerbar_param(request, {
            'form': form,
        })
        return render(request, 'subjecttype_add.html', _params)

    def post(self, request, *args, **kwargs):
        form = SubjecttypeAddForm(request.POST, request=request)

        if form.is_valid():
            subjecttype = form.save(commit=False)

            # ======  set value 'examyear'  ============
            subjecttype.examyear = request.user.examyear

            # ======  save field 'depbase_list_field'  ============
            _clean_depbase_list_field = form.cleaned_data.get('depbase_list_field')  # Type: <class 'list'>
            subjecttype.depbase_list = af.get_depbase_list_field_sorted_zerostripped(_clean_depbase_list_field)

            subjecttype.save(request=self.request)

            return redirect('subjecttype_list_url')
        else:
            # If the form is invalid, render the invalid form.
            _param = awpr_menu.get_headerbar_param(request, {
                'form': form,
                'display_country': True
            })
            return render(request, 'subjecttype_add.html', _param)


@method_decorator([login_required], name='dispatch')
class SubjecttypeEditView(UserPassesTestMixin, UpdateView):  # PR2018-08-11
    model = subj_mod.Subjecttype
    form_class = SubjecttypeEditForm
    template_name = 'subjecttype_edit.html'
    context_object_name = 'subjecttype'

    # PR2018-11-03 from: https://python-programming.com/django/permission-checking-django-views/
    # UserPassesTestMixin uses test_func to check permissions
    def test_func(self):
        is_ok = False
        subjecttype_id = self.kwargs['pk']
        if subjecttype_id is not None:
            subjecttype = subj_mod.Subjecttype.objects.filter(id=subjecttype_id).first()
            if subjecttype.examyear is not None:
                is_ok = self.request.user.examyear_correct(subjecttype.examyear.id)
        return is_ok

    # from https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # PR 2018-05-25 add request to kwargs, so it passes request to the form
    def get_form_kwargs(self):
        kwargs = super(SubjecttypeEditView, self).get_form_kwargs()
        # add request to kwargs, so it can be passed to form
        kwargs.update({'request': self.request})
        return kwargs

    def form_valid(self, form):
        subjecttype = form.save(commit=False)

    # ======  save field 'depbase_list_field'  ============
        _clean_depbase_list_field = form.cleaned_data.get('depbase_list_field')  # Type: <class 'list'>
        subjecttype.depbase_list = af.get_depbase_list_field_sorted_zerostripped(_clean_depbase_list_field)

        subjecttype.save(request=self.request)

        return redirect('subjecttype_list_url')


@method_decorator([login_required], name='dispatch')
class SubjecttypeDeleteView(DeleteView):
    model = subj_mod.Subjecttype
    template_name = 'subjecttype_delete.html'  # without template_name Django searches for subjectdefault_confirm_delete.html
    success_url = reverse_lazy('subjecttype_list_url')

    def delete(self, request, *args, **kwargs):
       self.object = self.get_object()

       if self.request.user:
          self.object.delete(request=self.request)
          return HttpResponseRedirect(self.get_success_url())
       else:
          raise Http404 #or return HttpResponse('404_url')

@method_decorator([login_required], name='dispatch')
class SubjecttypeLogView(View):
    def get(self, request, pk):
        subjecttype_log = subj_mod.Subjecttype_log.objects.filter(subjecttype_id=pk).order_by('-modified_at')
        subjecttype = subj_mod.Subjecttype.objects.get(id=pk)
        _param = awpr_menu.get_headerbar_param(request,  {'subjecttype_log': subjecttype_log, 'subjecttype': subjecttype})
        return render(request, 'subjecttype_log.html', _param)


# === Scheme =====================================
@method_decorator([login_required], name='dispatch')
class SchemeListView(ListView):  # PR2018-08-23

    def get(self, request, *args, **kwargs):
        _param = awpr_menu.get_headerbar_param(request, {
            'display_country': True,
        })
        if request.user.country is not None:
            if request.user.examyear is not None:
                schemes = subj_mod.Scheme.objects.filter(department__examyear=request.user.examyear)
                _param.update({'schemes': schemes})
        return render(request, 'scheme_list.html', _param)


@method_decorator([login_required], name='dispatch')
class SchemeAddView(CreateView):  # PR2018-08-24

    def get(self, request, *args, **kwargs):
        form = SchemeAddForm(request=request) #, src=_src)
        _params = self.get_params(request, form)
        return render(request, 'scheme_add.html', _params)

    def post(self, request, *args, **kwargs):
        form = SchemeAddForm(request.POST, request=request)

        if form.is_valid():
            scheme = form.save(commit=False)
            scheme.save(request=self.request)
            return redirect('scheme_list_url')
        else:
            _params = self.get_params(request, form)
            return render(request, 'scheme_add.html', _params)

    def get_params(self, request, form):
        params = awpr_menu.get_headerbar_param(request, {
            'form': form,
        })

        # filter Departments of request.user.country
        deps = sch_mod.Department.get_dep_attr(request.user)
        params.update({'deps': json.dumps(deps)})

        # filter Levels of request.user.country
        levels = subj_mod.Level.get_level_attr(request.user)
        params.update({'levels': json.dumps(levels)})

        # filter Sectors of request.user.country
        sectors = subj_mod.Sector.get_sector_attr(request.user)
        params.update({'sectors': json.dumps(sectors)})

        # logger.debug('SchemeAddView params: ' + str(params) + ' Type: ' + str(type(params)))
        return  params

@method_decorator([login_required], name='dispatch')
class SchemeEditView(UpdateView):  # PR2018-08-24
    model = subj_mod.Scheme
    form_class = SchemeEditForm
    template_name = 'scheme_edit.html'
    context_object_name = 'scheme'

    def get_context_data(self, **kwargs):  # https://docs.djangoproject.com/en/2.1/ref/class-based-views/mixins-simple/
        context = super().get_context_data(**kwargs)

        deps = sch_mod.Department.get_dep_attr(self.request.user)
        context['deps'] = json.dumps(deps)

        levels = subj_mod.Level.get_level_attr(self.request.user)
        context['levels'] = json.dumps(levels)

        sectors = subj_mod.Sector.get_sector_attr(self.request.user)
        context['sectors'] = json.dumps(sectors)

        # context['display_country'] = True
        return context

    def get_form_kwargs(self):
        kwargs = super(SchemeEditView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_params(self, request, form):
        params = awpr_menu.get_headerbar_param(request, {
            'form': form,
            'display_country': True,
            'display_examyear': True,
        })
        return  params

    def form_valid(self, form):
        scheme = form.save(commit=False)
# TODO: scheme has field 'department', not 'dep_list' PR2019-01-18
        # ======  save field 'dep_list_field'  ============
        # _clean_dep_list_field = form.cleaned_data.get('dep_list_field')  # Type: <class 'list'>
        # scheme.dep_list = f.get_depbase_list_field_sorted_zerostripped(_clean_dep_list_field)

        # ======  save field 'depbase_list_field'  ============
        _clean_fields_field = form.cleaned_data.get('fields_field')  # Type: <class 'list'>
        scheme.fields = af.get_depbase_list_field_sorted_zerostripped(_clean_fields_field)


        scheme.save(request=self.request)
        return redirect('scheme_list_url')


@method_decorator([login_required], name='dispatch')
class SchemeDeleteView(DeleteView):
    model = subj_mod.Scheme
    template_name = 'scheme_delete.html'  # without template_name Django searches for subjectdefault_confirm_delete.html
    success_url = reverse_lazy('scheme_list_url')

    def delete(self, request, *args, **kwargs):
       self.object = self.get_object()

       if self.request.user:
          self.object.delete(request=self.request)
          return HttpResponseRedirect(self.get_success_url())
       else:
          raise Http404 #or return HttpResponse('404_url')


@method_decorator([login_required], name='dispatch')
class SchemeLogView(View):
    def get(self, request, pk):
        scheme_log = subj_mod.Scheme_log.objects.filter(scheme_id=pk).order_by('-modified_at')
        scheme = subj_mod.Scheme.objects.get(id=pk)
        _param = awpr_menu.get_headerbar_param(request,  {'scheme_log': scheme_log, 'scheme': scheme})
        return render(request, 'scheme_log.html', _param)

# +++++++++++++++++++++++++++++++++++

# === Schemeitem =====================================
@method_decorator([login_required], name='dispatch')
class SchemeitemListView(ListView):  # PR2018-11-09

    def get(self, request, *args, **kwargs):
        _params = self.get_params(request)
        return render(request, 'schemeitem_list.html', _params)


    def get_params(self, request):

        params = awpr_menu.get_headerbar_param(request, {
            'display_country': True,
            'select_examyear': True,
        })
        #if request.user.country is not None:
        #    if request.user.examyear is not None:
        #        schemeitems = Schemeitem.objects.filter(scheme__department__examyear=request.user.examyear)
        #        params.update({'schemeitems': schemeitems})


        # 'deps':
        # '{"11": {"abbrev": "Vsbo", "level_req": "true", "sector_req": "true"},
        # "12": {"abbrev": "Havo", "level_req": "true", "sector_req": "true"},
        # "13": {"abbrev": "Vwo", "level_req": "true", "sector_req": "true"}}',

        # 'levels':
        # '{"7": {"name": "Theoretisch Kadergerichte Leerweg", "abbrev": "TKL", "sequence": 1, "depbase_list": ";11;"},
        # "8": {"name": "Praktisch Kadergerichte Leerweg", "abbrev": "PKL", "sequence": 2, "depbase_list": ";11;"},
        # "9": {"name": "Praktisch Basisgerichte Leerweg", "abbrev": "PBL", "sequence": 3, "depbase_list": ";11;"}}',

        # 'sectors':
        # '{"29": {"name": "Economie", "abbrev": "ec", "sequence": 1, "depbase_list": ";11;"},
        # "30": {"name": "Techniek", "abbrev": "tech", "sequence": 2, "depbase_list": ";11;"},
        # "31": {"name": "Zorg & Welzijn", "abbrev": "z&w", "sequence": 3, "depbase_list": ";11;"},
        # "32": {"name": "Cultuur en Maatschappij", "abbrev": "c&m", "sequence": 4, "depbase_list": ""},
        # "33": {"name": "Economie en Maatschappij", "abbrev": "e&m", "sequence": 5, "depbase_list": ";12;13;"},
        # "34": {"name": "Natuur en Gezondheid", "abbrev": "n&g", "sequence": 6, "depbase_list": ";12;13;"},
        # "35": {"name": "Natuur en Techniek", "abbrev": "n&t", "sequence": 7, "depbase_list": ";12;13;"}}'

        # filter Departments of request.user.country
        deps = sch_mod.Department.get_select_list(request.user)
        params.update({'deps': json.dumps(deps)})

        # filter Levels of request.user.country
        levels = subj_mod.Level.get_select_list(request.user)
        params.update({'levels': json.dumps(levels)})

        # filter Sectors of request.user.country
        sectors = subj_mod.Sector.get_select_list(request.user)
        params.update({'sectors': json.dumps(sectors)})

        # logger.debug('SchemeitemListView deps: ' + str(deps) + ' Type: ' + str(type(deps)))
        return  params


@method_decorator([login_required], name='dispatch')
class SchemeitemAddView(CreateView):  # PR2018-08-24

    def get(self, request, *args, **kwargs):
        form = SchemeitemAddForm(request=request)
        _params = self.get_params(request, form)
        return render(request, 'schemeitem_add.html', _params)

    def post(self, request, *args, **kwargs):
        form = SchemeitemAddForm(request.POST, request=request)

        if form.is_valid():
            schemeitem = form.save(commit=False)
            schemeitem.save(request=self.request)
            return redirect('schemeitem_list_url')
        else:
            _params = self.get_params(request, form)
            return render(request, 'schemeitem_add.html', _params)

    def get_params(self, request, form):
        params = awpr_menu.get_headerbar_param(request, {
            'form': form,
        })

        # filter Departments of request.user.country
        deps = sch_mod.Department.get_dep_attr(request.user)
        params.update({'deps': json.dumps(deps)})

        # filter Levels of request.user.country
        levels = subj_mod.Level.get_level_attr(request.user)
        params.update({'levels': json.dumps(levels)})

        # filter Sectors of request.user.country
        sectors = subj_mod.Sector.get_sector_attr(request.user)
        params.update({'sectors': json.dumps(sectors)})

        # logger.debug('SchemeitemAddView params: ' + str(params) + ' Type: ' + str(type(params)))
        return  params

@method_decorator([login_required], name='dispatch')
class SchemeitemEditView(UpdateView):  # PR2018-08-24
    model = subj_mod.Schemeitem
    form_class = SchemeitemEditForm
    template_name = 'schemeitem_edit.html'
    context_object_name = 'schemeitem'

    def get_context_data(self, **kwargs):  # https://docs.djangoproject.com/en/2.1/ref/class-based-views/mixins-simple/
        context = super().get_context_data(**kwargs)

        deps = sch_mod.Department.get_dep_attr(self.request.user)
        context['deps'] = json.dumps(deps)

        levels = subj_mod.Level.get_level_attr(self.request.user)
        context['levels'] = json.dumps(levels)

        sectors = subj_mod.Sector.get_sector_attr(self.request.user)
        context['sectors'] = json.dumps(sectors)

        # context['display_country'] = True
        return context

    def get_form_kwargs(self):
        kwargs = super(SchemeitemEditView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_params(self, request, form):
        params = awpr_menu.get_headerbar_param(request, {
            'form': form,
            'display_country': True
        })
        return  params

    def form_valid(self, form):
        schemeitem = form.save(commit=False)
        # TODO: scheme has field 'department', not 'dep_list' PR2019-01-18
        # ======  save field 'dep_list_field'  ============
        _clean_dep_list_field = form.cleaned_data.get('dep_list_field')  # Type: <class 'list'>
        schemeitem.dep_list = af.get_depbase_list_field_sorted_zerostripped(_clean_dep_list_field)

        schemeitem.save(request=self.request)
        return redirect('schemeitem_list_url')


@method_decorator([login_required], name='dispatch')
class SchemeitemDeleteView(DeleteView):
    model = subj_mod.Schemeitem
    template_name = 'schemeitem_delete.html'  # without template_name Django searches for subjectdefault_confirm_delete.html
    success_url = reverse_lazy('schemeitem_list_url')

    def delete(self, request, *args, **kwargs):
       self.object = self.get_object()

       if self.request.user:
          self.object.delete(request=self.request)
          return HttpResponseRedirect(self.get_success_url())
       else:
          raise Http404 #or return HttpResponse('404_url')


@method_decorator([login_required], name='dispatch')
class SchemeitemLogView(View):
    def get(self, request, pk):
        schemeitem_log = subj_mod.Schemeitem_log.objects.filter(schemeitem_id=pk).order_by('-modified_at')
        schemeitem = subj_mod.Schemeitem.objects.get(id=pk)
        _param = awpr_menu.get_headerbar_param(request,  {'schemeitem_log': schemeitem_log, 'schemeitem': schemeitem})
        return render(request, 'schemeitem_log.html', _param)

@method_decorator([login_required], name='dispatch')
class SchemeitemsDownloadView(View):  # PR2019-01-13
    # PR2019-01-17
    def post(self, request, *args, **kwargs):
        # logger.debug(' ============= SchemeitemsDownloadView ============= ')
        # logger.debug('request.POST' + str(request.POST) )

        # request.POST<QueryDict: {'dep_id': ['11'], 'lvl_id': ['7'], 'sct_id': ['30']}>

        params = {}
        if request.user is not None and request.user.examyear is not None:

        # lookup scheme by dep_id, lvl_id (if required) and sct_id (if required)
            if 'dep_id' in request.POST.keys():
                dep_id_int = int(request.POST['dep_id'])
                examyear = request.user.examyear
                department = sch_mod.Department.objects.filter(id=dep_id_int, examyear=examyear).first()
                if department:
                    dep_abbrev = department.abbrev
                    # logger.debug(dep_abbrev)

                    # lookup level (if required)
                    level = None
                    lvl_abbrev = ''
                    if department.level_req:
                        if 'lvl_id' in request.POST.keys():
                            lvl_id_int = int(request.POST['lvl_id'])
                            level = subj_mod.Level.objects.filter(id=lvl_id_int, examyear=examyear).first()
                            # if level:
                                # lvl_abbrev = level.abbrev
                    # logger.debug(lvl_abbrev)

                    # lookup sector (if required)
                    sector = None
                    sct_name = ''
                    if department.sector_req:
                        if 'sct_id' in request.POST.keys():
                            sct_id_int = int(request.POST['sct_id'])
                            sector = subj_mod.Sector.objects.filter(id=sct_id_int, examyear=examyear).first()
                            #if sector:
                                #sct_name = sector.name
                    # logger.debug(sct_name)

                    # lookup scheme by dep_id, lvl_id (if required) and sct_id (if required)
                    scheme = None
                    if level:
                        if sector:
                            logger.debug('filter by department, level and sector')
                            # filter by department, level and sector
                            # if selection contains multiple schemes: skip
                            if subj_mod.Scheme.objects.filter(
                                department=department, level=level, sector=sector
                            ).count() == 1:
                                scheme = subj_mod.Scheme.objects.filter(
                                    department=department, level=level, sector=sector
                                ).first()
                        else:
                            logger.debug('filter by department and level')
                            # filter by department and level
                            # if selection contains multiple schemes: skip
                            if subj_mod.Scheme.objects.filter(
                                    department=department, level=level
                            ).count() == 1:
                                scheme = subj_mod.Scheme.objects.filter(
                                    department=department, level=level
                                ).first()
                    else:
                        if sector:
                            # logger.debug('filter by department and sector')
                            # filter by department and sector
                            # if selection contains multiple schemes: skip

                            logger.debug('count: ' + str(subj_mod.Scheme.objects.filter(department=department, sector=sector).count()))
                            if subj_mod.Scheme.objects.filter(department=department, sector=sector).count() == 1:
                                scheme = subj_mod.Scheme.objects.filter(department=department, sector=sector).first()
                        else:
                            # logger.debug('only by department')
                            # filter only by department
                            # if selection contains multiple schemes: skip
                            if subj_mod.Scheme.objects.filter(department=department).count() == 1:
                                scheme = subj_mod.Scheme.objects.filter(department=department).first()

                    if scheme:
                        scheme_list_str = scheme.get_scheme_list_str()
                        params.update({'scheme': scheme_list_str})

                        # make list of all Subjects from this department and examyear (included in dep)
                        schemeitems = subj_mod.Schemeitem.get_schemeitem_list(scheme)
                        params.update({'schemeitems': schemeitems})

                        # make list of all Subjects from this department and examyear (included in dep)
                        subjects = subj_mod.Subject.get_subj_list(department)
                        params.update({'subjects': subjects})

                        # make list of all Subjecttypes from this department and examyear (included in dep)
                        subjecttypes = subj_mod.Subjecttype.get_subjtype_list( department)  # PR2019-01-18
                        params.update({'subjecttypes': subjecttypes})

                        # make list of all gradetypes

                        # GRADETYPE_CHOICES = ((0, 'None'), (1, 'Number'), (2, 'Good/Sufficient/Insufficient'))
                        gradetypes = []
                        for item in c.GRADETYPE_CHOICES:
                            if item[0] > 0:
                                gradetypes.append({
                                    'grtp_id': item[0],
                                    'name': item[1]
                                })
                        params.update({'gradetypes': gradetypes})

        #logger.debug('params')
        # logger.debug(params)
        return HttpResponse(json.dumps(params))


@method_decorator([login_required], name='dispatch')
class SchemeitemUploadView(View):  # PR2019-01-24

    def post(self, request, *args, **kwargs):
        logger.debug(' ============= SchemeitemUploadView ============= ')

        # create mode: ssi =  {'mode': 'c', 'scheme_id': '168', 'subj_id': '314', 'wtse': '2', 'wtce': '1',
        #                       'mand': '1', 'comb': '1', 'chal': '0', 'prac': '0', 'sequ': 60}

        #  update mode: ssi = {'mode': 'u', 'ssi_id': '380', 'scheme_id': '168', 'scm_id': '168', 'subj_id': '314',
        #                       'wtse': '2', 'wtce': '0', 'mand': '1', 'comb': '1', 'chal': '0', 'prac': '0',
        #                       'name': 'Duitse taal', 'sequ': '60'}

        #  delete mode: ssi = {"mod":"d", "ssi_id":"393"}

        params = {}
        if request.user is not None and request.user.examyear is not None:
            # get sybject scheme item from  request.POST
            ssi = json.loads(request.POST['ssi'])
            logger.debug("ssi: " + str(ssi))

            # convert values
            # ssi_id only necessary when items are updated
            mode = ssi.get('mode', '')
            ssi_id = int(ssi.get('ssi_id', '0'))
            scheme_id = int(ssi.get('scheme_id', '0')) # scheme_id has always value (retrieved form scheme)
            scm_id = int(ssi.get('scm_id', '0'))  # scm_id = '' scheme_id is retrieved form schemeitem
            subj_id = int(ssi.get('subj_id', '0'))
            sjtp_id = int(ssi.get('sjtp_id', '0'))

            # check if scheme_id and scm_id are the same and ssi_id not None (only at update and remove)
            scm_id_ok = False
            record_saved = False
            if scheme_id:
                if mode == 'c':
                    scm_id_ok = True
                elif ssi_id and scm_id == scheme_id:
                    scm_id_ok = True
            logger.debug("scm_id_ok: " + str(scm_id_ok))

            if scm_id_ok:
                # check if scheme exists
                scheme = subj_mod.Scheme.objects.filter(id=scheme_id).first()
                if scheme:
                    if mode == 'd':
                        # lookup schemeitem
                        schemeitem = subj_mod.Schemeitem.objects.filter(id=ssi_id).first()
                        if schemeitem:
                            schemeitem.delete(request=self.request)
                            record_saved = True
                    else:
                        # check if subject and subjecttype exist
                        subject = subj_mod.Subject.objects.filter(id=subj_id, examyear=request.user.examyear).first()
                        subjecttype = subj_mod.Subjecttype.objects.filter(id=sjtp_id, examyear=request.user.examyear).first()

                        logger.debug('scheme: <' + str(scheme) + '> type: ' + str(type(scheme)))
                        logger.debug('subject: <' + str(subject) + '> type: ' + str(type(subject)))
                        logger.debug('subjecttype: <' + str(subjecttype) + '> type: ' + str(type(subjecttype)))

                        if subject and subjecttype:
                            logger.debug("scheme and subject and subjecttype")
                            if mode == 'c':
                                # create new schemeitem
                                schemeitem = subj_mod.Schemeitem(
                                    scheme=scheme,
                                    subject=subject,
                                    subjecttype=subjecttype
                                )
                            else:
                                # lookup schemeitem
                                schemeitem = subj_mod.Schemeitem.objects.filter(id=ssi_id).first()

                            if schemeitem:
                                # update mode or create mode
                                schemeitem.subjecttype = subjecttype

                                # ------------ import values from ssi  -----------------------------------
                                schemeitem.gradetype = int(ssi.get('grtp_id', '0'))
                                schemeitem.weightSE = int(ssi.get('wtse', '0'))
                                schemeitem.weightCE = int(ssi.get('wtce', '0'))
                                schemeitem.is_mandatory = (ssi.get('mand', '0') == '1')
                                schemeitem.is_combi = (ssi.get('comb', '0') == '1')
                                schemeitem.choicecombi_allowed = (ssi.get('chal', '0') == '1')
                                schemeitem.has_practexam = (ssi.get('prac', '0') == '1')

                                schemeitem.save(request=self.request)

                                record_saved = True

            # renew list of all Subjects from this department and examyear (included in dep)
            schemeitems = subj_mod.Schemeitem.get_schemeitem_list(scheme)
            params.update({'schemeitems': schemeitems})

            if not record_saved:
                if mode == 'c':
                    err_code = 'err_msg02'
                elif mode == 'd':
                    err_code = 'err_msg04'
                else:
                    err_code = 'err_msg03'
                params.update({'err_code': err_code})

        logger.debug("params: " + str(params))

        # PR2019-02-04 was: return HttpResponse(json.dumps(params))

        # return HttpResponse(json.dumps(params, cls=LazyEncoder), mimetype='application/javascript')

        return HttpResponse(json.dumps(params, cls=af.LazyEncoder))


# ========  SubjectListView  ======= # PR2020-09-29
@method_decorator([login_required], name='dispatch')
class SubjectListView(View):

    def get(self, request):
        #logger.debug(" =====  SubjectListView  =====")
# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

        requsr_examyear = sch_mod.Examyear.objects.get_or_none(country_id=request.user.country_id, pk=request.user.examyear_id)
        requsr_examyear_text = str(_('Examyear')) + ' ' + str(requsr_examyear) if requsr_examyear else _('<No examyear selected>')

        requsr_school = sch_mod.School.objects.get_or_none( examyear=request.user.examyear, base=request.user.schoolbase)
        requsr_school_text = requsr_school.base.code + ' ' + requsr_school.name if requsr_school else _('<No school selected>')

        # set headerbar parameters PR2018-08-06
        params = awpr_menu.get_headerbar_param(request, {
            'menu_key': 'subjects',
            'examyear': requsr_examyear_text,
            'school': requsr_school_text
        })

        return render(request, 'subjects.html', params)


def create_subject_rows(setting_dict, append_dict, subject_pk):
    # --- create rows of all subjects of this examyear  PR2020-09-29 PR2020-10-30
    #logger.debug(' =============== create_subject_rows ============= ')
    subject_rows = []
    examyear_pk = setting_dict.get('requsr_examyear_pk')
    if examyear_pk:
        sql_keys = {'ey_id': examyear_pk}
        sql_list = ["""SELECT sj.id, sj.base_id, sj.examyear_id,
            CONCAT('subject_', sj.id::TEXT) AS mapid,
            sj.name, sj.abbrev, sj.sequence, sj.depbases,
            sj.modifiedby_id, sj.modifiedat,
            ey.examyear AS examyear,
            SUBSTRING(au.username, 7) AS modby_username
    
            FROM subjects_subject AS sj 
            INNER JOIN schools_examyear AS ey ON (ey.id = sj.examyear_id) 
            LEFT JOIN accounts_user AS au ON (au.id = sj.modifiedby_id) 
            
            WHERE sj.examyear_id = %(ey_id)s::INT
            """]

        if subject_pk:
            # when employee_pk has value: skip other filters
            sql_list.append('AND sj.id = %(sj_id)s::INT')
            sql_keys['sj_id'] = subject_pk
        else:
            sql_list.append('ORDER BY sj.sequence')

        sql = ' '.join(sql_list)

        newcursor = connection.cursor()
        newcursor.execute(sql, sql_keys)
        subject_rows = sch_mod.dictfetchall(newcursor)

        # - add messages to subject_row
        if subject_pk and subject_rows:
            # when subject_pk has value there is only 1 row
            row = subject_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    return subject_rows
# --- end of create_subject_rows


@method_decorator([login_required], name='dispatch')
class SubjectUploadView(View):  # PR2020-10-01

    def post(self, request, *args, **kwargs):
        logger.debug(' ============= SubjectUploadView ============= ')

        update_wrap = {}
        has_permit = False
        if request.user is not None and request.user.country is not None and request.user.schoolbase is not None:
            has_permit = True # (request.user.is_perm_planner or request.user.is_perm_hrman)
        if has_permit:

# - Reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                logger.debug('upload_dict' + str(upload_dict))

# - get id  variables
                subject_pk = af.get_dict_value(upload_dict, ('id', 'pk'))
                examyear_pk = af.get_dict_value(upload_dict, ('id', 'ppk'))
                mode = af.get_dict_value(upload_dict, ('id', 'mode'))

                append_dict = {'mode': mode, 'table': 'subject'}
                error_dict = {}
                subject_rows = []
# A. check if examyear exists  (examyear is parent of subject)
                examyear = sch_mod.Examyear.objects.get_or_none(id=examyear_pk, country=request.user.country)
                logger.debug('examyear: ' + str(examyear))
                if examyear and examyear == request.user.examyear:
# C. Delete subject
                    # upload_dict = {'id': {'pk': 164, 'ppk': 37, 'table': 'subject', 'mode': 'delete', 'mapid': 'subject_164'}}
                    if mode == 'delete':
                        subject = sbj_mod.Subject.objects.get_or_none(id=subject_pk, examyear=examyear)
                        logger.debug('subject: ' + str(subject))
                        if subject:
                            this_text = _("Subject '%(tbl)s'") % {'tbl': subject.name}
                    # a. check if employee has emplhours, put msg_err in update_dict when error
                            examyear_is_locked, examyear_has_activated_schools = av.validate_locked_activated_examyear(examyear)
                            msg_err = None #validate_employee_has_emplhours(employee)
                            if examyear_is_locked:
                                append_dict['err_delete'] = str(_('Exam year %(exyr)s is closed.') % {'exyr': examyear.examyear} +
                                                                '\n' + _('%(item)s cannot be deleted.') % {'item': this_text})
                            elif examyear_has_activated_schools:
                                append_dict['err_delete'] = str(_('There are schools that have activated exam year %(exyr)s.') % {'exyr': examyear.examyear} +
                                                                '\n' + _('%(item)s cannot be deleted.') % {'item': this_text})
                            else:
                    # b. check if there are teammembers with this employee: absence teammembers, remove employee from shift teammembers
                                # delete_employee_from_teammember(employee, request)
                    # c. delete subject
                                deleted_ok = sch_mod.delete_instance(subject, append_dict, request, this_text)
                                logger.debug('deleted_ok' + str(deleted_ok))
                                if deleted_ok:
                     # - add deleted_row to absence_rows
                                    subject_rows.append({'pk': subject_pk,
                                                         'mapid': 'subject_' + str(subject_pk),
                                                         'deleted': True})
                                    subject = None
                                logger.debug('subject_rows' + str(subject_rows))
                    else:
# D. Create new subject
                        # upload_dict = {'id': {'table': 'subject', 'ppk': 37, 'mode': 'create'},
                        #               'abbrev': {'value': 'ab', 'update': True},
                        #               'sequence': {'value': 15, 'update': True},
                        #               'name': {'value': 'ab', 'update': True},
                        #                depbases': {'value': [], 'update': True}}
                        if mode == 'create':
                            subject, msg_err = create_subject(examyear, upload_dict, request)
                            if subject:
                                append_dict['created'] = True
                            elif msg_err:
                                append_dict['err_create'] = msg_err

                            logger.debug('append_dict' + str(append_dict))
# E. Get existing subject
                        else:
                            subject = sbj_mod.Subject.objects.get_or_none(id=subject_pk, examyear=examyear)

# F. Update subject, also when it is created.
                        #  Not necessary. Most fields are required. All fields are saved in create_subject
                        #if subject:
                            update_subject(subject, examyear, upload_dict, error_dict, request)

# I. add update_dict to update_wrap
                    logger.debug('subject' + str(subject))
                    logger.debug('subject_rows' + str(subject_rows))
                    if subject:
                        if error_dict:
                            append_dict['error'] = error_dict

                        logger.debug('subject' + str(subject))

                        subject_rows = create_subject_rows(
                            examyear=examyear,
                            append_dict=append_dict,
                            subject_pk=subject.pk
                        )
                    logger.debug('subject_rows' + str(subject_rows))

                    if subject_rows:
                        update_wrap['updated_subject_rows'] = subject_rows

        logger.debug('update_wrap' + str(update_wrap))


# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))


@method_decorator([login_required], name='dispatch')
class SubjectImportView(View):  # PR2020-10-01

    def get(self, request):
        param = {}
        has_permit = False
        if request.user is not None and request.user.country is not None and request.user.schoolbase is not None:
            has_permit = True # (request.user.is_perm_planner or request.user.is_perm_hrman)
        if has_permit:
            # coldef_list = [{'tsaKey': 'employee', 'caption': _('Company name')},
            #                      {'tsaKey': 'ordername', 'caption': _('Order name')},
            #                      {'tsaKey': 'orderdatefirst', 'caption': _('First date order')},
            #                      {'tsaKey': 'orderdatelast', 'caption': _('Last date order')} ]

    # get coldef_list  and caption
            coldef_list = c.COLDEF_SUBJECT
            captions_dict = c.CAPTION_IMPORT

            # get mapped coldefs from table Companysetting
            # get stored setting from Companysetting
            settings_json = sch_mod.Schoolsetting.get_jsonsetting(c.KEY_SUBJECT_MAPPED_COLDEFS, request.user.schoolbase)
            stored_setting = json.loads(settings_json) if settings_json else {}

            # don't replace keyvalue when new_setting[key] = ''
            self.has_header = True
            self.worksheetname = ''
            self.codecalc = 'linked'
            if 'has_header' in stored_setting:
                self.has_header = False if Lower(stored_setting['has_header']) == 'false' else True
            if 'worksheetname' in stored_setting:
                self.worksheetname = stored_setting['worksheetname']
            if 'codecalc' in stored_setting:
                self.codecalc = stored_setting['codecalc']

            if 'coldefs' in stored_setting:
                stored_coldefs = stored_setting['coldefs']
                # skip if stored_coldefs does not exist
                if stored_coldefs:
                    # loop through coldef_list
                    for coldef in coldef_list:
                        # coldef = {'tsaKey': 'employee', 'caption': 'Cliënt'}
                        # get fieldname from coldef
                        fieldname = coldef.get('tsaKey')
                        #logger.debug('fieldname: ' + str(fieldname))

                        if fieldname:  # fieldname should always be present
                            # check if fieldname exists in stored_coldefs
                            if fieldname in stored_coldefs:
                                # if so, add Excel name with key 'excKey' to coldef
                                coldef['excKey'] = stored_coldefs[fieldname]
                                #logger.debug('stored_coldefs[fieldname]: ' + str(stored_coldefs[fieldname]))

            coldefs_dict = {
                'worksheetname': self.worksheetname,
                'has_header': self.has_header,
                'codecalc': self.codecalc,
                'coldefs': coldef_list
            }
            coldefs_json = json.dumps(coldefs_dict, cls=LazyEncoder)

            captions = json.dumps(captions_dict, cls=LazyEncoder)

            param = awpr_menu.get_headerbar_param(request, {'captions': captions, 'setting': coldefs_json})

        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'subjectimport.html', param)


@method_decorator([login_required], name='dispatch')
class SubjectImportUploadSetting(View):   # PR2019-03-10
    # function updates mapped fields, no_header and worksheetname in table Companysetting
    def post(self, request, *args, **kwargs):
        #logger.debug(' ============= SubjectImportUploadSetting ============= ')
        #logger.debug('request.POST' + str(request.POST) )
        schoolsetting_dict = {}
        has_permit = False
        if request.user is not None and request.user.examyear is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_perm_adm_or_sys_)
        if has_permit:
            if request.POST['upload']:
                new_setting_json = request.POST['upload']
                # new_setting is in json format, no need for json.loads and json.dumps
                #logger.debug('new_setting_json' + str(new_setting_json))

                new_setting_dict = json.loads(request.POST['upload'])
                settings_key = c.KEY_SUBJECT_MAPPED_COLDEFS

                new_worksheetname = ''
                new_has_header = True
                new_code_calc = ''
                new_coldefs = {}
                stored_json = sch_mod.Schoolsetting.get_jsonsetting(settings_key, request.user.schoolbase)
                if stored_json:
                    stored_setting = json.loads(stored_json)
                    #logger.debug('stored_setting: ' + str(stored_setting))
                    if stored_setting:
                        new_has_header = stored_setting.get('has_header', True)
                        new_worksheetname = stored_setting.get('worksheetname', '')
                        new_code_calc = stored_setting.get('codecalc', '')
                        new_coldefs = stored_setting.get('coldefs', {})

                if new_setting_json:
                    new_setting = json.loads(new_setting_json)
                    #logger.debug('new_setting' + str(new_setting))
                    if new_setting:
                        if 'worksheetname' in new_setting:
                            new_worksheetname = new_setting.get('worksheetname', '')
                        if 'has_header' in new_setting:
                            new_has_header = new_setting.get('has_header', True)
                        if 'coldefs' in new_setting:
                            new_coldefs = new_setting.get('coldefs', {})
                    #logger.debug('new_code_calc' + str(new_code_calc))
                new_setting = {'worksheetname': new_worksheetname,
                               'has_header': new_has_header,
                               'codecalc': new_code_calc,
                               'coldefs': new_coldefs}
                new_setting_json = json.dumps(new_setting)
                #logger.debug('new_setting' + str(new_setting))
                #logger.debug('---  set_jsonsettingg  ------- ')
                #logger.debug('new_setting_json' + str(new_setting_json))
                #logger.debug(new_setting_json)
                sch_mod.Schoolsetting.set_jsonsetting(settings_key, new_setting_json, request.user.schoolbase)

    # only for testing
                # ----- get user_lang
                #user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                #tblName = 'employee'
                #coldefs_dict = compdicts.get_stored_coldefs_dict(tblName, user_lang, request)
                #if coldefs_dict:
                #    schoolsetting_dict['coldefs'] = coldefs_dict
                #logger.debug('new_setting from saved ' + str(coldefs_dict))

                #m.Companysetting.set_setting(c.settings_key, new_setting_json, request.user.schoolbase)

        return HttpResponse(json.dumps(schoolsetting_dict, cls=LazyEncoder))
# --- end of SubjectImportUploadSetting

@method_decorator([login_required], name='dispatch')
class SubjectImportUploadData(View):  # PR2018-12-04 PR2019-08-05 PR2020-06-04

    def post(self, request):
        logger.debug(' ========================== SubjectImportUploadData ========================== ')
        params = {}
        has_permit = False
        is_not_locked = False
        if request.user is not None and request.user.examyear is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_perm_adm_or_sys_)
            is_not_locked = not request.user.examyear.locked

        if is_not_locked and has_permit:
            # - Reset language
            # PR2019-03-15 Debug: language gets lost, get request.user.lang again
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                params = import_subjects(upload_dict, user_lang, request)

        return HttpResponse(json.dumps(params, cls=LazyEncoder))

# --- end of SubjectImportUploadData

def import_subjects(upload_dict, user_lang, request):

    logger.debug(' -----  import_subjects ----- ')
    logger.debug('upload_dict: ' + str(upload_dict))
# - get is_test, codecalc, dateformat, awpKey_list
    is_test = upload_dict.get('test', False)
    awpKey_list = upload_dict.get('awpKey_list')
    dateformat = upload_dict.get('dateformat', '')

    params = {}
    if awpKey_list:
# - get lookup_field
        # lookup_field is field that determines if employee alreay exist.
        # check if one of the fields 'payrollcode', 'identifier' or 'code' exists
        # first in the list is lookup_field
        lookup_field = 'code'

# - get upload_dict from request.POST
        subject_list = upload_dict.get('subjects')
        if subject_list:

            today_dte = af.get_today_dateobj()
            today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
            double_line_str = '=' * 80
            indent_str = ' ' * 5
            space_str = ' ' * 30
            logfile = []
            logfile.append(double_line_str)
            logfile.append( '  ' + str(request.user.schoolbase.code) + '  -  ' +
                            str(_('Import subjects')) + ' ' + str(_('date')) + ': ' + str(today_formatted))
            logfile.append(double_line_str)

            if lookup_field is None:
                info_txt = str(_('There is no field given to lookup subjects. Subjects cannot be uploaded.'))
                logfile.append(indent_str + info_txt)
            else:
                if is_test:
                    info_txt = str(_("This is a test. The subject data are not saved."))
                else:
                    info_txt = str(_("The subject data are saved."))
                logfile.append(indent_str + info_txt)
                lookup_caption = str(get_field_caption('subject', lookup_field))
                info_txt = str(_("Subjects are looked up by the field: '%(fld)s'.") % {'fld': lookup_caption})
                logfile.append(indent_str + info_txt)
                #if dateformat:
                #    info_txt = str(_("The date format is: '%(fld)s'.") % {'fld': dateformat})
                #    logfile.append(indent_str + info_txt)
                update_list = []
                for subject_dict in subject_list:
                    # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html

                    update_dict = upload_subject(subject_list, subject_dict, lookup_field,
                                                 awpKey_list, is_test, dateformat, indent_str, space_str, logfile, request)
                    # json_dumps_err_list = json.dumps(msg_list, cls=f.LazyEncoder)
                    if update_dict:  # 'Any' returns True if any element of the iterable is true.
                        update_list.append(update_dict)

                if update_list:  # 'Any' returns True if any element of the iterable is true.
                    params['subject_list'] = update_list
            if logfile:  # 'Any' returns True if any element of the iterable is true.
                params['logfile'] = logfile
                        # params.append(new_employee)
    return params


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def upload_subject(subject_list, subject_dict, lookup_field, awpKey_list,
                   is_test, dateformat, indent_str, space_str, logfile, request):  # PR2019-12-17 PR2020-10-21
    logger.debug('----------------- import subject  --------------------')
    logger.debug(str(subject_dict))
    # awpKeys are: 'code', 'name', 'sequence', 'depbases'

# - get index and lookup info from subject_dict
    row_index = subject_dict.get('rowindex', -1)
    new_code = subject_dict.get('code')
    new_name = subject_dict.get('name')
    new_sequence = subject_dict.get('sequence')
    new_depbases = subject_dict.get('depbases')

# - create update_dict
    update_dict = {'id': {'table': 'subject', 'rowindex': row_index}}

# - give row_error when lookup went wrong
    # multiple_found and value_too_long return the lookup_value of the error field

    lookup_field_caption = str(get_field_caption('subject', lookup_field))
    lookup_field_capitalized = '-'
    if lookup_field_caption:
        lookup_field_capitalized = lookup_field_caption.capitalize()
    is_skipped_str = str(_("is skipped."))
    skipped_str = str(_("Skipped."))
    logfile.append(indent_str)
    msg_err = None
    log_str = ''

    subjectbase = None
    subject = None

# check if lookup_value has value ( lookup_field = 'code')
    lookup_value = subject_dict.get(lookup_field)
    if not lookup_value:
        log_str = str(_("No value for lookup field: '%(fld)s'.") % {'fld': lookup_field_caption})
        msg_err = ' '.join((skipped_str, log_str))

# check if lookup_value is not too long
    elif len(lookup_value) > c.MAX_LENGTH_SUBJECTCODE:
        value_too_long_str = str(_("Value '%(fld)s' is too long.") % {'fld': lookup_value})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_SUBJECTCODE})
        log_str = value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))

# check if new_name has value
    elif new_name is None:
        field_caption = str(get_field_caption('subject', 'name'))
        log_str = str(_("No value for required field: '%(fld)s'.") % {'fld': field_caption})
        msg_err = ' '.join((skipped_str, log_str))

# check if subject name  is not too long
    elif len(new_name) > c.MAX_LENGTH_NAME:
        value_too_long_str = str(_("Value '%(fld)s' is too long.") % {'fld': lookup_value})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_NAME})
        log_str = value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))
    else:

# - check if lookup_value occurs mutiple times in Excel file
        excel_list_multiple_found = False
        excel_list_count = 0
        for dict in subject_list:
            value = dict.get(lookup_field)
            if value and value == lookup_value:
                excel_list_count += 1
            if excel_list_count > 1:
                excel_list_multiple_found = True
                break
        if excel_list_multiple_found:
            log_str = str(_("%(fld)s '%(val)s' is not unique in Excel file.") % {'fld': lookup_field_capitalized, 'val': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

    if msg_err is None:

# - check if subjectbase with this code exists in request.user.country. subjectbase has value when only one found
        # lookup_value = subject_dict.get(lookup_field)
        subjectbase, multiple_found = lookup_subjectbase(lookup_value, request)
        if multiple_found:
            log_str = str(_("Value '%(fld)s' is found multiple times.") % {'fld': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

# - check if subject with this subjectbase exists in request.user.examyear. subject has value when only one found
        multiple_subjects_found = False
        if subjectbase:
            subject, multiple_subjects_found = lookup_subject(subjectbase, request)
        if multiple_subjects_found:
            log_str = str(_("Value '%(fld)s' is found multiple times in this exam year.") % {'fld': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

    code_text = (new_code + space_str)[:30]

# - if error: put msg_err in update_dict and logfile
    if msg_err:
        update_dict['row_error'] = msg_err
        update_dict[lookup_field] = {'error': msg_err}
        logfile.append(code_text + is_skipped_str)
        logfile.append(' ' * 30 + log_str)
    else:

# - create new subjectbase when subjectbase not found in database
        if subjectbase is None:
            try:
                subjectbase = subj_mod.Subjectbase(
                    country=request.user.country,
                    code=new_code
                )
                if subjectbase:
                    subjectbase.save()
            except:
# - give error msg when creating subjectbase failed
                error_str = str(_("An error occurred. The subject is not added."))
                logfile.append(" ".join((code_text, error_str )))
                update_dict['row_error'] = error_str

        if subjectbase :

# - create new subject when subject not found in database
            is_existing_subject = False
            save_instance = False

            if subject is None:
                try:
                    subject = subj_mod.Subject(
                        base=subjectbase,
                        examyear=request.user.examyear,
                        name=new_name
                    )
                    if subject:
                        subject.save(request=request)
                        update_dict['id']['created'] = True
                        logfile.append(code_text + str(_('is added.')))
                except:
    # - give error msg when creating subject failed
                    error_str = str(_("An error occurred. The subject is not added."))
                    logfile.append(" ".join((code_text, error_str )))
                    update_dict['row_error'] = error_str
            else:
                is_existing_subject = True
                logfile.append(code_text + str(_('already exists.')))

            if subject:
                # add 'id' at the end, after saving the subject. Pk doent have value until instance is saved
                #update_dict['id']['pk'] = subject.pk
                #update_dict['id']['ppk'] = subject.company.pk
                #if subject:
                #    update_dict['id']['created'] = True

                # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
                # solved bij wrapping with str()

                blank_str = '<' + str(_('blank')) + '>'
                was_str = str(_('was') + ': ')
                # FIELDS_SUBJECT = ('base', 'examyear', 'name', 'abbrev', 'sequence', 'depbases', 'modifiedby', 'modifiedat')
                for field in ('name', 'abbrev', 'sequence', 'depbases'):
                    # --- get field_dict from  upload_dict  if it exists
                    if field in awpKey_list:
                        #('field: ' + str(field))
                        field_dict = {}
                        field_caption = str(get_field_caption('subject', field))
                        caption_txt = (indent_str + field_caption + space_str)[:30]

                        if field in ('code', 'name', 'namefirst', 'email', 'address', 'city', 'country'):
                            if field == 'code':
                                # new_code is created in this function and already checked for max_len
                                new_value = new_code
                            else:
                                new_value = subject_dict.get(field)
                # check length of new_value
                            max_len = c.MAX_LENGTH_NAME \
                                if field in ('namelast', 'namefirst', 'email', 'address', 'city', 'country') \
                                else c.MAX_LENGTH_CODE

                            if max_len and new_value and len(new_value) > max_len:
                                msg_err = str(_("'%(val)s' is too long. Maximum is %(max)s characters'.") % {
                                    'val': new_value, 'max': max_len})
                                field_dict['error'] = msg_err
                            else:
                    # - replace '' by None
                                if not new_value:
                                    new_value = None
                                field_dict['value'] = new_value
                                if not is_existing_subject:
                                    logfile.append(caption_txt + (new_value or blank_str))
                    # - get saved_value
                                saved_value = getattr(subject, field)
                                if new_value != saved_value:
                    # put new value in subject instance
                                    setattr(subject, field, new_value)
                                    field_dict['updated'] = True
                                    save_instance = True
                    # create field_dict and log
                                    if is_existing_subject:
                                        old_value_str = was_str + (saved_value or blank_str)
                                        field_dict['info'] = field_caption + ' ' + old_value_str
                                        update_str = ((new_value or blank_str) + space_str)[:25] + old_value_str
                                        logfile.append(caption_txt + update_str)

                # add field_dict to update_dict
                        update_dict[field] = field_dict

               # dont save data when it is a test run
                if not is_test and save_instance:
                    employee.save(request=request)
                    update_dict['id']['pk'] = employee.pk
                    update_dict['id']['ppk'] = employee.company.pk
                    # wagerate wagecode
                    # priceratejson additionjson
                    try:
                        employee.save(request=request)
                        update_dict['id']['pk'] = employee.pk
                        update_dict['id']['ppk'] = employee.company.pk
                    except:
        # - give error msg when creating employee failed
                        error_str = str(_("An error occurred. The subject data is not saved."))
                        logfile.append(" ".join((code_text, error_str)))
                        update_dict['row_error'] = error_str

    return update_dict
# --- end of upload_subject





# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def lookup_subjectbase(lookup_value, request):  # PR2020-10-20
    logger.debug('----------- lookup_subjectbase ----------- ')
    # function searches for existing subjectbase
    logger.debug('lookup_value: ' + str(lookup_value) + ' ' + str(type(lookup_value)))

    subjectbase = None
    multiple_found = False

# check if 'code' exists multiple times in Subjectbase
    row_count = subj_mod.Subjectbase.objects.filter(code__iexact=lookup_value, country=request.user.country).count()
    if row_count > 1:
        multiple_found = True
    elif row_count == 1:
# get subjectbase when only one found
        subjectbase = subj_mod.Subject.objects.get_or_none(code__iexact=lookup_value, examyear=request.user.examyear)
    # TODO skip for now, remove this line
    multiple_found = False
    return subjectbase, multiple_found


def lookup_subject(subjectbase, request):  # PR2019-12-17 PR2020-10-20
    #logger.debug('----------- lookup_subject ----------- ')

    subject = None
    multiple_subjects_found = False

# - search subject by subjectbase and request.user.examyear
    if subjectbase:
        # check if subject exists multiple times
        row_count = subj_mod.Subject.objects.filter(base=subjectbase, examyear=request.user.examyear).count()
        if row_count > 1:
            multiple_subjects_found = True
        elif row_count == 1:
            # get subject when only one found
            subject = subj_mod.Subject.objects.get_or_none(base=subjectbase, examyear=request.user.examyear)

    return subject, multiple_subjects_found



def get_field_caption(table, field):
    caption = ''
    if table == 'subject':
        if field == 'code':
            caption = _('Abbreviation')
        elif field == 'name':
            caption = _('Subject name')
        elif field == 'sequence':
            caption = _('Sequence')
        elif field == 'depbases':
            caption = _('Departments')
    return caption



# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_subject(examyear, upload_dict, request):
    # --- create subject # PR2019-07-30 PR2020-10-11
    logger.debug(' ----- create_subject ----- ')

    subject = None
    msg_err = None

    logger.debug('examyear: ' + str(examyear))
    if examyear:

# - get value of 'abbrev'
        abbrev = af.get_dict_value(upload_dict, ('abbrev', 'value'))
        name = af.get_dict_value(upload_dict, ('name', 'value'))
        sequence = af.get_dict_value(upload_dict, ('sequence', 'value'))
        depbases = af.get_dict_value(upload_dict, ('depbases', 'value'))
        logger.debug('abbrev: ' + str(abbrev))
        logger.debug('name: ' + str(name))
        logger.debug('sequence: ' + str(sequence))
        logger.debug('depbases: ' + str(depbases) + str(type(depbases)))
        if abbrev and name and sequence:
# - validate abbrev checks null, max len and exists
            """
            msg_err = validate_code_name_identifier(
                table='subject',
                field='code',
                new_value=code,
                is_absence=False,
                parent=parent,
                update_dict={},
                msg_dict={},
                request=request,
                this_pk=None)
            """
            msg_err = None
# - create and save subject
            if not msg_err:

               # try:
                    # First create base record. base.id is used in Subject. Create also saves new record
                base = sbj_mod.Subjectbase.objects.create(
                    country=examyear.country,
                    code =abbrev
                )
                logger.debug('base: ' + str(base))

                subject = sbj_mod.Subject(
                    base=base,
                    examyear=examyear,
                    name=name,
                    abbrev=abbrev,
                    sequence=sequence,
                    depbases=depbases
                )
                subject.save(request=request)
                logger.debug('subject: ' + str(subject))
                #except:
                #    msg_err = str(_("An error occurred. Subject '%(val)s' could not be added.") % {'val': name})

    logger.debug('subject: ' + str(subject))
    logger.debug('msg_err: ' + str(msg_err))
    return subject, msg_err


#######################################################
def update_subject(instance, parent, upload_dict, msg_dict, request):
    # --- update existing and new instance PR2019-06-06
    # add new values to update_dict (don't reset update_dict, it has values)
    #logger.debug(' ------- update_subject -------')
    #logger.debug('upload_dict' + str(upload_dict))

    if instance:
        # FIELDS_SUBJECT = ('base', 'examyear', 'name', 'abbrev','sequence', 'depbases', 'modifiedby', 'modifiedat')
        save_changes = False
        for field in c.FIELDS_SUBJECT:

# --- get field_dict from  upload_dict  if it exists
            field_dict = upload_dict[field] if field in upload_dict else {}
            if field_dict:
                if 'update' in field_dict:
# a. get new_value and saved_value
                    new_value = field_dict.get('value')
                    saved_value = getattr(instance, field)

# 2. save changes in field 'name', 'abbrev'
                    if field in ['name', 'abbrev']:
                        if new_value != saved_value:
            # validate_code_name_id checks for null, too long and exists. Puts msg_err in update_dict
                            """
                            msg_err = validate_code_name_identifier(
                                table='subject',
                                field=field,
                                new_value=new_value, parent=parent,
                                is_absence=False,
                                update_dict={},
                                msg_dict={},
                                request=request,
                                this_pk=instance.pk)
                            """
                            msg_err = None
                            if not msg_err:
                                # c. save field if changed and no_error
                                setattr(instance, field, new_value)
                                save_changes = True
                            else:
                                msg_dict['err_' + field] = msg_err

    # 3. save changes in fields 'namefirst', 'namelast'
                    elif field in ['namefirst', 'namelast']:
                        if new_value != saved_value:
                            name_first = None
                            name_last = None
                            if field == 'namefirst':
                                name_first = new_value
                                name_last = getattr(instance, 'namelast')
                            elif field == 'namelast':
                                name_first = getattr(instance, 'namefirst')
                                name_last = new_value
                            # check if subject namefirst / namelast combination already exists
                            """
                            has_error = validate_namelast_namefirst(
                                namelast=name_last,
                                namefirst=name_first,
                                company=request.user.company,
                                update_field=field,
                                msg_dict=msg_dict,
                                this_pk=instance.pk)
                            """
                            has_error = False
                            if not has_error:
                                setattr(instance, field, new_value)
                                save_changes = True

# 3. save changes in depbases
                    elif field == 'depbases':
                        # save new value when it has different length
                        len_new = len(new_value) if new_value else 0
                        len_saved = len(saved_value) if saved_value else 0
                        if len_new != len_saved:
                            setattr(instance, field, new_value)
                            save_changes = True
                        elif len_new:
                        # compare items in sorted list when len>0 (givers error otherwise)
                            new_value_sorted = sorted(new_value)
                            saved_value_sorted = sorted(saved_value)
                            if new_value_sorted != saved_value_sorted:
                                setattr(instance, field, new_value_sorted)
                                save_changes = True

# 4. save changes in field 'inactive'
                    elif field == 'inactive':
                        #logger.debug('inactive new_value]: ' + str(new_value) + ' ' + str(type(new_value)))
                        saved_value = getattr(instance, field)
                        #logger.debug('inactive saved_value]: ' + str(saved_value) + ' ' + str(type(saved_value)))
                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True
                    else:
                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True
# --- end of for loop ---

# 5. save changes
        if save_changes:
            try:
                instance.save(request=request)
            except:
                msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>








@method_decorator([login_required], name='dispatch')
class SubjectLogView(View):
    def get(self, request, pk):
        subject_log = subj_mod.Subject_log.objects.filter(subject_id=pk).order_by('-modified_at')
        subject = subj_mod.Subject.objects.get(id=pk)
        _param = awpr_menu.get_headerbar_param(request,  {'subject_log': subject_log, 'subject': subject})
        return render(request, 'subject_log.html', _param)


#  =========== Ajax requests  ===========

# PR2018-09-03 from https://simpleisbetterthancomplex.com/tutorial/2018/01/29/how-to-implement-dependent-or-chained-dropdown-list-with-django.html
def load_levels(request):
    logger.debug('load_levels request: ' + str(request) + ' Type: ' + str(type(request)))
    # load_levels request: <WSGIRequest: GET '/scheme/load_levels/?department_id=2'> Type: WSGIRequest
    _dep_id = request.GET.get('department_id')

    # create list of dicts
    items = []  # [{'id': 0, 'name': '---'}]# items = [(0, '---')]
    keys = ['id', 'tag', 'name']

    # get country_id of department
    if _dep_id:
        _dep_id_int = int(_dep_id)
        _dep = sch_mod.Department.objects.get(id=_dep_id_int)
        #logger.debug('load_levels _department ' + str(_department) + ' Type: ' + str(type(_department)))
        if _dep:
            # wrap dep_id in delimiters, so ';1;' can be searched in ";1;15;6;'
            _dep_id_str = ';' + str(_dep_id) + ";"
            # filter on Country (to be on the safe side, not necessary) and dep_id in depbase_list
            _levels = sch_mod.Level.objects.filter(country=_dep.country, depbase_list__contains=_dep_id_str).order_by('sequence')
            logger.debug('load_levels _levels ' + str(_levels) + ' Type: ' + str(type(_levels)))

            for _level in _levels:
                logger.debug('load_levels _level ' + str(_level) + ' Type: ' + str(type(_level)))
                values = [_level.id, _level.depbase_list, _level.abbrev]

                logger.debug('load_levels values: ' + str(values) + ' Type: ' + str(type(values)))
                items.append(dict(zip(keys, values)))

            logger.debug('load_levels items: ' + str(items) + ' Type: ' + str(type(items)))
            # cities: < QuerySet[ < Birthcity: Anderlecht >, ... , < Birthcity: Wilrijk >] > Type: <class 'QuerySet'>
            items = _levels
    return render(request, 'dropdown_list_options.html', {'items': items})



# PR2018-09-03 from https://simpleisbetterthancomplex.com/tutorial/2018/01/29/how-to-implement-dependent-or-chained-dropdown-list-with-django.html
def load_sectors(request):
    _dep_id = request.GET.get('department_id')

    # create list of dicts
    items = []  # [{'id': 0, 'name': '---'}]# items = [(0, '---')]
    keys = ['id','tag', 'name']

    # get country_id of department
    if _dep_id:
        _dep_id_int = int(_dep_id)
        _dep = sch_mod.Department.objects.get(id=_dep_id_int)
        #logger.debug('load_sectors _department ' + str(_department) + ' Type: ' + str(type(_department)))
        if _dep:
            # wrap dep_id in delimiters, so ';1;' can be searched in ";1;15;6;'
            _dep_id_str = ';' + str(_dep_id) + ";"
            # TODO change dep_list in  depbase_list PR2019-02-26
            # filter on Country (to be on the safe side, not necessary) and dep_id in dep_list
            _sectors = sch_mod.Sector.objects.filter(country=_dep.country, dep_list__contains=_dep_id_str).order_by('sequence')
            # logger.debug('load_sectors _levels ' + str(_sectors) + ' Type: ' + str(type(_sectors)))

            for _sector in _sectors:
                logger.debug('load_sectors _sector ' + str(_sector) + ' Type: ' + str(type(_sector)))
                values = [_sector.id, _sector.dep_list, _sector.abbrev]

                items.append(dict(zip(keys, values)))

            logger.debug('load_sectors items: ' + str(items) + ' Type: ' + str(type(items)))
            # cities: < QuerySet[ < Birthcity: Anderlecht >, ... , < Birthcity: Wilrijk >] > Type: <class 'QuerySet'>
            items = _sectors
    return render(request, 'dropdown_list_options.html', {'items': items})


