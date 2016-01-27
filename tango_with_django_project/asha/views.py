from django.http import HttpResponse,HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from asha.models import Category,Page
from asha.forms import CategoryForm,PageForm,UserForm, UserProfileForm
from django.contrib.auth import authenticate, login , logout
from django.contrib.auth.decorators import login_required
from datetime import datetime
from asha.search import run_query
@login_required
def restricted(request):
    return HttpResponse("Since you're logged in, you can see this text!")
@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/asha/')
def search(request):
    context = RequestContext(request)
    result_list = []
    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            result_list = run_query(query)

    return render_to_response('asha/search.html', {'result_list': result_list}, context)
def register(request):
    if request.session.test_cookie_worked():
        print ">>>> TEST COOKIE WORKED!"
        request.session.delete_test_cookie()
    context = RequestContext(request)
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()
            registered = True

        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render_to_response(
            'asha/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
            context)
def user_login(request):
    context = RequestContext(request)
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/asha/')
            else:
                return HttpResponse("Your account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('asha/login.html', {}, context)

def index(request):
    request.session.set_test_cookie()
    context=RequestContext(request)
    page_list=Page.objects.order_by('-views')[:5]
    context_dict={'pages':page_list}
    category_list=Category.objects.order_by('-likes')[:5]
    context_dict['categories']=category_list
    for category in category_list:
        category.url=category.name.replace(' ','_')
    if request.session.get('last_visit'):
        # The session has a value for the last visit
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits', 0)

        if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
            request.session['visits'] = visits + 1
            request.session['last_visit'] = str(datetime.now())
    else:
        # The get returns None, and the session does not have a value for the last visit.
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = 1
    #### END NEW CODE ####

    return render_to_response('asha/index.html', context_dict, context)
    # If the cookie doesn't exist, we default to zero and cast that.
"""    visits = int(request.COOKIES.get('visits', '0'))
   if 'last_visit' in request.COOKIES:
        last_visit=request.COOKIES['last_visit']
        last_visit_time =datetime.strptime(last_visit[:-7],"%Y-%m-%d %H:%M:%S")
        if(datetime.now()-last_day_time).days >0:
            response.set_cookie('last_visit',visits+1)
            response.set_cookie('last_visit', datetime.now())
    else:
        response.set_cookie('last_visit', datetime.now())
    return response"""

def about(request):
    context=RequestContext(request)
    context_dict={}
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0
    return render_to_response('asha/about.html', {'visits': count}, context)
def category(request,category_name_url):
    context=RequestContext(request)
    # URLs don't handle spaces well, so we encode them as underscores.
    # We can then simply replace the underscores with spaces again to get the name.
    category_name=category_name_url.replace('_',' ')
    context_dict={'category_name':category_name}
    context_dict["category_name_url"]=category_name_url
    try:
        category=Category.objects.get(name=category_name)
        pages=Page.objects.filter(category=category)
        context_dict["pages"]=pages
        context_dict["category"]=category
    except Category.DoesNotExist:
        pass
    return render_to_response('asha/category.html',context_dict,context)
def decode_url(url):
    return url.replace('_',' ')
def add_category(request):
    context=RequestContext(request)
    if request.method=='POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            #to show user home page
            return index(request)
        else:
            print form.errors

    else:
        # If the request was not a POST, display the form to enter details.
        form = CategoryForm()
    return render_to_response('asha/add_category.html', {'form': form}, context)

def add_page(request,category_name_url):
    context=RequestContext(request)
    category_name = decode_url(category_name_url)
    if request.method=='POST':
        form = PageForm(request.POST)

        if form.is_valid():
            page=form.save(commit=False)
            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:                
                return render_to_response('asha/add_category.html', {}, context)
            page.views=0
            page.save()
            # Now that the page is saved, display the category instead.
            return category(request, category_name_url)
        else:
            print form.errors

    else:
        # If the request was not a POST, display the form to enter details.
        form = PageForm()
    return render_to_response('asha/add_page.html',{'category_name_url': category_name_url,'category_name': category_name, 'form': form},context)
