# PR2018-07-20
from django.contrib.auth.decorators import login_required # PR2018-04-01
from django.core.paginator import Paginator # PR2018-07-20
from django.core.exceptions import PermissionDenied # PR2018-11-03
import json # PR2018-10-25
from django.db import connection
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect #, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView, DeleteView, View, ListView, CreateView

from schools.models import Department
from subjects.models import Subjectbase, Subject, Subject_log, Level, Level_log, \
    Sector, Sector_log, Subjecttype, Subjecttype_log, \
    Scheme, Scheme_log, Schemeitem, Schemeitem_log

from subjects.forms import SubjectAddForm, SubjectEditForm, \
    LevelAddForm, LevelEditForm, SectorAddForm, SectorEditForm, \
    SubjecttypeAddForm, SubjecttypeEditForm, \
    SchemeAddForm, SchemeEditForm, SchemeitemAddForm, SchemeitemEditForm

from awpr import functions as f
from awpr import constants as c

from django.contrib.auth.mixins import UserPassesTestMixin

# PR2018-04-27
import logging
logger = logging.getLogger(__name__)

# PR2018-05-06
from django.utils.translation import activate, get_language_info, ugettext_lazy as _

"""

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

# === Level =====================================
@method_decorator([login_required], name='dispatch')
class LevelListView(ListView):  # PR2018-08-11

    def get(self, request, *args, **kwargs):
        _params = f.get_headerbar_param(request, {})
        if request.user.examyear is not None:
            # filter Levels of request.user.examyear 'Country is parent of Examyear PR2018-10-18
            levels = Level.objects.filter(examyear=request.user.examyear)
            logger.debug('LevelListView get levels: <' + str(levels) + '> type: <' + str(type(levels)) + '>')

            _params.update({'levels': levels})
        return render(request, 'level_list.html', _params)


@method_decorator([login_required], name='dispatch')
class LevelAddView(CreateView):
    # PR2018-08-11
    def get(self, request, *args, **kwargs):
        form = LevelAddForm(request=request)
        _params = f.get_headerbar_param(request, {
            'form': form,
        })
        return render(request, 'level_add.html', _params)

    def post(self, request, *args, **kwargs):
        form = LevelAddForm(request.POST, request=request)

        if form.is_valid():
            level = form.save(commit=False)

            # ======  set value 'examyear'  ============
            level.examyear = request.user.examyear

            # ======  save field 'depbase_list_field'  ============
            _clean_depbase_list_field = form.cleaned_data.get('depbase_list_field')  # Type: <class 'list'>
            level.depbase_list = f.get_depbase_list_field_sorted_zerostripped(_clean_depbase_list_field)

            level.save(request=self.request)

            return redirect('level_list_url')
        else:
            # If the form is invalid, render the invalid form.
            _param = f.get_headerbar_param(request, {
                'form': form,
                'display_country': True
            })
            return render(request, 'level_add.html', _param)

@method_decorator([login_required], name='dispatch')
class LevelEditView(UserPassesTestMixin, UpdateView):  # PR2018-08-11
    model = Level
    form_class = LevelEditForm
    template_name = 'level_edit.html'
    context_object_name = 'level'

    # PR2018-11-03 from: https://python-programming.com/django/permission-checking-django-views/
    # UserPassesTestMixin uses test_func to check permissions
    def test_func(self):
        is_ok = False
        level_id = self.kwargs['pk']
        if level_id is not None:
            level = Level.objects.filter(id=level_id).first()
            if level.examyear is not None:
                is_ok = self.request.user.examyear_correct(level.examyear.id)
        return is_ok

    # from https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # PR 2018-05-25 add request to kwargs, so it passes request to the form
    def get_form_kwargs(self):
        kwargs = super(LevelEditView, self).get_form_kwargs()
        # add request to kwargs, so it can be passed to form
        kwargs.update({'request': self.request})
        return kwargs

    def form_valid(self, form):
        level = form.save(commit=False)

    # ======  save field 'depbase_list_field'  ============
        _clean_depbase_list_field = form.cleaned_data.get('depbase_list_field')  # Type: <class 'list'>
        logger.debug('_clean_depbase_list_field: <' + str(_clean_depbase_list_field) + '> Type: ' + str(type(_clean_depbase_list_field)))

        level.depbase_list = f.get_depbase_list_field_sorted_zerostripped(_clean_depbase_list_field)
        logger.debug('LevelEditView form_valid level.depbase_list: <' + str(level.depbase_list) + '> Type: ' + str(type(level.depbase_list)))

        level.save(request=self.request)

        return redirect('level_list_url')


@method_decorator([login_required], name='dispatch')
class LevelDeleteView(DeleteView):
    model = Level
    template_name = 'level_delete.html'  # without template_name Django searches for level_confirm_delete.html
    success_url = reverse_lazy('level_list_url')

    def delete(self, request, *args, **kwargs):
       self.object = self.get_object()
       if self.request.user:
          self.object.delete(request=self.request)
          return HttpResponseRedirect(self.get_success_url())
       else:
          raise Http404 #or return HttpResponse('404_url')


@method_decorator([login_required], name='dispatch')
class LevelLogView(View):
    def get(self, request, pk):
        level_log = Level_log.objects.filter(level_id=pk).order_by('-modified_at')
        level = Level.objects.get(id=pk)
        _param = f.get_headerbar_param(request,  {'level_log': level_log, 'level': level})
        return render(request, 'level_log.html', _param)


# === Sector =====================================
@method_decorator([login_required], name='dispatch')
class SectorListView(ListView):  # PR2018-08-23

    def get(self, request, *args, **kwargs):
        _params = f.get_headerbar_param(request, {'select_country': True})
        if request.user.examyear is not None:
            # filter Sectors of request.user.examyear 'Country is parent of Examyear PR2018-10-18
            sectors = Sector.objects.filter(examyear=request.user.examyear)
            _params.update({'sectors': sectors})
        return render(request, 'sector_list.html', _params)


@method_decorator([login_required], name='dispatch')
class SectorAddView(CreateView):  # PR2018-08-24
    def get(self, request, *args, **kwargs):
        form = SectorAddForm(request=request)
        _params = f.get_headerbar_param(request, {
            'form': form,
        })
        return render(request, 'sector_add.html', _params)

    def post(self, request, *args, **kwargs):
        form = SectorAddForm(request.POST, request=request)
        if form.is_valid():
            sector = form.save(commit=False)

            # ======  set value 'examyear'  ============
            sector.examyear = request.user.examyear

            # ======  save field 'depnase_list_field'  ============
            _clean_depbase_list_field = form.cleaned_data.get('depbase_list_field')  # Type: <class 'list'>
            sector.depbase_list = f.get_depbase_list_field_sorted_zerostripped(_clean_depbase_list_field)

            sector.save(request=self.request)

            return redirect('sector_list_url')
        else:
            # If the form is invalid, render the invalid form.
            _param = f.get_headerbar_param(request, {'form': form, 'display_country': True, 'display_examyear': True})
            return render(request, 'sector_add.html', _param)


@method_decorator([login_required], name='dispatch')
class SectorEditView(UserPassesTestMixin, UpdateView):  #PR2018-09-04
        model = Sector
        form_class = SectorEditForm
        template_name = 'sector_edit.html'
        context_object_name = 'sector'

        # PR2018-11-03 from: https://python-programming.com/django/permission-checking-django-views/
        # UserPassesTestMixin uses test_func to check permissions
        def test_func(self):
            is_ok = False
            sector_id = self.kwargs['pk']
            if sector_id is not None:
                sector = Sector.objects.filter(id=sector_id).first()
                if sector.examyear is not None:
                    is_ok = self.request.user.examyear_correct(sector.examyear.id)
            return is_ok

        # from https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
        # PR 2018-05-25 add request to kwargs, so it passes request to the form
        def get_form_kwargs(self):
            kwargs = super(SectorEditView, self).get_form_kwargs()
            # add request to kwargs, so it can be passed to form
            kwargs.update({'request': self.request})
            return kwargs

        def form_valid(self, form):
            sector = form.save(commit=False)

            # ======  save field 'depbase_list_field'  ============
            _clean_depbase_list_field = form.cleaned_data.get('depbase_list_field')  # Type: <class 'list'>
            logger.debug('_clean_depbase_list_field: <' + str(_clean_depbase_list_field) + '> Type: ' + str(type(_clean_depbase_list_field)))

            sector.depbase_list = f.get_depbase_list_field_sorted_zerostripped(_clean_depbase_list_field)
            logger.debug('SectorEditView form_valid sector.depbase_list: <' + str(sector.depbase_list) + '> Type: ' + str(type(sector.depbase_list)))

            sector.save(request=self.request)

            return redirect('sector_list_url')


@method_decorator([login_required], name='dispatch')
class SectorDeleteView(UserPassesTestMixin, DeleteView):
    model = Sector
    template_name = 'sector_delete.html'  # without template_name Django searches for subjectdefault_confirm_delete.html
    success_url = reverse_lazy('sector_list_url')

    # PR2018-11-03 from: https://python-programming.com/django/permission-checking-django-views/
    # UserPassesTestMixin uses test_func to check permissions
    def test_func(self):
        is_ok = False
        sector_id = self.kwargs['pk']
        if sector_id is not None:
            sector = Sector.objects.filter(id=sector_id).first()
            if sector.examyear is not None:
                is_ok = self.request.user.examyear_correct(sector.examyear.id)
        return is_ok

    def delete(self, request, *args, **kwargs):
       self.object = self.get_object()

       if self.request.user:
          self.object.delete(request=self.request)
          return HttpResponseRedirect(self.get_success_url())
       else:
          raise Http404 #or return HttpResponse('404_url')

@method_decorator([login_required], name='dispatch')
class SectorLogView(View):
    def get(self, request, pk):
        sector_log = Sector_log.objects.filter(sector_id=pk).order_by('-modified_at')
        sector = Sector.objects.get(id=pk)
        _param = f.get_headerbar_param(request, {'sector_log': sector_log, 'sector': sector})
        return render(request, 'sector_log.html', _param)


# === Subjecttype =====================================
@method_decorator([login_required], name='dispatch')
class SubjecttypeListView(ListView):  # PR2018-08-11

    def get(self, request, *args, **kwargs):
        _params = f.get_headerbar_param(request, {})
        if request.user.examyear is not None:
            # filter Subjecttypes of request.user.examyear 'Country is parent of Examyear PR2018-10-18
            subjecttypes = Subjecttype.objects.filter(examyear=request.user.examyear)

            _params.update({'subjecttypes': subjecttypes})
        return render(request, 'subjecttype_list.html', _params)


@method_decorator([login_required], name='dispatch')
class SubjecttypeAddView(CreateView):
    # PR2018-08-11
    def get(self, request, *args, **kwargs):
        form = SubjecttypeAddForm(request=request)
        _params = f.get_headerbar_param(request, {
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
            subjecttype.depbase_list = f.get_depbase_list_field_sorted_zerostripped(_clean_depbase_list_field)

            subjecttype.save(request=self.request)

            return redirect('subjecttype_list_url')
        else:
            # If the form is invalid, render the invalid form.
            _param = f.get_headerbar_param(request, {
                'form': form,
                'display_country': True
            })
            return render(request, 'subjecttype_add.html', _param)


@method_decorator([login_required], name='dispatch')
class SubjecttypeEditView(UserPassesTestMixin, UpdateView):  # PR2018-08-11
    model = Subjecttype
    form_class = SubjecttypeEditForm
    template_name = 'subjecttype_edit.html'
    context_object_name = 'subjecttype'

    # PR2018-11-03 from: https://python-programming.com/django/permission-checking-django-views/
    # UserPassesTestMixin uses test_func to check permissions
    def test_func(self):
        is_ok = False
        subjecttype_id = self.kwargs['pk']
        if subjecttype_id is not None:
            subjecttype = Subjecttype.objects.filter(id=subjecttype_id).first()
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
        subjecttype.depbase_list = f.get_depbase_list_field_sorted_zerostripped(_clean_depbase_list_field)

        subjecttype.save(request=self.request)

        return redirect('subjecttype_list_url')


@method_decorator([login_required], name='dispatch')
class SubjecttypeDeleteView(DeleteView):
    model = Subjecttype
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
        subjecttype_log = Subjecttype_log.objects.filter(subjecttype_id=pk).order_by('-modified_at')
        subjecttype = Subjecttype.objects.get(id=pk)
        _param = f.get_headerbar_param(request,  {'subjecttype_log': subjecttype_log, 'subjecttype': subjecttype})
        return render(request, 'subjecttype_log.html', _param)


# === Scheme =====================================
@method_decorator([login_required], name='dispatch')
class SchemeListView(ListView):  # PR2018-08-23

    def get(self, request, *args, **kwargs):
        _param = f.get_headerbar_param(request, {
            'display_country': True,
        })
        if request.user.country is not None:
            if request.user.examyear is not None:
                schemes = Scheme.objects.filter(department__examyear=request.user.examyear)
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
        params = f.get_headerbar_param(request, {
            'form': form,
        })

        # filter Departments of request.user.country
        deps = Department.get_dep_attr(request.user)
        params.update({'deps': json.dumps(deps)})

        # filter Levels of request.user.country
        levels = Level.get_level_attr(request.user)
        params.update({'levels': json.dumps(levels)})

        # filter Sectors of request.user.country
        sectors = Sector.get_sector_attr(request.user)
        params.update({'sectors': json.dumps(sectors)})

        # logger.debug('SchemeAddView params: ' + str(params) + ' Type: ' + str(type(params)))
        return  params

@method_decorator([login_required], name='dispatch')
class SchemeEditView(UpdateView):  # PR2018-08-24
    model = Scheme
    form_class = SchemeEditForm
    template_name = 'scheme_edit.html'
    context_object_name = 'scheme'

    def get_context_data(self, **kwargs):  # https://docs.djangoproject.com/en/2.1/ref/class-based-views/mixins-simple/
        context = super().get_context_data(**kwargs)

        deps = Department.get_dep_attr(self.request.user)
        context['deps'] = json.dumps(deps)

        levels = Level.get_level_attr(self.request.user)
        context['levels'] = json.dumps(levels)

        sectors = Sector.get_sector_attr(self.request.user)
        context['sectors'] = json.dumps(sectors)

        # context['display_country'] = True
        return context

    def get_form_kwargs(self):
        kwargs = super(SchemeEditView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_params(self, request, form):
        params = f.get_headerbar_param(request, {
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
        scheme.fields = f.get_depbase_list_field_sorted_zerostripped(_clean_fields_field)


        scheme.save(request=self.request)
        return redirect('scheme_list_url')


@method_decorator([login_required], name='dispatch')
class SchemeDeleteView(DeleteView):
    model = Scheme
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
        scheme_log = Scheme_log.objects.filter(scheme_id=pk).order_by('-modified_at')
        scheme = Scheme.objects.get(id=pk)
        _param = f.get_headerbar_param(request,  {'scheme_log': scheme_log, 'scheme': scheme})
        return render(request, 'scheme_log.html', _param)

# +++++++++++++++++++++++++++++++++++

# === Schemeitem =====================================
@method_decorator([login_required], name='dispatch')
class SchemeitemListView(ListView):  # PR2018-11-09

    def get(self, request, *args, **kwargs):
        _params = self.get_params(request)
        return render(request, 'schemeitem_list.html', _params)


    def get_params(self, request):

        params = f.get_headerbar_param(request, {
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
        deps = Department.get_select_list(request.user)
        params.update({'deps': json.dumps(deps)})

        # filter Levels of request.user.country
        levels = Level.get_select_list(request.user)
        params.update({'levels': json.dumps(levels)})

        # filter Sectors of request.user.country
        sectors = Sector.get_select_list(request.user)
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
        params = f.get_headerbar_param(request, {
            'form': form,
        })

        # filter Departments of request.user.country
        deps = Department.get_dep_attr(request.user)
        params.update({'deps': json.dumps(deps)})

        # filter Levels of request.user.country
        levels = Level.get_level_attr(request.user)
        params.update({'levels': json.dumps(levels)})

        # filter Sectors of request.user.country
        sectors = Sector.get_sector_attr(request.user)
        params.update({'sectors': json.dumps(sectors)})

        # logger.debug('SchemeitemAddView params: ' + str(params) + ' Type: ' + str(type(params)))
        return  params

@method_decorator([login_required], name='dispatch')
class SchemeitemEditView(UpdateView):  # PR2018-08-24
    model = Schemeitem
    form_class = SchemeitemEditForm
    template_name = 'schemeitem_edit.html'
    context_object_name = 'schemeitem'

    def get_context_data(self, **kwargs):  # https://docs.djangoproject.com/en/2.1/ref/class-based-views/mixins-simple/
        context = super().get_context_data(**kwargs)

        deps = Department.get_dep_attr(self.request.user)
        context['deps'] = json.dumps(deps)

        levels = Level.get_level_attr(self.request.user)
        context['levels'] = json.dumps(levels)

        sectors = Sector.get_sector_attr(self.request.user)
        context['sectors'] = json.dumps(sectors)

        # context['display_country'] = True
        return context

    def get_form_kwargs(self):
        kwargs = super(SchemeitemEditView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_params(self, request, form):
        params = f.get_headerbar_param(request, {
            'form': form,
            'display_country': True
        })
        return  params

    def form_valid(self, form):
        schemeitem = form.save(commit=False)
        # TODO: scheme has field 'department', not 'dep_list' PR2019-01-18
        # ======  save field 'dep_list_field'  ============
        _clean_dep_list_field = form.cleaned_data.get('dep_list_field')  # Type: <class 'list'>
        schemeitem.dep_list = f.get_depbase_list_field_sorted_zerostripped(_clean_dep_list_field)

        schemeitem.save(request=self.request)
        return redirect('schemeitem_list_url')


@method_decorator([login_required], name='dispatch')
class SchemeitemDeleteView(DeleteView):
    model = Schemeitem
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
        schemeitem_log = Schemeitem_log.objects.filter(schemeitem_id=pk).order_by('-modified_at')
        schemeitem = Schemeitem.objects.get(id=pk)
        _param = f.get_headerbar_param(request,  {'schemeitem_log': schemeitem_log, 'schemeitem': schemeitem})
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
                department = Department.objects.filter(id=dep_id_int, examyear=examyear).first()
                if department:
                    dep_abbrev = department.abbrev
                    # logger.debug(dep_abbrev)

                    # lookup level (if required)
                    level = None
                    lvl_abbrev = ''
                    if department.level_req:
                        if 'lvl_id' in request.POST.keys():
                            lvl_id_int = int(request.POST['lvl_id'])
                            level = Level.objects.filter(id=lvl_id_int, examyear=examyear).first()
                            # if level:
                                # lvl_abbrev = level.abbrev
                    # logger.debug(lvl_abbrev)

                    # lookup sector (if required)
                    sector = None
                    sct_name = ''
                    if department.sector_req:
                        if 'sct_id' in request.POST.keys():
                            sct_id_int = int(request.POST['sct_id'])
                            sector = Sector.objects.filter(id=sct_id_int, examyear=examyear).first()
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
                            if Scheme.objects.filter(
                                department=department, level=level, sector=sector
                            ).count() == 1:
                                scheme = Scheme.objects.filter(
                                    department=department, level=level, sector=sector
                                ).first()
                        else:
                            logger.debug('filter by department and level')
                            # filter by department and level
                            # if selection contains multiple schemes: skip
                            if Scheme.objects.filter(
                                    department=department, level=level
                            ).count() == 1:
                                scheme = Scheme.objects.filter(
                                    department=department, level=level
                                ).first()
                    else:
                        if sector:
                            # logger.debug('filter by department and sector')
                            # filter by department and sector
                            # if selection contains multiple schemes: skip

                            logger.debug('count: ' + str(Scheme.objects.filter(department=department, sector=sector).count()))
                            if Scheme.objects.filter(department=department, sector=sector).count() == 1:
                                scheme = Scheme.objects.filter(department=department, sector=sector).first()
                        else:
                            # logger.debug('only by department')
                            # filter only by department
                            # if selection contains multiple schemes: skip
                            if Scheme.objects.filter(department=department).count() == 1:
                                scheme = Scheme.objects.filter(department=department).first()

                    if scheme:
                        scheme_list_str = scheme.get_scheme_list_str()
                        params.update({'scheme': scheme_list_str})

                        # make list of all Subjects from this department and examyear (included in dep)
                        schemeitems = Schemeitem.get_schemeitem_list(scheme)
                        params.update({'schemeitems': schemeitems})

                        # make list of all Subjects from this department and examyear (included in dep)
                        subjects = Subject.get_subj_list(department)
                        params.update({'subjects': subjects})

                        # make list of all Subjecttypes from this department and examyear (included in dep)
                        subjecttypes = Subjecttype.get_subjtype_list( department)  # PR2019-01-18
                        params.update({'subjecttypes': subjecttypes})

                        # make list of all gradetypes

                        # GRADETYPE_CHOICES = ((0, 'None'), (1, 'Number'), (2, 'Good/Sufficient/Insufficient'))
                        gradetypes = []
                        for item in c.GRADETYPE_CHOICES:
                            if item[0] > 0:
                                gradetypes.append({
                                    'grtp_id': str(item[0]),
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
                scheme = Scheme.objects.filter(id=scheme_id).first()
                if scheme:
                    if mode == 'd':
                        # lookup schemeitem
                        schemeitem = Schemeitem.objects.filter(id=ssi_id).first()
                        if schemeitem:
                            schemeitem.delete(request=self.request)
                            record_saved = True
                    else:
                        # check if subject and subjecttype exist
                        subject = Subject.objects.filter(id=subj_id, examyear=request.user.examyear).first()
                        subjecttype = Subjecttype.objects.filter(id=sjtp_id, examyear=request.user.examyear).first()

                        logger.debug('scheme: <' + str(scheme) + '> type: ' + str(type(scheme)))
                        logger.debug('subject: <' + str(subject) + '> type: ' + str(type(subject)))
                        logger.debug('subjecttype: <' + str(subjecttype) + '> type: ' + str(type(subjecttype)))

                        if subject and subjecttype:
                            logger.debug("scheme and subject and subjecttype")
                            if mode == 'c':
                                # create new schemeitem
                                schemeitem = Schemeitem(
                                    scheme=scheme,
                                    subject=subject,
                                    subjecttype=subjecttype
                                )
                            else:
                                # lookup schemeitem
                                schemeitem = Schemeitem.objects.filter(id=ssi_id).first()

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
            schemeitems = Schemeitem.get_schemeitem_list(scheme)
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

        return HttpResponse(json.dumps(params, cls=f.LazyEncoder))


# ========  Subject  =====================================
@method_decorator([login_required], name='dispatch')
class SubjectListView(ListView):
    # PR2018-08-08

    def get(self, request, *args, **kwargs):
        _params = f.get_headerbar_param(request,{})

        # filter subjects of request.user.examyear
        if request.user.examyear is not None:
            subjects = Subject.objects.filter(examyear=request.user.examyear).order_by('sequence')
            # add subjectdefaults to headerbar parameters PR2018-08-12
            _params.update({'subjects': subjects})

        return render(request, 'subject_list.html', _params)


@method_decorator([login_required], name='dispatch')
class SubjectAddView(CreateView):  # PR2018-08-09

    def get(self, request, *args, **kwargs):
        form = SubjectAddForm(request=request)

        _params = f.get_headerbar_param(request, {
            'form': form,
            'display_examyear': True,
            'display_school': True
        })
        return render(request, 'subject_add.html', _params)

    def post(self, request, *args, **kwargs):
        form = SubjectAddForm(request.POST, request=request) # this one doesn't work: form = Subjectdefault(request=request)

        if form.is_valid():
            subject = form.save(commit=False)

            # ======  save field 'depbase_list_field'  ============
            _clean_depbase_list_field = form.cleaned_data.get('depbase_list_field')  # Type: <class 'list'>
            subject.depbase_list = f.get_depbase_list_field_sorted_zerostripped(_clean_depbase_list_field)

            # First create Levelbase record: Levelbase.id is used in Level. Create also saves new record
            # check if request.user.examyear is child of request.user.country PR2018-10-18
            if request.user.examyear.country.pk == request.user.country.pk:
                subject_base = Subjectbase.objects.create(country=request.user.country)

                subject.base = subject_base
                subject.examyear = request.user.examyear

                subject.save(request=self.request)

            return redirect('subject_list_url')
        else:
            # If the form is invalid, render the invalid form.
            _params = f.get_headerbar_param(request, {
                'form': form,
                'display_school': True
            })
            return render(request, 'subject_add.html', _params)


@method_decorator([login_required], name='dispatch')
class SubjectEditView(UpdateView):  # PR2018-10-31
    model = Subject
    form_class = SubjectEditForm
    template_name = 'subject_edit.html'
    context_object_name = 'subject'

    # from https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # PR 2018-05-25 add request to kwargs, so it passes request to the form
    def get_form_kwargs(self):
        kwargs = super(SubjectEditView, self).get_form_kwargs()
        # add request to kwargs, so it can be passed to form
        kwargs.update({'request': self.request})
        return kwargs

    def form_valid(self, form):
        subject = form.save(commit=False)

    # ======  save field 'depbase_list_field'  ============
        _clean_depbase_list_field = form.cleaned_data.get('depbase_list_field')  # Type: <class 'list'>
        subject.depbase_list = f.get_depbase_list_field_sorted_zerostripped(_clean_depbase_list_field)
        #logger.debug('SubjectlEditView form_valid subject.depbase_list: <' + str(subject.depbase_list) + '> Type: ' + str(type(subject.depbase_list)))

        subject.save(request=self.request)

        return redirect('subject_list_url')


@method_decorator([login_required], name='dispatch')
class SubjectDeleteView(DeleteView):
    model = Subject
    template_name = 'subject_delete.html'  # without template_name Django searches for subjectdefault_confirm_delete.html
    success_url = reverse_lazy('subject_list_url')

    def delete(self, request, *args, **kwargs):
       self.object = self.get_object()

       if self.request.user:
          self.object.delete(request=self.request)
          return HttpResponseRedirect(self.get_success_url())
       else:
          raise Http404 #or return HttpResponse('404_url')


@method_decorator([login_required], name='dispatch')
class SubjectLogView(View):
    def get(self, request, pk):
        subject_log = Subject_log.objects.filter(subject_id=pk).order_by('-modified_at')
        subject = Subject.objects.get(id=pk)
        _param = f.get_headerbar_param(request,  {'subject_log': subject_log, 'subject': subject})
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
        _dep = Department.objects.get(id=_dep_id_int)
        #logger.debug('load_levels _department ' + str(_department) + ' Type: ' + str(type(_department)))
        if _dep:
            # wrap dep_id in delimiters, so ';1;' can be searched in ";1;15;6;'
            _dep_id_str = ';' + str(_dep_id) + ";"
            # filter on Country (to be on the safe side, not necessary) and dep_id in depbase_list
            _levels = Level.objects.filter(country=_dep.country, depbase_list__contains=_dep_id_str).order_by('sequence')
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
        _dep = Department.objects.get(id=_dep_id_int)
        #logger.debug('load_sectors _department ' + str(_department) + ' Type: ' + str(type(_department)))
        if _dep:
            # wrap dep_id in delimiters, so ';1;' can be searched in ";1;15;6;'
            _dep_id_str = ';' + str(_dep_id) + ";"
            # filter on Country (to be on the safe side, not necessary) and dep_id in dep_list
            _sectors = Sector.objects.filter(country=_dep.country, dep_list__contains=_dep_id_str).order_by('sequence')
            # logger.debug('load_sectors _levels ' + str(_sectors) + ' Type: ' + str(type(_sectors)))

            for _sector in _sectors:
                logger.debug('load_sectors _sector ' + str(_sector) + ' Type: ' + str(type(_sector)))
                values = [_sector.id, _sector.dep_list, _sector.abbrev]

                items.append(dict(zip(keys, values)))

            logger.debug('load_sectors items: ' + str(items) + ' Type: ' + str(type(items)))
            # cities: < QuerySet[ < Birthcity: Anderlecht >, ... , < Birthcity: Wilrijk >] > Type: <class 'QuerySet'>
            items = _sectors
    return render(request, 'dropdown_list_options.html', {'items': items})


