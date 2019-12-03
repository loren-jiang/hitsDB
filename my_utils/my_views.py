from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.edit import UpdateView, View, CreateView, ProcessFormView
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.decorators import method_decorator
from .views_helper import build_modal_form_data

class MultiFormMixin(ContextMixin):
    # taken from https://gist.github.com/badri/4a1be2423ce9353373e1b3f2cc67b80b
    # I added feature to take in form arguments
    form_classes = {} 
    form_arguments = {}
    prefixes = {}
    success_urls = {}
    
    initial = {}
    prefix = None
    success_url = None

    def get_form_arguments(self, form_name):
        return self.form_arguments.get(form_name)

    def get_form_classes(self):
        return self.form_classes
     
    def get_forms(self, form_classes):
        return dict([(key, self._create_form(key, class_name)) for key, class_name in form_classes.items()])
    
    def get_form_kwargs(self, form_name):
        kwargs = {}
        kwargs.update({'initial':self.get_initial(form_name)})
        kwargs.update({'prefix':self.get_prefix(form_name)})
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        form_arguments = self.get_form_arguments(form_name)
        if form_arguments:
            kwargs.update(form_arguments)
        return kwargs
    
    def forms_valid(self, forms, form_name):
        form_valid_method = '%s_form_valid' % form_name
        if hasattr(self, form_valid_method):
            return getattr(self, form_valid_method)(forms[form_name])
        else:
            return HttpResponseRedirect(self.get_success_url(form_name))
     
    def forms_invalid(self, forms, form_name):
        return self.render_to_response(self.get_context_data(forms=forms))
    
    def get_initial(self, form_name):
        initial_method = 'get_%s_initial' % form_name
        if hasattr(self, initial_method):
            return getattr(self, initial_method)()
        else:
            return {'action': form_name}
        
    def get_prefix(self, form_name):
        return self.prefixes.get(form_name, self.prefix)
        
    def get_success_url(self, form_name=None):
        return self.success_urls.get(form_name, self.success_url)

    def _create_form(self, form_name, form_class):
        form_kwargs = self.get_form_kwargs(form_name)
        print(form_kwargs)
        form = form_class(**form_kwargs)
        return form

class ProcessMultipleFormsView(ProcessFormView):
    
    def get(self, request, *args, **kwargs):
        form_classes = self.get_form_classes()
        forms = self.get_forms(form_classes)
        return self.render_to_response(self.get_context_data(forms=forms))
     
    def post(self, request, *args, **kwargs):
        form_classes = self.get_form_classes()
        form_name = request.POST.get('action')
        # form_names = request.POST.getlist('action')
        # form_name = None
        # for name in form_names:
        #     if name in request.POST:
        #         form_name = name
        return self._process_individual_form(form_name, form_classes)
        
    def _process_individual_form(self, form_name, form_classes):
        forms = self.get_forms(form_classes)
        form = forms.get(form_name)
        if not form:
            return HttpResponseForbidden()
        elif form.is_valid():
            print('FORM VALID')
            return self.forms_valid(forms, form_name)
        else:
            print('FORM INVALID')
            print(form.errors)
            return self.forms_invalid(forms, form_name)
 
class BaseMultipleFormsView(MultiFormMixin, ProcessMultipleFormsView):
    """
    A base view for displaying several forms.
    """
 
class MultiFormsView(TemplateResponseMixin, BaseMultipleFormsView):
    """
    A view for displaying several forms, and rendering a template response.
    """

class AjaxableResponseMixin: 
    #taken/ tweaked from https://docs.djangoproject.com/en/2.2/topics/class-based-views/generic-editing/#ajax-example
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.is_ajax():
            data = {'result':'failure'}
            data.update({'errors':form.errors.as_json()})
            return JsonResponse(data, status=400)
        else:
            return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super().form_valid(form) 
        if self.request.is_ajax():
            data = {'result':'success'}
            data.update({
                'pk': self.object.pk,
            })
            return JsonResponse(data)
        
        return response

class ModalCreateView(AjaxableResponseMixin, CreateView):
    template_name = 'modals/modal_form.html'

    def dispatch(self, request, *args, **kwargs):
        decorators = kwargs.pop("decorators", [])
        @method_decorator(decorators)
        def helper(self, request, *args, **kwargs):
            return super().dispatch(request, *args, **kwargs)
        return helper(self, request, *args, **kwargs)

    def get_initial(self, *args, **kwargs):
        initial = super(ModalCreateView, self).get_initial(*args, **kwargs)
        return initial

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(ModalCreateView, self).get_form_kwargs(*args, **kwargs) 
        user = self.request.user
        if user:
            kwargs['user'] = user
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(ModalCreateView, self).get_context_data(*args, **kwargs)
        context.update({
            "modal_title":"New " + self.form_class.Meta.model.model_name ,
            "action": self.form_class.Meta.model.newInstanceUrl(), 
            "use_ajax":True, 
        })
        return context 

class ModalEditView(AjaxableResponseMixin, UpdateView):
    template_name = 'modals/modal_form.html'

    def dispatch(self, request, *args, **kwargs):
        decorators = kwargs.pop("decorators", [])
        @method_decorator(decorators)
        def helper(self, request, *args, **kwargs):
            return super().dispatch(request, *args, **kwargs)
        return helper(self, request, *args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs) 
        user = self.request.user
        if user:
            kwargs['user'] = user
        return kwargs

    def get_context_data(self, *args, **kwargs):
        pk = self.object.pk
        # modalFormData = self.object.getModalFormData()
        modalFormData = build_modal_form_data(type(self.object))
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
            "arg":pk,
            "modal_title":"Edit " + self.form_class.Meta.model.model_name,
            'action':self.object.editInstanceUrl,
            "form_class": modalFormData['edit']['form_class'],
            "use_ajax":True,
        })
        return context

class ModifyFromTableView(View):
    model_class = None

    def post(self, request, *args, **kwargs):
        prev = request.META.get('HTTP_REFERER')
        form = request.POST
        btn_id = form['btn']
        if btn_id:
            pks = form.getlist('checked') #list of model instance pks
            qs = self.model_class.objects.filter(id__in=pks)
            if btn_id=="delete_selected":
                qs.delete()
        return redirect(prev)
