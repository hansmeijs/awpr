# PR2018-07-20
from django.contrib.auth.decorators import login_required # PR2018-04-01
from django.core.paginator import Paginator # PR2018-07-20
from django.core.exceptions import PermissionDenied # PR2018-11-03
import json # PR2018-10-25
from django.db import connection
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect, Http404
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

            # ======  save field 'dep_list_field'  ============
            _clean_dep_list_field = form.cleaned_data.get('dep_list_field')  # Type: <class 'list'>
            level.dep_list = f.get_depbase_list_field_sorted_zerostripped(_clean_dep_list_field)

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

    # ======  save field 'dep_list_field'  ============
        _clean_dep_list_field = form.cleaned_data.get('dep_list_field')  # Type: <class 'list'>
        level.dep_list = f.get_depbase_list_field_sorted_zerostripped(_clean_dep_list_field)
        # logger.debug('LevelEditView form_valid level.dep_list: <' + str(level.dep_list) + '> Type: ' + str(type(level.dep_list)))

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

            # ======  save field 'dep_list_field'  ============
            _clean_dep_list_field = form.cleaned_data.get('dep_list_field')  # Type: <class 'list'>
            sector.dep_list = f.get_depbase_list_field_sorted_zerostripped(_clean_dep_list_field)

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

            # ======  save field 'dep_list_field'  ============
            _clean_dep_list_field = form.cleaned_data.get('dep_list_field')  # Type: <class 'list'>
            sector.dep_list = f.get_depbase_list_field_sorted_zerostripped(_clean_dep_list_field)
            # logger.debug('SectorEditView form_valid sector.dep_list: <' + str(sector.dep_list) + '> Type: ' + str(type(sector.dep_list)))

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

            # ======  save field 'dep_list_field'  ============
            _clean_dep_list_field = form.cleaned_data.get('dep_list_field')  # Type: <class 'list'>
            subjecttype.dep_list = f.get_depbase_list_field_sorted_zerostripped(_clean_dep_list_field)

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

    # ======  save field 'dep_list_field'  ============
        _clean_dep_list_field = form.cleaned_data.get('dep_list_field')  # Type: <class 'list'>
        subjecttype.dep_list = f.get_depbase_list_field_sorted_zerostripped(_clean_dep_list_field)

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

        # ======  save field 'dep_list_field'  ============
        _clean_dep_list_field = form.cleaned_data.get('dep_list_field')  # Type: <class 'list'>
        scheme.dep_list = f.get_depbase_list_field_sorted_zerostripped(_clean_dep_list_field)

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
        _param = f.get_headerbar_param(request, {
            'display_country': True,
            'select_examyear': True,
        })
        if request.user.country is not None:
            if request.user.examyear is not None:
                schemeitems = Schemeitem.objects.filter(scheme__department__examyear=request.user.examyear)
                _param.update({'schemeitems': schemeitems})
        return render(request, 'schemeitem_list.html', _param)


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

            # ======  save field 'dep_list_field'  ============
            _clean_dep_list_field = form.cleaned_data.get('dep_list_field')  # Type: <class 'list'>
            subject.dep_list = f.get_depbase_list_field_sorted_zerostripped(_clean_dep_list_field)

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

    # ======  save field 'dep_list_field'  ============
        _clean_dep_list_field = form.cleaned_data.get('dep_list_field')  # Type: <class 'list'>
        subject.dep_list = f.get_depbase_list_field_sorted_zerostripped(_clean_dep_list_field)
        # logger.debug('SubjectlEditView form_valid subject.dep_list: <' + str(subject.dep_list) + '> Type: ' + str(type(subject.dep_list)))

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
            # filter on Country (to be on the safe side, not necessary) and dep_id in dep_list
            _levels = Level.objects.filter(country=_dep.country, dep_list__contains=_dep_id_str).order_by('sequence')
            logger.debug('load_levels _levels ' + str(_levels) + ' Type: ' + str(type(_levels)))

            for _level in _levels:
                logger.debug('load_levels _level ' + str(_level) + ' Type: ' + str(type(_level)))
                values = [_level.id, _level.dep_list, _level.abbrev]

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


