from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.models import *
from basejump.plural import plural
from basejump.urlizer import urlize
from kickstarter.models import *
from kickstarter.forms import *
from invdb.models import Asset

def index(request):
    if not request.user.is_authenticated():
        return view(request, 'login')
    else:
        return view(request, 'home')

def view(request, route, form_errors=None, instance_id=None, assets=None):
    content_bag = getCommonContent()
    print "route = %s" % route
    if route == 'server_view':
        content_bag['servers'] = Asset.objects.filter(asset_type__name__exact='Server')
        viewname = "kickstart_servers"
    elif route == 'settings_view':
        settings = kssettings.objects.all()
        content_bag['form'] = EditSetting()
        content_bag['settings'] = settings
        viewname = 'kickstart_settings'
    elif route == 'settings_edit':
        content_bag['form'] = EditSetting()
        content_bag['form_action'] = 'kickstarter.views.settings_view'
        viewname = "formview"
    else:
        viewname = 'kickstart'
    print "rendering viewname(%s)" % viewname
    return render_to_response(viewname + '.html', content_bag, context_instance=RequestContext(request))


def getCommonContent():
    content_bag = {}
    content_bag['appname'] = "kickstarter"
    content_bag['kssettings'] = kssettings.objects.all()
    return content_bag

def server_view(request):
    return view(request, 'server_view')

def settings_view(request):
    return view(request, 'settings_view')

def settings_add(request):
    if request.method == "POST":
        form = EditSetting(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            new_setting = form.cleaned_data['setting']
            new_setting = kssettings.create(name, new_setting)
            new_setting.save()
    return settings_view(request)
