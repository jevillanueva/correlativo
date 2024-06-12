from datetime import datetime
import uuid
from django.http import Http404, HttpResponse
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.translation import activate
from django.core.paginator import Paginator

from .forms import EmissionByDepartmentForm, EmissionByDepartmentFormEdit, EmissionForm
from .models import Department, Emission, Sequence, UserDepartment


# Create your views here.
@login_required
def index(request):
    activate("es")
    user = request.user  # the user
    email = user.email  # their email
    username = user.username  # their username
    # emissions = Emission.objects.filter()
    user_departments = UserDepartment.objects.filter(user=user)
    emissions_by_department = {}
    query = request.GET.get("q")
    # is a date
    query_date = None
    if query:
        try:
            query_date = datetime.strptime(query, "%d/%m/%Y")
        except ValueError:
            query_date = None
    # is a number
    query_number = None
    if query:
        try:
            query_number = int(query)
        except ValueError:
            query_number = None
    for user_department in user_departments:
        department = user_department.department
        if query:
            emissions_list = Emission.objects.filter(
                Q(sequence__department=department)
                & Q(user=user)
                & (
                    Q(detail__icontains=query)
                    | Q(destination__icontains=query)
                    | Q(number=query_number)
                    | Q(date=query_date)
                )
            ).order_by("received", "-number")
        else:
            emissions_list = Emission.objects.filter(
                user=user, sequence__department=department
            ).order_by("received", "-number")
        paginator = Paginator(emissions_list, 10)
        page_number = request.GET.get(f"page_{department.id}", 1)
        page_obj = paginator.get_page(page_number)
        emissions_by_department[department.id] = page_obj
    tab = request.GET.get(f"tab", 0)
    if not str(tab).isdigit():
        tab = 0
    return render(
        request,
        "emission/index.html",
        {
            "q": query,
            "emissions_by_department": emissions_by_department,
            "user_departments": user_departments,
            "tab": int(tab),
        },
    )


@login_required
# @permission_required('todo.can_view_tasks', raise_exception=True)
def new(request):
    if request.method == "POST":
        form = EmissionForm(request.POST, user=request.user)
        if form.is_valid():
            emission = form.save()
            return redirect("emissions:index")
    else:
        form = EmissionForm(user=request.user)
    return render(request, "emission/new.html", {"form": form, "emission": None})


@login_required
# @permission_required('todo.can_view_tasks', raise_exception=True)
def new(request, id):
    user = request.user
    uid = uuid.UUID(id, version=4)
    department = get_object_or_404(Department, id=uid)
    user_departments = UserDepartment.objects.filter(user=user, department=department)
    if not user_departments:
        raise Http404("No such department")
    sequence = Sequence.objects.filter(department=department, can_emit=True).first()
    if not sequence:
        raise Http404("No sequence available")
    if request.method == "POST":
        form = EmissionByDepartmentForm(
            request.POST, user=request.user, department=department
        )
        if form.is_valid():
            emission = form.save()
            return redirect("emissions:index")
    else:
        form = EmissionByDepartmentForm(user=request.user, department=department)
    return render(request, "emission/emission.html", {"form": form, "emission": None})


@login_required
# @permission_required('todo.can_view_tasks', raise_exception=True)
def edit(request, id):
    activate("es")
    user = request.user
    uid = uuid.UUID(id, version=4)
    emission = get_object_or_404(Emission, id=uid)
    if emission.user != user:
        raise Http404("No such emission")
    user_departments = UserDepartment.objects.filter(
        user=user, department=emission.sequence.department
    )
    if not user_departments:
        raise Http404("No such department")
    if not emission.sequence.can_emit:
        raise Http404("No sequence available")
    if emission.received:
        raise Http404("Emission already received")
    if request.method == "POST":
        form = EmissionByDepartmentFormEdit(
            request.POST,
            user=user,
            department=emission.sequence.department,
            instance=emission,
        )
        if form.is_valid():
            emission = form.save()
            return redirect("emissions:index")
    else:
        form = EmissionByDepartmentFormEdit(
            user=request.user,
            department=emission.sequence.department,
            instance=emission,
        )
    return render(
        request, "emission/emission.html", {"form": form, "emission": emission}
    )


@login_required
@permission_required("emission.can_receive", raise_exception=True)
def receive(request, id):
    activate("es")
    user = request.user
    uid = uuid.UUID(id, version=4)
    emission = get_object_or_404(Emission, id=uid)
    if emission.sequence.department not in UserDepartment.objects.filter(
        user=user
    ).values_list("department", flat=True):
        raise Http404("No such emission")
    if emission.received:
        raise Http404("Emission already received")
    emission.received = True
    emission.user_received = user
    emission.date_received = timezone.now()
    emission.save()
    return redirect("emissions:index")


@login_required
def user_department(request):
    activate("es")
    user = request.user  # the user
    email = user.email  # their email
    username = user.username  # their username
    user_departments = UserDepartment.objects.filter()
    return render(
        request, "user_department/index.html", {"user_departments": user_departments}
    )