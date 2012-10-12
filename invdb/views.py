from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.models import *
from basejump.plural import plural
from invdb.models import *
from invdb.forms import *

def index(request):
    if not request.user.is_authenticated():
        return formview(request, 'login')
    else:
        return gridview(request, 'index')


def formview(request, formname):
    content_bag = get_common_content(request)
    if formname == "area_add":
        content_bag['form'] = AddArea()
        content_bag['form_action'] = 'invdb.views.area_add'
    print "\n\nCONTENT BAG\n%s\n\n" % content_bag
    return render_to_response('formview.html', content_bag, context_instance=RequestContext(request))

def gridview(request, gridname="index"):
    content_bag = get_common_content(request)
    areas = getArea()
    if not areas:
        return formview(request, "area_add")
    content_bag['areas'] = areas
    print "\n\nCONTENT BAG\n%s\n\n" % content_bag
    return render_to_response(gridname + '.html', content_bag, context_instance=RequestContext(request))

def get_common_content(request):
    content_bag = {
        'nav_left_menu': menutize(getAssetTypes()),
        'user': request.user,
    }
    return content_bag

def menutize(boo):
    # boo: bunch of objects
    menu = []
    for o in boo:
        menuitem = {
            'name': plural(o.name),
            'url': '#',
            }
        menu.append(menuitem)
    return menu

def getAssetTypes():
    assettypes = AssetType.objects.all().order_by('name')
    return assettypes

def getArea():
    areas = Area.objects.all().order_by('name')
    return areas

def area_add(request):
    if request.method == "POST":
        form = AddArea(request.POST)
        if form.is_valid():
            area_name = form.cleaned_data['name']
            area_address = form.cleaned_data['address']
            area_phone = form.cleaned_data['phone']
            area_email = form.cleaned_data['email']
        else:
            return formview(request,'area_add')
    else:
        return index(request)
