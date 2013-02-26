from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.utils import simplejson
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.template import RequestContext
from django.contrib.auth.models import *
from django import template
from basejump.plural import plural
from basejump.urlizer import urlize
from basejump.ipmi import *
from kickstarter.models import *
from kickstarter.forms import *
from invdb.models import Asset
from basejump.checker import *
import re

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
        content_bag['bootoptions'] = getBootOptions()
        viewname = "kickstart_servers"
    elif route == 'settings_view':
        settings = kssettings.objects.all()
        service_checks = ServiceCheck.objects.all()
        checkResults = runChecks(service_checks)
        content_bag['service_checks'] = service_checks
        content_bag['checkResults'] = checkResults
        content_bag['form'] = EditSetting()
        content_bag['settings'] = settings
        viewname = 'kickstart_settings'
    elif route == 'settings_edit':
        content_bag['form'] = EditSetting()
        content_bag['form_action'] = 'kickstarter.views.settings_view'
        viewname = "formview"
    elif route == "bootoptions_view":
        content_bag['bootoptions'] = getBootOptions()
        content_bag['form'] = AddBootOption()
        viewname = 'kickstart_bootoptions'
    elif route == "bootoptions_add":
        content_bag['form'] = AddBootOption()
    elif route == 'bootoptions_edit':
        content_bag['form'] = AddBootOption()
    else:
        viewname = 'kickstart'
    print "rendering viewname(%s)" % viewname
    print "\n\nCONTENT_BAG:\n%s\n\n" % content_bag
    return render_to_response(viewname + '.html', content_bag, context_instance=RequestContext(request))


def getCommonContent():
    content_bag = {}
    content_bag['appname'] = "kickstarter"
    content_bag['kssettings'] = kssettings.objects.all()
    return content_bag

def getBootOptions():
    boot_options = BootOption.objects.all()
    return boot_options

def server_view(request):
    return view(request, 'server_view')

def settings_view(request):
    return view(request, 'settings_view')

def bootoptions_view(request):
    return view(request, 'bootoptions_view')

def bootoptions_edit(request):
    return view(request, 'bootoptions_edit')

def bootoptions_add(request):
    if request.method == "POST":
        form = AddBootOption(request.POST)
        if form.is_valid():
            form.save()
            return view(request, 'bootoptions_view')
        else:
            return view(request, 'bootoptions_add', form.errors)
    return view(request, 'bootoptions_add')

def settings_add(request):
    if request.method == "POST":
        form = EditSetting(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            new_setting = form.cleaned_data['setting']
            new_setting = kssettings.create(name, new_setting)
            new_setting.save()
            return settings_view(request)

def getSetting(setting_key):
    settings = kssettings.objects.get(name__exact=setting_key)
    return settings.setting

def kickme(request, opsys, release, arch):
    response = HttpResponse(content_type="text/plain")
    debugging =  "Operating System: %s\nRelease: %s\nArch: %s\n" % (opsys, release, arch)
    log = open('kicker.log', 'w')
    log.write("%s" % request)
    try:
        CLIENT_MAC = request.META['HTTP_X_RHN_PROVISIONING_MAC_0']
    except KeyError:
        response.write("NO MAC ADDRES SENT IN REQUEST\n")
        CLIENT_MAC = 'eth0 08:00:27:B6:8B:32'
        #return response
    CLIENT_MAC = CLIENT_MAC.partition(' ')[2].replace(':','')
    try:
        asset = Asset.objects.get(primary_interface__mac=CLIENT_MAC)
    except:
        response.write("Could not find asset with MAC: '%s''\n" % CLIENT_MAC)
        return response
    print "ASSET INFO: %s" % asset.primary_interface.ip4
    CLIENT_IP = asset.primary_interface.ip4
    if CLIENT_IP is not None:
        response.write("NO CLIENT IP IN DATABASE\n")
        if asset.hostname is None:
            response.write("CLIENT_HOSTNAME NOT DEFINED FOR INTEFFACE WITH MAC: %s\n" % CLIENT_MAC)
            return response
        CLIENT_NETMASK='255.255.255.0'
        CLIENT_GATEWAY='10.88.189.1'
        CLIENT_NS='10.88.160.40'
        ksconfig = open('kickstarter/ksconfigs/ksconfig', 'r').read()
        ksconfig = ksconfig.replace('__NETWORK__', '--bootproto=static --ip=' + CLIENT_IP + ' --netmask=' + CLIENT_NETMASK + ' --gateway=' + CLIENT_GATEWAY + ' --nameserver=' + CLIENT_NS)
        REPO = getSetting('REPO_URL')
        REPO = REPO.replace('__OS__', opsys)
        REPO = REPO.replace('__RELEASE__', release)
        REPO = REPO.replace('__ARCH__', arch)
        ksconfig = ksconfig.replace('__REPO_URL__', REPO)
        ksconfig = ksconfig.replace('__BASEJUMP_URL__', request.META['HTTP_HOST'])
        log.write("Returning the following ksconfig:\n%s" % ksconfig)
        response.write(ksconfig)
    else:
        response.write("IP ADDRESS FOR (%s) NOT FOUND IN INVENTORY:\n" % CLIENT_MAC)
    return response


def returnFile(request, filename):
    import os.path
    import mimetypes
    mimetypes.init()
    try:
        file_path = settings.PROJECT_DIR + '/kickstarter/' + filename
        fsock = open(file_path,"r")
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        mime_type_guess = mimetypes.guess_type(file_name)
        if mime_type_guess is not None:
            response = HttpResponse(fsock, mimetype=mime_type_guess[0])
            response['Content-Disposition'] = 'attachment; filename=' + file_name
    except IOError:
        response = HttpResponseNotFound()
    return response

def chef_validator(request):
    return returnFile(request, "chef-validation.pem")

def chef_client(request):
    return returnFile(request, "chef-client.rb")


def BootFileName(mac):
    tftp_root = getSetting('TFTP_ROOT')
    pxe_root = tftp_root + '/pxelinux.cfg'
    mac_pxe_file = pxe_root + '/' + re.sub("(.{2})", "\\1-", mac, re.DOTALL)[:17]
    return mac_pxe_file

def checkBootOption(asset_id):
    default_boot = "localboot"
    asset = Asset.objects.get(pk=asset_id)
    if asset is not None:
        mac = asset.primary_interface.mac
        if mac is None:
            return default_boot
        mac_pxe_file = BootFileName(mac)
        print "CHECKING TFTP_ROOT FOR PXE FILE: (%s)" % mac_pxe_file
        pxe_boot_option = readLink(mac_pxe_file)
        print "%s --> %s" % (mac_pxe_file, pxe_boot_option)
            # read the link (00-aa-bb-cc-dd-ee -> /data/tftpboot/pxelinux.cfg/centos6.3)
            #               (00-aa-bb-cc-dd-ef -> /data/tftpboot/pxelinux.cfg/localboot)
    return default_boot

def bootoptions_get_assetid(request, asset_id):
    bootoption = checkBootOption(asset_id)
    print "THE BOOTOPTION FOR (%s) is (%s)" % (asset_id, bootoption)
    return returnJSON(bootoption)

def bootoptions_get_macaddr(request, macaddr):
    # normalize the mac to HEX, no dashes, uppercase
    mac = str(macaddr.replace("-", ""))
    mac = mac.upper()
    asset = Asset.objects.get(primary_interface__mac=mac)
    return bootoptions_get_assetid(request, asset.pk)

# I think that using jQuery to mess with the form is screwing up CSRF validation
# which results in a HTTP/403 Response, but no futher explanation
@csrf_exempt
def servers_kick(request):
    # this function needs to do 2 parts
    # 1. create the BootOption file
    # 2. reboot the server
    print "GOT REBOOT REQUEST"
    if request.method == "POST":
        asset_id = request.POST['asset_id']
        bootoption_id = request.POST['select_pxe_option']
        asset = Asset.objects.get(pk=asset_id)
        mac = asset.primary_interface.mac
        mac_file = BootFileName(mac)
        print "SETTING BOOTOPTION TO %s" % bootoption_id
        if fileExists(mac_file):
            print "REMOVING OLD SYMLINK %s" % mac_file
            os.unlink(mac_file)
        if bootoption_id == "localboot":
            print "CREATING SYMLINK (%s -> localbootl)" % mac_file
            os.symlink("localboot", mac_file)
        else:
            bootoption = BootOption.objects.get(pk=bootoption_id)
            print "CREATING SYMLINK (%s -> %s)" % (mac_file, bootoption.label)
            os.symlink(bootoption.label, mac_file)
        print "SENDING POWER CYCLE SIGNAL VIA IPMI"
        powerCycle(asset.console)
        return HttpResponse("GOOD:\n%s" % request.POST, mimetype="text/plain")
    else:
        return HttpResponse(status=204)

def returnJSON(to_json):
    return HttpResponse(simplejson.dumps(to_json), mimetype="application/json")
