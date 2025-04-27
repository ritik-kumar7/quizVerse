import json
from django.shortcuts import render, redirect
from .models import Profile
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.db import connection
from .forms import SignupForm

def signup_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        default_photo = 'https://i.imgur.com/pG5Zwli.jpg'  # Default profile photo

        with connection.cursor() as cursor:
            # Create profile
            cursor.execute('''
                INSERT INTO profile (name, email, password, profile_photo)
                VALUES (%s, %s, %s, %s)
            ''', [name, email, password, default_photo])
            
            # Get the new user ID
            cursor.execute('SELECT LAST_INSERT_ID()')
            user_id = cursor.fetchone()[0]
            
            # Create empty user_info entry
            cursor.execute('''
                INSERT INTO user_info (user_id)
                VALUES (%s)
            ''', [user_id])

        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')

    return render(request, 'signup.html')

def profile(request):
    if not request.session.get('user_id'):
        return redirect('login')

    user_id = request.session['user_id']
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'info':
            # Update profile info
            name = request.POST.get('name')
            email = request.POST.get('email')
            
            with connection.cursor() as cursor:
                cursor.execute('''
                    UPDATE profile 
                    SET name = %s, email = %s 
                    WHERE id = %s
                ''', [name, email, user_id])
                
                # Update session
                request.session['user_name'] = name
                request.session['user_email'] = email
                messages.success(request, 'Profile updated successfully!')

        elif form_type == 'password':
            # Update password
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Verify old password
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT password FROM profile WHERE id = %s
                ''', [user_id])
                row = cursor.fetchone()
                current_password = row[0]
                
                if current_password != old_password:
                    messages.error(request, 'Current password is incorrect!')
                elif new_password != confirm_password:
                    messages.error(request, 'New passwords do not match!')
                else:
                    cursor.execute('''
                        UPDATE profile 
                        SET password = %s 
                        WHERE id = %s
                    ''', [new_password, user_id])
                    messages.success(request, 'Password updated successfully!')

        elif form_type == 'user_info':
            # Update user information
            age = request.POST.get('age')
            gender = request.POST.get('gender')
            college_name = request.POST.get('college_name')
            city = request.POST.get('city')
            state = request.POST.get('state')
            
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1 FROM user_info WHERE user_id = %s', [user_id])
                if cursor.fetchone():
                    # Update existing record
                    cursor.execute('''
                        UPDATE user_info 
                        SET age = %s,
                            gender = %s,
                            college_name = %s,
                            city = %s,
                            state = %s
                        WHERE user_id = %s
                    ''', [age, gender, college_name, city, state, user_id])
                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO user_info 
                        (user_id, age, gender, college_name, city, state)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', [user_id, age, gender, college_name, city, state])
                
                messages.success(request, 'Additional information updated!')

        elif 'profile_photo' in request.FILES:
            # Handle profile photo upload
            profile_photo = request.FILES['profile_photo']
            file_name = f"profile_photos/{user_id}_{profile_photo.name}"
            file_path = default_storage.save(file_name, profile_photo)
            photo_url = default_storage.url(file_path)
            
            with connection.cursor() as cursor:
                cursor.execute('''
                    UPDATE profile 
                    SET profile_photo = %s 
                    WHERE id = %s
                ''', [photo_url, user_id])
                
                request.session['profile_photo'] = photo_url
                messages.success(request, 'Profile photo updated!')

    # Get updated user data
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT p.name, p.email, p.profile_photo,
                   u.age, u.gender, u.college_name, 
                   u.city, u.state, u.points, u.quiz_played
            FROM profile p
            LEFT JOIN user_info u ON p.id = u.user_id
            WHERE p.id = %s
        ''', [user_id])
        user_data = cursor.fetchone()
        
    context = {
        'name': user_data[0],
        'email': user_data[1],
        'profile_photo': user_data[2],
        'age': user_data[3] if user_data[3] is not None else '',
        'gender': user_data[4] if user_data[4] is not None else '',
        'college_name': user_data[5] if user_data[5] is not None else '',
        'city': user_data[6] if user_data[6] is not None else '',
        'state': user_data[7] if user_data[7] is not None else '',
        'points': user_data[8] if user_data[8] is not None else 0,
        'quiz_played': user_data[9] if user_data[9] is not None else 0,
    }
    
    return render(request, 'profile.html', context)


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = Profile.objects.get(email=email, password=password)
            request.session['user_id'] = user.id
            request.session['user_name'] = user.name
            request.session['user_email'] = user.email
            request.session['profile_photo'] = user.profile_photo
            return redirect('topics')
        except Profile.DoesNotExist:
            messages.error(request, 'Invalid Credentials!')
            return redirect('login')

    return render(request, 'login.html')


def topics(request):
    # Allow access with or without login but show different content
    context = {}
    if 'user_id' in request.session:
        context = {
            'name': request.session.get('user_name'),
            'email': request.session.get('user_email'),
            'profile_photo': request.session.get('profile_photo'),
        }
    return render(request, 'topics.html', context)


def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('index')

def index(request):
    # Allow access with or without login but show different content
    context = {}
    if 'user_id' in request.session:
        context = {
            'name': request.session.get('user_name'),
            'email': request.session.get('user_email'),
            'profile_photo': request.session.get('profile_photo'),
        }
    return render(request, 'index.html', context)


def about(request):
    # Allow access with or without login but show different content
    context = {}
    if 'user_id' in request.session:
        context = {
            'name': request.session.get('user_name'),
            'email': request.session.get('user_email'),
            'profile_photo': request.session.get('profile_photo'),
        }
    return render(request, 'about.html', context)

def leaderboard(request):
    # Fetch top users ordered by points
    with connection.cursor() as cursor:
        # Get top 10 users with their points
        cursor.execute('''
            SELECT p.id, p.name, p.profile_photo, u.points 
            FROM profile p
            JOIN user_info u ON p.id = u.user_id
            ORDER BY u.points DESC
            LIMIT 10
        ''')
        top_users = cursor.fetchall()
        
        # Get current user's rank if logged in
        current_user = None
        if request.session.get('user_id'):
            user_id = request.session['user_id']
            
            # Get current user's rank and info
            cursor.execute('''
                SELECT p.id, p.name, p.profile_photo, u.points,
                       (SELECT COUNT(*) + 1 
                        FROM user_info u2 
                        WHERE u2.points > u.points) as rank
                FROM profile p
                JOIN user_info u ON p.id = u.user_id
                WHERE p.id = %s
            ''', [user_id])
            current_user = cursor.fetchone()
    
    # Prepare the data for template
    leaderboard_data = []
    for rank, user in enumerate(top_users, start=1):
        leaderboard_data.append({
            'rank': rank,
            'id': user[0],
            'name': user[1],
            'profile_photo': user[2],
            'points': user[3],
            'initials': ''.join([name[0].upper() for name in user[1].split()[:2]]),
            'is_current_user': request.session.get('user_id') == user[0]
        })
    
    context = {
        'top_users': leaderboard_data[:3],  # Top 3 for podium
        'other_users': leaderboard_data[3:],  # Rest for table
        'current_user': {
            'rank': current_user[4] if current_user else None,
            'id': current_user[0] if current_user else None,
            'name': current_user[1] if current_user else None,
            'profile_photo': current_user[2] if current_user else None,
            'points': current_user[3] if current_user else None,
            'initials': ''.join([name[0].upper() for name in current_user[1].split()[:2]]) if current_user else None,
        } if current_user else None,
    }
    
    return render(request, 'leaderboard.html', context)

def quiz(request):
    return render(request, 'quiz.html')


# def topics(request):
#     return render(request, 'topics.html')

def result(request):
    return render(request, 'result.html')


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def increment_quiz_played(request):
    if request.method == 'POST' and request.session.get('user_id'):
        user_id = request.session['user_id']
        with connection.cursor() as cursor:
            cursor.execute('''
                UPDATE user_info 
                SET quiz_played = quiz_played + 1 
                WHERE user_id = %s
            ''', [user_id])
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=401)

@csrf_exempt
def update_quiz_results(request):
    if request.method == 'POST' and request.session.get('user_id'):
        user_id = request.session['user_id']
        data = json.loads(request.body)
        points = data.get('points', 0)
        
        with connection.cursor() as cursor:
            cursor.execute('''
                UPDATE user_info 
                SET points = points + %s 
                WHERE user_id = %s
            ''', [points, user_id])
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=401)