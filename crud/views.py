from .models import *
import datetime
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from crud.forms import *
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect
from django.db.models import F
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash 
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password 
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
import uuid
import pandas as pd
import pickle
import numpy as np
import threading
import datetime
import json
from .serializers import SimulationSerializer, DataSerializer
import csv
from django.http import HttpResponse
from time import strftime
from fpdf import FPDF
from tempfile import NamedTemporaryFile
import os

# Register
@csrf_protect
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
            )
            user.set_password(form.cleaned_data['password1'])
            user.is_staff = True
            user.is_active = True
            user.is_superuser = True
            try:
                user.full_clean()
                user.save()
                messages.success(request, 'Member was created successfully!')
                return redirect('register_success')
            except ValidationError as e:
                messages.error(request, 'Error: {}'.format(e))
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def register_success(request):
    return render(request, 'success.html')

# Dashboard
@login_required
def dashboard(request):
    get_simulation = Simulation.objects.all()  
    get_simulation = list(get_simulation)
    get_simulation.reverse() 
    number_user = len(get_simulation)  

    if number_user == 0:
        max_score = 0
        min_score = 0
    else:
        max_score = get_simulation[0].score
        min_score = get_simulation[0].score

    for i in get_simulation:
        if i.score > max_score:
            max_score = i.score
        if i.score < min_score:
            min_score = i.score 

    score_counts = {'<10': 0, '10-30': 0, '>30': 0}
    for i in get_simulation:
        if i.score < 10:
            score_counts['<10'] += 1
        elif 10 <= i.score <= 30:
            score_counts['10-30'] += 1
        elif i.score > 30:
            score_counts['>30'] += 1
    counts = list(score_counts.values())
    number_potential_customers = counts[1] + counts[2]

    # percent
    try:
        metrics, _ = DashboardMetrics.objects.get_or_create(
            id=1,
            defaults={
                'number_user': 0,
                'max_score': 0,
                'min_score': 0,
                'number_potential_customers': 0,
                'number_user_percent': 0,
                'max_score_percent': 0,
                'min_score_percent': 0,
                'number_potential_customers_percent': 0,
            }
        )

        if number_user != 0:
            if number_user != metrics.number_user:
                number_user_percent = round((number_user - metrics.number_user) / number_user * 100, 2)
                if max_score == 0:
                    max_score_percent = 0
                else:
                    max_score_percent = round((max_score - metrics.max_score) / max_score * 100, 2)
                if min_score == 0:
                    min_score_percent = 0
                else:
                    min_score_percent = round((min_score - metrics.min_score) / min_score * 100, 2)
                if number_potential_customers == 0:
                    number_potential_customers_percent = 0
                else:
                    number_potential_customers_percent = round((number_potential_customers - metrics.number_potential_customers) / number_potential_customers * 100, 2)
                
                metrics.number_user = number_user
                metrics.max_score = max_score
                metrics.min_score = min_score
                metrics.number_potential_customers = number_potential_customers
                metrics.number_user_percent = number_user_percent
                metrics.max_score_percent = max_score_percent
                metrics.min_score_percent = min_score_percent
                metrics.number_potential_customers_percent = number_potential_customers_percent
                metrics.save()
            else:
                number_user_percent = metrics.number_user_percent
                max_score_percent = metrics.max_score_percent
                min_score_percent = metrics.min_score_percent
                number_potential_customers_percent = metrics.number_potential_customers_percent
        else:
            number_user_percent = 0
            max_score_percent = 0
            min_score_percent = 0
            number_potential_customers_percent = 0
            metrics.number_user = 0
            metrics.max_score = 0
            metrics.min_score = 0
            metrics.number_potential_customers = 0
            metrics.number_user_percent = 0
            metrics.max_score_percent = 0
            metrics.min_score_percent = 0
            metrics.number_potential_customers_percent = 0
            metrics.save()

    except DashboardMetrics.DoesNotExist:
        metrics = DashboardMetrics.objects.create(
            id=1,
            number_user=0,
            max_score=0,
            min_score=0,
            number_potential_customers=0,
            number_user_percent=0,
            max_score_percent=0,
            min_score_percent=0,
            number_potential_customers_percent=0
        )
    
    context = {
        'get_simulation': get_simulation,
        'number_user': number_user,
        'max_score': round(max_score, 2),
        'min_score': round(min_score, 4),
        'number_potential_customers': number_potential_customers,
        'number_user_percent': metrics.number_user_percent,
        'max_score_percent': metrics.max_score_percent,
        'min_score_percent': metrics.min_score_percent,
        'number_potential_customers_percent': metrics.number_potential_customers_percent,
    }
    return render(request, 'dashboard.html', context)

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'CUSTOMER SCORING PERFORMANCE REPORT', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')
def bold_text(pdf, text):
    pdf.set_font('Arial', 'B', 12)
    pdf.multi_cell(0, 10, text)
def normal_text(pdf, text):
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, text)

def export_report(request):
    metrix = DashboardMetrics.objects.get(id=1)

    # Tạo một tệp PDF tạm thời
    with NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf_file:
        temp_pdf_path = temp_pdf_file.name

        # Tạo PDF và điền thông tin vào
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        headers_data = [
            ["1. Total user data:", f"- User: {metrix.number_user}\n- Change rate: {metrix.number_user_percent}%\n"],
            ["2. Total potential customer data:", f"- Potential customer: {metrix.number_potential_customers}\n- Change rate: {metrix.number_potential_customers_percent}%\n"],
            ["3. Score:", f"- Max score: {metrix.max_score}\n- Change rate: {metrix.max_score_percent}%\n\n- Min score: {metrix.min_score}\n- Change rate: {metrix.min_score_percent}%\n"],
            ["4. Pie chart:", ""],
            ["5. Bar chart:", ""],
        ]

        get_simulation = Simulation.objects.all()
        chart_score_counts = {'10-20': 0, '20-30': 0, '>30': 0}
        pie_score_counts = {'<10': 0, '10-30': 0, '>30': 0}
        for simulation in get_simulation:
            if simulation.score < 10:
                pie_score_counts['<10'] += 1
            elif 10 <= simulation.score < 20:
                chart_score_counts['10-20'] += 1
                pie_score_counts['10-30'] += 1
            elif 20 <= simulation.score <= 30:
                chart_score_counts['20-30'] += 1
                pie_score_counts['10-30'] += 1
            elif simulation.score > 30:
                chart_score_counts['>30'] += 1
                pie_score_counts['>30'] += 1
        
        for level, count in pie_score_counts.items():
            headers_data[3][1] += f"- Level {level} ({'10 - 30' if level == '10-30' else level}): {count}\n"
        for level, count in chart_score_counts.items():
            headers_data[4][1] += f"- Level {level} ({'10 - 20' if level == '10-20' else level}): {count}\n"

        for header, data in headers_data:
            bold_text(pdf, header)
            normal_text(pdf, data)

        pdf.output(temp_pdf_path)

    # Đọc nội dung tệp PDF tạm thời
    with open(temp_pdf_path, 'rb') as f:
        pdf_content = f.read()

    # Tạo HTTPResponse chứa nội dung PDF và gửi về client
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    os.unlink(temp_pdf_path)
    return response
# Upload File
def process_data_chunk(df_chunk):
    for index, row in df_chunk.iterrows(): 
        simulation = Simulation(
            user_id = row['UserID'],
            basket_icon_click = row['basket_icon_click'],
            basket_add_list = row['basket_add_list'],
            basket_add_detail = row['basket_add_detail'],
            sort_by = row['sort_by'],
            image_picker = row['image_picker'],
            account_page_click = row['account_page_click'],
            promo_banner_click = row['promo_banner_click'],
            detail_wishlist_add = row['detail_wishlist_add'],
            list_size_dropdown = row['list_size_dropdown'],
            closed_minibasket_click = row['closed_minibasket_click'],
            checked_delivery_detail = row['checked_delivery_detail'],
            checked_returns_detail = row['checked_returns_detail'],
            sign_in = row['sign_in'],
            saw_checkout = row['saw_checkout'],
            saw_sizecharts = row['saw_sizecharts'],
            saw_delivery = row['saw_delivery'],
            saw_account_upgrade = row['saw_account_upgrade'],
            saw_homepage = row['saw_homepage'],
            device_computer = row['device_computer'],
            device_tablet = row['device_tablet'],
            returning_user = row['returning_user'],
            loc_uk = row['loc_uk'], 
            propensity = row['propensity'],
            score = row['score'],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(), )
        simulation.save() 
@login_required
def fileupload(request): 
    context = {}
    return render(request, 'fileupload.html', context) 

# Simulation 
def convert_to_score(probability, epsilon=1e-10):
    score = np.log((probability + epsilon) / (1 - probability + epsilon))
    return score+30
 
@login_required
def simulation(request):
    columns = ["Basket icon click", "Basket add list", "Basket add detail", "Sort by", "Image picker", "Account page click", "Promo banner click", "Detail wishlist add", "List size dropdown", "Closed minibasket click", "Checked delivery detail", "Checked returns detail", "Sign in", "Saw checkout", "Saw sizecharts", "Saw delivery", "Saw account upgrade", "Saw homepage", "Device computer", "Device tablet", "Returning user", "Loc uk"]

    context = {'columns': columns}
    return render(request, 'simulation.html',context)



@login_required 
def save_file(request):
    simulations = Simulation.objects.all()
    file_name = f"data_{strftime('%Y-%m-%d-%H-%M')}"

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{file_name}.csv"'
    writer = csv.writer(response)
    writer.writerow(['user_id', 'basket_icon_click', 'basket_add_list', 'basket_add_detail', 'sort_by', 'image_picker', 'account_page_click', 'promo_banner_click', 'detail_wishlist_add', 'list_size_dropdown', 'closed_minibasket_click', 'checked_delivery_detail', 'checked_returns_detail', 'sign_in', 'saw_checkout', 'saw_sizecharts', 'saw_delivery', 'saw_account_upgrade', 'saw_homepage', 'device_computer', 'device_tablet', 'returning_user', 'loc_uk', 'propensity', 'score'])

    for i in simulations:
        writer.writerow([i.user_id, i.basket_icon_click, i.basket_add_list, i.basket_add_detail, i.sort_by, i.image_picker, i.account_page_click, i.promo_banner_click, i.detail_wishlist_add, i.list_size_dropdown, i.closed_minibasket_click, i.checked_delivery_detail, i.checked_returns_detail, i.sign_in, i.saw_checkout, i.saw_sizecharts, i.saw_delivery, i.saw_account_upgrade, i.saw_homepage, i.device_computer, i.device_tablet, i.returning_user, i.loc_uk, i.propensity, i.score])  

    return response


@login_required
def delete1(request, user_id): 
    simulation = Simulation.objects.filter(user_id=user_id).first()
    simulation.delete()
    messages.success(request, 'Data was deleted successfully!') 
    return redirect('database')


@login_required
def delete_all(request):
    Simulation.objects.all().delete()
    messages.success(request, 'All Simulations were deleted successfully!') 
    return redirect('database')

# database
@login_required
def database(request):
    get_simulation = Simulation.objects.all()  
    get_simulation = list(get_simulation)

    serializer = SimulationSerializer(get_simulation, many=True)
    get_simulation = serializer.data 
    get_simulation.reverse() 

    # Pagination
    number = 10
    select1 = "All"
    if request.method == 'GET':
        number = request.GET.get('number', 10) 
        number = int(number)

        select1 = request.GET.get('filter',"All")
        print("select: ", select1)
        if select1 == "All":
            get_simulation = get_simulation
        elif select1 == "Level 1":
            get_simulation = [i for i in get_simulation if i['score'] >30] 
        elif select1 == "Level 2":
            get_simulation = [i for i in get_simulation if 20 <= i['score'] <= 30] 
        elif select1 == "Level 3":
            get_simulation = [i for i in get_simulation if 10 <= i['score'] < 20]
    paginator = Paginator(get_simulation, number)
    page = request.GET.get('page')
    
    select1 = select1.replace(" ", "_")
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages) 


    # fiter
    dic_cols = {"basket_icon_click":"Basket icon click", "basket_add_list":"Basket add list", "basket_add_detail":"Basket add detail", "sort_by":"Sort by", "image_picker":"Image picker", "account_page_click":"Account page click", "promo_banner_click":"Promo banner click", "detail_wishlist_add":"Detail wishlist add", "list_size_dropdown":"List size dropdown", "closed_minibasket_click":"Closed minibasket click", "checked_delivery_detail":"Checked delivery detail", "checked_returns_detail":"Checked returns detail", "sign_in":"Sign in", "saw_checkout":"Saw checkout", "saw_sizecharts":"Saw sizecharts", "saw_delivery":"Saw delivery", "saw_account_upgrade":"Saw account upgrade", "saw_homepage":"Saw homepage", "device_computer":"Device computer", "device_tablet":"Device tablet", "returning_user":"Returning user", "loc_uk":"Loc uk", "propensity":"Propensity"}
    value_col_str = ",".join(dic_cols.values())

    try:
        isSelect, _ = IsSelect.objects.get_or_create(
            id=1,
            defaults={
                'select': value_col_str,
                'not_select': 'N'
            }
        )
    except IsSelect.DoesNotExist:
        isSelect, _ = IsSelect.objects.get_or_create(
            id=1,
            defaults={
                'select': value_col_str,
                'not_select': 'N'
            }
        )
    if isSelect:
        value_col = isSelect.select
        if value_col != '':
            value_col = value_col.split(",")
        else:
            value_col = []
        value_not_col = isSelect.not_select
        if value_not_col != '':
            value_not_col = value_not_col.split(",")
        else:
            value_not_col = []
        
        key_col = [i.replace(" ", "_").lower() for i in value_col]

    context = {'get_simulation': get_simulation, 'data': data, 'number': number, 'select': select1,
               'value_col': value_col, 'value_not_col': value_not_col, 'key_col': key_col}
    return render(request, 'database.html', context)


# User
@login_required
def users(request):
    users_list = User.objects.all()
    paginator = Paginator(users_list, 5)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    return render(request, 'users.html', {'users': users})

@login_required
def user_delete(request, id):
    user = get_object_or_404(User, id=id)
    user.delete()
    messages.success(request, 'User was deleted successfully!')
    return redirect('users')

#  change password
@login_required
def changePassword(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        repeat_password = request.POST.get('repeat_password')
        
        user = request.user
        
        # Check if the current password is correct
        if not check_password(current_password, user.password):
            messages.error(request, 'Current password is incorrect.')
            return render(request, 'change_password.html')
        
        # Check if new password matches repeat password
        if new_password != repeat_password:
            messages.error(request, 'New password and repeat password do not match.')
            return render(request, 'change_password.html')
        
        # Change the password
        user.set_password(new_password)
        user.save()
         
        update_session_auth_hash(request, user)
        
        messages.success(request, 'Your password was successfully updated!')
        return redirect('change_password')
        
    return render(request, 'change_password.html')

# 404
def custom_404(request, exception):
    return render(request, '404.html', status=404)

#  API
class editUserID(APIView):
    def post(self, request):
        user_id = request.data.get('user_id').strip()
        list_col = request.data.get('list_input').split(",")
        list_col = [int(i) for i in list_col]
        with open('D:/HK2/Kỹ_thuật_dữ_liệu/final/backend/crud/model/model_filename.pkl', 'rb') as file:
            loaded_model = pickle.load(file)

        propensity1 = loaded_model.predict_proba([list_col])[:, 1][0] 
        score1 = convert_to_score(propensity1)
        user = Simulation.objects.filter(user_id=user_id).first()
        user.basket_icon_click = list_col[0]
        user.basket_add_list = list_col[1]
        user.basket_add_detail = list_col[2]
        user.sort_by = list_col[3]
        user.image_picker = list_col[4]
        user.account_page_click = list_col[5]
        user.promo_banner_click = list_col[6]
        user.detail_wishlist_add = list_col[7]
        user.list_size_dropdown = list_col[8]
        user.closed_minibasket_click = list_col[9]
        user.checked_delivery_detail = list_col[10]
        user.checked_returns_detail = list_col[11]
        user.sign_in = list_col[12]
        user.saw_checkout = list_col[13]
        user.saw_sizecharts = list_col[14]
        user.saw_delivery = list_col[15]
        user.saw_account_upgrade = list_col[16]
        user.saw_homepage = list_col[17]
        user.device_computer = list_col[18]
        user.device_tablet = list_col[19]
        user.returning_user = list_col[20]
        user.loc_uk = list_col[21]
        user.propensity = propensity1
        user.score = score1
        user.updated_at = datetime.datetime.now()
        user.save()
        
        return Response({'data': 'UserID has been updated successfully!'}, status=status.HTTP_200_OK)
class isSelected(APIView):
    def post(self, request):
        selected = request.data.get('selected')
        notselected = request.data.get('notselected')
        
        # cập nhât lại giá trị cho isSelect
        isSelect = IsSelect.objects.get(id=1)
        if selected == '':
            selected = 'N'
        if notselected == '':
            notselected = 'N'
        isSelect.select = selected
        isSelect.not_select = notselected
        isSelect.save()
        return Response({'message': 'Selected was created successfully!'}, status=status.HTTP_200_OK)
class analysisUserID(APIView):
    def post(self, request):
        user_id = request.data.get('user_id').strip()
        get_simulation = Simulation.objects.filter(user_id=user_id).first()
        if get_simulation is not None:
            serializer = SimulationSerializer(get_simulation)
            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'data': 'User ID does not exist!'}, status=status.HTTP_200_OK)
class chartPie(APIView):  
    def get(self, request): 
        get_simulation = Simulation.objects.all()
        get_simulation = list(get_simulation)
        score_counts = {'<10': 0, '10-30': 0, '>30': 0}
        for i in get_simulation:
            if i.score < 10:
                score_counts['<10'] += 1
            elif 10 <= i.score <= 30:
                score_counts['10-30'] += 1
            elif i.score > 30:
                score_counts['>30'] += 1
        scores = list(score_counts.keys())
        counts = list(score_counts.values())
        return Response({'scores': scores, 'counts': counts}, status=status.HTTP_200_OK)

class chartBar(APIView):
    def get(self, request):
        get_simulation = Simulation.objects.all()
        get_simulation = list(get_simulation)
        score_counts = {'10-20': 0, '20-30': 0, '>30': 0}
        for i in get_simulation:
            if 10 <= i.score < 20:
                score_counts['10-20'] += 1
            elif 20 <= i.score <= 30:
                score_counts['20-30'] += 1
            elif i.score > 30:
                score_counts['>30'] += 1
        scores = list(score_counts.keys())
        counts = list(score_counts.values())
        return Response({'scores': scores, 'counts': counts}, status=status.HTTP_200_OK)

class FileUpload(APIView):
    def post(self, request):
        print(request.data)
        myfile = request.data.get('myfile')
        start_number = request.data.get('start_number')
        end_number = request.data.get('end_number')
        threading1 = request.data.get('threading')
        if myfile.name.endswith('.csv') and myfile != None:   
            try:
                start = datetime.datetime.now()
                df = pd.read_csv(myfile)   
                if len(df) < int(end_number):
                    end_number = len(df)
                
                df = df.iloc[int(start_number):int(end_number)]
                if "propensity".lower() not in df.columns.str.lower():
                    userids = df['UserID']
                    df = df.drop(['ordered','UserID','device_mobile'], axis=1)
                    with open('D:/HK2/Kỹ_thuật_dữ_liệu/final/backend/crud/model/model_filename.pkl', 'rb') as file:
                        loaded_model = pickle.load(file)

                    df['propensity'] = loaded_model.predict_proba(df)[:, 1]
                    df['score'] = df['propensity'].apply(lambda x: convert_to_score(x))
                    df = pd.concat([userids, df], axis=1)
                if "Score".lower() not in df.columns.str.lower():
                    df['score'] = df['propensity'].apply(lambda x: convert_to_score(x))
                if len(df) >= 50:
                    num_threads = int(threading1)
                    chunk_size = (len(df) + num_threads - 1) // num_threads
                    chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
                    threads = []
                    for chunk in chunks:
                        t = threading.Thread(target=process_data_chunk, args=(chunk,))
                        threads.append(t)
                        t.start()
                    
                    for t in threads:
                        t.join()   
                    
                else:
                    process_data_chunk(df)
                end = datetime.datetime.now()
                t = end - start
                messages.success(request, 'File was uploaded successfully!')
                print(f'File was uploaded successfully {t}!')
                return redirect('fileupload')
            except Exception as e:
                print("Lỗi khi đọc tệp CSV:", e)
        else:
            print("Loại tệp không được chấp nhận. Hãy chọn tệp CSV.")
        return Response({'message': 'File was uploaded successfully!'}, status=status.HTTP_200_OK)

class SimulationAPI(APIView):
    def post(self, request):
        name = request.data.get('data')
        name = name.split(',')
        name = [int(i) for i in name]
        print(len(name))
        with open('D:/HK2/Kỹ_thuật_dữ_liệu/final/backend/crud/model/model_filename.pkl', 'rb') as file:
            loaded_model = pickle.load(file)

        propensity = loaded_model.predict_proba([name])[:, 1][0] 
        score = convert_to_score(propensity)
        simulation = Simulation(
            user_id = uuid.uuid4(),
            basket_icon_click = name[0],
            basket_add_list = name[1],
            basket_add_detail = name[2],
            sort_by = name[3],
            image_picker = name[4],
            account_page_click = name[5],
            promo_banner_click = name[6],
            detail_wishlist_add = name[7],
            list_size_dropdown = name[8],
            closed_minibasket_click = name[9],
            checked_delivery_detail = name[10],
            checked_returns_detail = name[11],
            sign_in = name[12],
            saw_checkout = name[13],
            saw_sizecharts = name[14],
            saw_delivery = name[15],
            saw_account_upgrade = name[16],
            saw_homepage = name[17],
            device_computer = name[18],
            device_tablet = name[19],
            returning_user = name[20],
            loc_uk = name[21],
            propensity = propensity,
            score = score,
            created_at = datetime.datetime.now(),
            updated_at = datetime.datetime.now()
        )
        simulation.save()
        simulation = Simulation.objects.filter(user_id=simulation.user_id).first()
        serializer = SimulationSerializer(simulation)
        return Response({'message': 'Simulation was created successfully!','data':serializer.data}, status=status.HTTP_200_OK)

